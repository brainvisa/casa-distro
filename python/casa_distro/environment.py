# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function

import fnmatch
from glob import glob
import json
import os
import os.path as osp
import re
import shutil
import subprocess
import tempfile

from casa_distro import (share_directories,
                         singularity,
                         vbox)
from casa_distro.build_workflow import prepare_home  # should be moved here
from casa_distro.web import url_listdir, urlopen, wget_command

bv_maker_branches = {
    'latest_release': 'latest_release',
    'master': 'bug_fix',
    'integration': 'trunk'
}

# We need to duplicate this function to allow copying over
# an existing directory
def copytree(src, dst, symlinks=False, ignore=None):
    """Recursively copy a directory tree using copy2().
    If exception(s) occur, an Error is raised with a list of reasons.
    If the optional symlinks flag is true, symbolic links in the
    source tree result in symbolic links in the destination tree; if
    it is false, the contents of the files pointed to by symbolic
    links are copied.
    The optional ignore argument is a callable. If given, it
    is called with the `src` parameter, which is the directory
    being visited by copytree(), and `names` which is the list of
    `src` contents, as returned by os.listdir():
        callable(src, names) -> ignored_names
    Since copytree() is called recursively, the callable will be
    called once for each directory that is copied. It returns a
    list of names relative to the `src` directory that should
    not be copied.
    XXX Consider this example code rather than the ultimate tool.
    """
    if os.path.isdir(src):
        names = os.listdir(src)
        dstnames = names
    else:
        names = [os.path.basename(src)]
        src = os.path.dirname(src)
        
        if os.path.isdir(dst):
            dstnames = names
        else:
            dstnames = [os.path.basename(dst)]
            dst = os.path.dirname(dst)
        
    if ignore is not None:
        ignored_names = ignore(src, names, 
                               dst, dstnames)
    else:
        ignored_names = set()

    if not os.path.exists(dst):
        os.makedirs(dst)
        
    errors = []
    for name, new_name in zip(names, dstnames):
        if name in ignored_names:
            continue
        srcname = os.path.join(src, name)
        dstname = os.path.join(dst, new_name)
        try:
            if symlinks and os.path.islink(srcname):
                linkto = os.readlink(srcname)
                os.symlink(linkto, dstname)
            elif os.path.isdir(srcname):
                copytree(srcname, dstname, symlinks, ignore)
            else:
                # Will raise a SpecialFileError for unsupported file types
                shutil.copy2(srcname, dstname)
        # catch the Error from the recursive copytree so that we can
        # continue with other files
        except shutil.Error as err:
            errors.extend(err.args[0])
        except EnvironmentError as why:
            errors.append((srcname, dstname, str(why)))
    try:
        shutil.copystat(src, dst)
    except OSError as why:
        if shutil.WindowsError is not None and isinstance(why, shutil.WindowsError):
            # Copying file access times may fail on Windows
            pass
        else:
            errors.append((src, dst, str(why)))
    if errors:
        raise shutil.Error(errors)
    
def cp(src, dst, not_override=[], verbose=None):
    
    def override_exclusion(cur_src, names, 
                           cur_dst, dst_names):
        excluded = []
        for n in not_override:
            if n in names:
              i = names.index(n)
              d = os.path.join(cur_dst, dst_names[i])
              if os.path.exists(d) or os.path.islink(d):
                excluded.append(n)
                if verbose:
                    print('file', d, 'exists,', 'skipping override.', 
                          file=verbose)

        return excluded

    copytree(src, dst, ignore=override_exclusion)

def string_to_byte_count(size):
    coefs = {
        '': 1,
        'K': 1024,
        'M': 1024 ** 2,
        'G': 1024 ** 3}
    
    match = re.match(r'^(\d+(?:\.\d+)?)\s*([KMG]?)$', size)
    if not match:
        raise ValueError('Invlid file system size: {0}'.format(size))
    n = float(match.group(1))
    coef = coefs[match.group(2)]
    return int(n * coef)


def update_config(config, update):
    """
    Update a configuration dictionary with an update configuration dictionary. 
    These two dictionaries are JSON objects. To date this simply merge the 
    two dictionaries (dictionaries are merged recursively, lists are
    concatenated)
    """
    for k, v in update.items():
        if k not in config:
            config[k] = v
        else:
            oldv = config[k]
            if isinstance(oldv, dict):
                update_config(oldv, v)
            elif isinstance(oldv, list):
                oldv += v
            else:
                config[k] = v

def find_in_path(file):
    '''
    Look for a file in a series of directories contained in ``PATH`` environment variable.
    '''
    path = os.environ.get('PATH').split(os.pathsep)
    for i in path:
        p = osp.normpath(osp.abspath(i))
        if p:
            r = glob(osp.join(p, file))
            if r:
                return r[0]

def ext3_file_size(filename):
    block_size = block_count = None
    for line in subprocess.check_output(['dumpe2fs', filename], stderr=subprocess.STDOUT).split('\n'):
        if line.startswith('Block count'):
            block_count = int(line.rsplit(None,1)[-1])
        elif line.startswith('Block size'):
            block_size = int(line.rsplit(None,1)[-1])
    if block_size is not None and block_count is not None:
        return block_size * block_count
    return None

def create_ext3_file(filename, size):
    block_size = 1024*1024
    block_count = int(size/block_size)
    if size % block_size != 0:
        block_count += 1
    # If there are too few blocks, the system cannot be created
    block_count = max(2, block_count)
    subprocess.check_call(['dd', 
                           'if=/dev/zero',
                           'of={0}'.format(filename), 
                           'bs={0}'.format(block_size),
                           'count={0}'.format(block_count)])
    tmp = tempfile.mkdtemp()
    try:
        subprocess.check_call(['mkfs.ext3', '-d', tmp, filename])
    finally:
        os.rmdir(tmp)

def resize_ext3_file(filename, size):
    if isinstance(size, int):
        size=str(size)
    elif not re.match(r'\d+[KMG]?', size):
        raise ValueError('Invlid file system size: {0}'.format(size))
    subprocess.check_call(['e2fsck', '-f', filename])
    subprocess.check_call(['resize2fs', filename, size])


def iter_distros():
    """
    Iterate over all available distros. For each one, yield a
    dictionary corresponding to the casa_distro.json file
    with the "directory" item added.
    """
    for share_directory in share_directories():
        distro_dir = osp.join(share_directory, 'distro')
        if not osp.isdir(distro_dir):
            continue
        for basename in os.listdir(distro_dir):
            casa_distro_json = osp.join(distro_dir, basename,
                                        'casa_distro.json')
            if osp.isfile(casa_distro_json):
                with open(casa_distro_json) as f:
                    distro = json.load(f)
                distro['directory'] = osp.join(distro_dir, basename)
                yield distro


def select_distro(distro):
    """
    Select a distro given its name or an existing distro directory.
    """
    for d in iter_distros():
        if d['name'] == distro:
            return d
    if osp.isdir(distro):
        directory = distro
        casa_distro_json = osp.join(directory, 'host', 'conf', 'casa_distro.json')
        if osp.exists(casa_distro_json):
            distro = json.load(open(casa_distro_json))
            distro['directory'] = directory
            return distro
    raise ValueError('Invalid distro: {0}'.format(distro))

_casa_distro_directory = None


def casa_distro_directory():
    """
    Return the defaut casa_distro directory.
    Either $CASA_DEFAULT_REPOSITORY or ~/casa_distro.
    """
    global _casa_distro_directory

    if _casa_distro_directory is None:
        _casa_distro_directory = os.environ.get('CASA_DEFAULT_REPOSITORY')
        if not _casa_distro_directory:
            _casa_distro_directory = osp.expanduser('~/casa_distro')
    return _casa_distro_directory


def iter_environments(base_directory, **filter):
    """
    Iterate over environments created with "setup" or "setup_dev" commands
    in the given
    base directory. For each one, yield a dictionary corresponding to the
    casa_distro.json file with the "directory" item added.
    """
    for casa_distro_json in sorted(glob(osp.join(base_directory, '*', 'host',
                                                 'conf', 'casa_distro.json'))):
        environment_config = json.load(open(casa_distro_json))
        directory = osp.dirname(osp.dirname(osp.dirname(casa_distro_json)))
        config = {}
        config['config_files'] = [casa_distro_json]
        config['directory'] = directory
        config['mounts'] = {'/casa/host':'{directory}/host'}
        config['env'] = {
            'CASA_DISTRO': '{name}',
            'CASA_SYSTEM': '{system}',
            'CASA_HOST_DIR': '{directory}',
        }
        if 'bv_maker_branch' in config:
            config['env']['CASA_BRANCH'] = config['bv_maker_branch']
        if environment_config['container_type'] == 'singularity':
            config.setdefault('gui_env', {}).update({
                'DISPLAY': '$DISPLAY',
                'XAUTHORITY': '/casa/host/home/.Xauthority'})

        update_config(config, environment_config)
        
        for i in ('~/.config/casa-distro/casa_distro_3.json',):
            f = osp.expanduser(i).format(name=config['name'])
            if osp.exists(f):
                config['config_files'].append(f)
                update_config(config, json.load(open(f)))
        
        overlay = osp.join(directory, 'overlay.img')
        if osp.exists(overlay):
            config['overlay'] = overlay
            config['overlay_size'] = ext3_file_size(overlay)
        
        match = False
        for k, p in filter.items():
            if p is None:
                continue
            v = config.get(k)
            if v is None or not fnmatch.filter([v], p):
                break
        else:
            match = True
        if match:
            yield config


def iter_images(base_directory=casa_distro_directory(), **filter):
    """
    Iterate over locally installed images, with filtering.
    Filtering may be environment-driven (filter from existing environments),
    or image-driven (filter local image names even if they are not used in any
    environment). Image-driven mode is used if none of the environment
    selection filters are used (name, system, distro and branch are all None).
    If you with to trigger the environment-driven mode without filtering, just
    select "*" as one of the environment filter variables.
    """
    if filter.get('name') or filter.get('system') or filter.get('distro') \
            or filter.get('branch'):
        # select by environment
        for config in iter_environments(base_directory,
                                        type=filter.get('type'),
                                        distro=filter.get('distro'),
                                        branch=filter.get('branch'),
                                        system=filter.get('system'),
                                        name=filter.get('name'),
                                        image=filter.get('image')):
            image = (config['container_type'], config['image'])
            yield image

    else:
        # select by images
        image_filter = filter.get('image')
        for image in singularity.iter_images(base_directory=base_directory):
            if not image_filter or fnmatch.filter([image], image_filter):
                yield ('singularity', image)
        #for image in docker.iter_images(base_directory=base_directory):
            #if not filter or fnmatch.filter([image], filter):
                #yield ('docker', image)
        #for image in vbox.iter_images(base_directory=base_directory):
            #if not filter or fnmatch.filter([image], filter):
                #yield ('vbox', image)


def image_remote_location(container_type, image_name, url):
    if container_type == 'docker':
        raise NotImplementedError('docker case not implemented yet.')
    return '%s/%s' % (url, osp.basename(image_name))


def update_container_image(container_type, image_name, url, force=False,
                           verbose=None, new_only=False):
    """
    Download a container image.

    Parameters
    ----------
    container_type: str
        singularity, docker, vbox
    image_name: str
        image filename (full path)
    url: str
        pattern ('http://brainvisa.info/casa-distro/{container_type}')
    force: bool
        download image even if it seems up-to-date
    verbose: file
        print things
    new_only: bool
        download only if the local image is missing (don't really update)
    """
    url = url.format(container_type=container_type)
    remote_image = image_remote_location(container_type, image_name, url)

    if not os.path.isabs(image_name) and not osp.exists(image_name):
        image_name = osp.join(casa_distro_directory(), image_name)

    image = osp.basename(image_name)
    if image not in url_listdir(url):
        if image.endswith('.simg') and not verbose:
            # probably a casa-distro 2 image: don't even warn
            return
        print('File {image_name} does not exist and cannot be downloaded '
              'from {remote_image}'.format(
                  image_name=image, remote_image=remote_image))
        return

    metadata_file = '%s.json' % image_name
    metadata = json.loads(urlopen('%s.json' % remote_image).read())
    if new_only and osp.exists(metadata_file):
        print('image %s already exists.' % image, file=verbose)
        return  # don't update
    if not force and osp.exists(metadata_file):
        local_metadata = json.load(open(metadata_file))
        if local_metadata.get('md5') == metadata.get('md5') \
                and local_metadata.get('size') == metadata.get('size') \
                and osp.isfile(image_name) \
                and os.stat(image_name).st_size == metadata.get('size'):
            #if verbose:
            print('image %s is up-to-date.' % image)
            return
    #if verbose:
    print('pulling image: %s' % image_name)
    tmp_metadata_file = list(osp.split(metadata_file))
    tmp_metadata_file[-1] = '.%s' % tmp_metadata_file[-1]
    tmp_metadata_file = osp.join(*tmp_metadata_file)

    tmp_image_name = list(osp.split(image_name))
    tmp_image_name[-1] = '.%s' % tmp_image_name[-1]
    tmp_image_name = osp.join(*tmp_image_name)

    download_all = True
    if osp.exists(tmp_metadata_file):
        older_metadata = json.load(open(tmp_metadata_file))
        if older_metadata['md5'] == metadata['md5']:
            download_all = False

    json.dump(metadata, open(tmp_metadata_file, 'w'), indent=4)
    if download_all:
        subprocess.check_call(wget_command() + [remote_image, '-O',
                                                tmp_image_name])
    else:
        subprocess.check_call(wget_command() + ['--continue', remote_image,
                                                '-O', tmp_image_name])
    # move to final location
    os.rename(tmp_image_name, image_name)
    os.rename(tmp_metadata_file, metadata_file)


def select_environment(base_directory, **kwargs):
    """
    Select a single distro given its name or an existing distro directory.
    """
    l = list(iter_environments(base_directory, **kwargs))
    if len(l) == 1:
        return l[0]
    if len(l) > 1:
        raise ValueError('Several distros found, use a more selective criteria: {0}'.format(', '.join(i['name'] for i in l)))
    raise ValueError('Cannot find any distro to perform requested action')


def setup(metadata, writable,
          base_directory, output, verbose):
    '''
    Create a new run environment.

    '''
        
    environment = {}
    environment.update(metadata)
    environment['casa_distro_compatibility'] = '3'
        
    if not osp.exists(osp.join(output, 'host', 'conf')):
        os.makedirs(osp.join(output, 'host', 'conf'))
        
    casa_distro_json = osp.join(output, 'host', 'conf', 'casa_distro.json')
    json.dump(environment, open(casa_distro_json, 'w'), indent=4)

    home = osp.join(output, 'host', 'home')
    if not osp.exists(home):
        os.mkdir(home)

    if writable:
        size = string_to_byte_count(writable)
        if size:
            overlay = osp.join(output, 'overlay.img')
            create_ext3_file(overlay, size)

def setup_dev(metadata,
              distro,
              writable,
              base_directory, 
              output, 
              verbose):
    setup(metadata=metadata,
          writable=writable,
          base_directory=base_directory,
          output=output,
          verbose=verbose)

    all_subdirs = ('conf', 'home', 'src', 'build', 'install',)    
    for subdir in all_subdirs:
        if not osp.exists(osp.join(output, 'host', subdir)):
            os.makedirs(osp.join(output, 'host', subdir))
    for i in os.listdir(distro['directory']):
        if i == 'casa_distro.json':
            continue
        cp(osp.join(distro['directory'], i), osp.join(output, i), verbose=verbose)
    
    svn_secret = osp.join(output, 'host', 'conf', 'svn.secret')
    if not os.path.exists(svn_secret):
        print('\n------------------------------------------------------------')
        print('**WARNING:**' )
        print('Before using "casa_distro bv_maker" you will have to '
              'create the svn.secret file with your Bioproj login / password '
              'in order to access the BrainVisa repository.')
        print('Place it at the following location:\n')
        print(svn_secret)
        print('\nThis file is a shell script that must set the variables '
              'SVN_USERNAME and SVN_PASSWORD. Do not forget to properly quote '
              'the values if they contains special characters.')
        print('For instance, the file could contain the two following lines (replacing '
              '"your_login" and "your_password" by appropriate values:\n')
        print("SVN_USERNAME='your_login'")
        print("SVN_PASSWORD='your_password'\n")
        print('If you are only using open-source projects, you can use the '
              '"public" login/password: brainvisa / Soma2009\n')
        print('Remember also that you can edit and customize the projects to '
              'be built, by editing the following file:\n')
        print(osp.join(output, 'host', 'conf', 'bv_maker.cfg'))
        print('------------------------------------------------------------')
        print()


def update_environment(config, base_directory, writable, verbose):
    """
    Update an existing environment
    """
    env_directory = config['directory']
    if writable:
        overlay = osp.join(env_directory, 'overlay.img')
        size = string_to_byte_count(writable)
        if size:
            if os.path.exists(overlay):
                resize_ext3_file(overlay, int(size / 1024) + (1 if size % 1024 else 0))
            else:
                create_ext3_file(overlay, size)
        else:
            if os.path.exists(overlay):
                os.remove(overlay)


def run_container(config, command, gui, root, cwd, env, image, 
                  container_options, base_directory, verbose):
    """
    Run a command in the container defined in the environment
    """
    env_directory = config['directory']
    # if config.get('user_specific_home'):
        # env_relative_subdirectory = osp.normcase(
            # osp.abspath(env_directory)).lstrip(os.sep)
        # home_path = os.path.join(
            # os.path.expanduser('~'), '.config', 'casa-distro',
            # env_relative_subdirectory, 'home')
        # config.setdefault('mounts', {})
        # config['mounts']['/casa/home'] = home_path
        # if not os.path.exists(home_path):
            # In case of user-specific home directories, the home dir has not
            # been initialized at the creation of the build-workflow, so it
            # needs to be done at first launch.
            # os.makedirs(home_path)
            # prepare_home(env_directory, home_path)

    container_type = config.get('container_type')
    if container_type == 'singularity':
        module = singularity
    elif container_type == 'vbox':
        raise NotImplementedError('run command is not implemented for VirtualBox')
        module = vbox
    elif container_type == 'docker':
        raise NotImplementedError('run command is not implemented for Docker')
    else:
        raise ValueError('Invalid container type: {0}'.format(container_type))
    env = (env.copy() if env else {})
    branch = config.get('branch')
    if branch:
        env['CASA_BRANCH'] = bv_maker_branches[branch]
        print('!', branch)
    module.run(config, 
               command=command, 
               gui=gui,
               root=root,
               cwd=cwd, 
               env=env,
               image=image,
               container_options=container_options,
               base_directory=base_directory,
               verbose=verbose)
