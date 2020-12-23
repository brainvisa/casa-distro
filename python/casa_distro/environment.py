# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

import fnmatch
from glob import glob
import json
import os
import os.path as osp
import platform
import re
import shutil
import subprocess
import sys
import time

import casa_distro
from casa_distro import (share_directories,
                         singularity,
                         vbox)
from casa_distro.web import url_listdir, urlopen
from casa_distro import downloader

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
        if (shutil.WindowsError is not None
                and isinstance(why, shutil.WindowsError)):
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
    These two dictionaries are JSON objects. This simply merges the
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
    '''Look for a file in directories of the ``PATH`` environment variable.
    '''
    path = os.environ.get('PATH').split(os.pathsep)
    for i in path:
        p = osp.normpath(osp.abspath(i))
        if p:
            r = glob(osp.join(p, file))
            if r:
                return r[0]


def install_casa_distro(dest):
    source = osp.dirname(osp.dirname(osp.dirname(__file__)))
    for i in ('bin', 'python', 'etc', 'share'):
        dest_dir = osp.join(dest, i)
        if osp.exists(dest_dir):
            shutil.rmtree(dest_dir)
        copytree(osp.join(source, i), dest_dir,
                 symlinks=True,
                 ignore=lambda src, names, dst, dstnames:
                 {i for i in names if i in ('__pycache__',)
                  or i.endswith('.pyc') or i.endswith('~')})


def setup_user(setup_dir):
    """
    Initialize a user environment directory.
    This function is supposed to be called from a user image.
    """
    if not osp.exists(setup_dir):
        print('Directory {} does not exist.'.format(setup_dir),
              file=sys.stderr)
        sys.exit(1)

    if not osp.exists(osp.join(setup_dir, 'conf')):
        os.makedirs(osp.join(setup_dir, 'conf'))
    bin = osp.join(setup_dir, 'bin')
    if not osp.exists(bin):
        os.makedirs(bin)

    bv = osp.join(osp.dirname(osp.dirname(osp.dirname(__file__))),
                  'bin', 'bv')
    dest = osp.join(bin, 'bv')
    shutil.copy(bv, dest)
    create_environment_bin_commands(osp.dirname(bv), bin)

    casa_distro_dir = osp.join(setup_dir, 'casa-distro')
    install_casa_distro(casa_distro_dir)

    environment = {
        'casa_distro_compatibility': str(casa_distro.version_major),
        'type': 'run',
        'container_type': 'singularity',
    }
    environment['distro'] = os.getenv('CASA_DISTRO')
    if not environment['distro']:
        environment['distro'] = 'unkown_distro'
    environment['system'] = os.getenv('CASA_SYSTEM')
    if not environment['system']:
        environment['system'] = \
            '-'.join(platform.linux_distribution()[:2]).lower()
    if 'CASA_BRANCH' in os.environ:
        environment['branch'] = os.environ['CASA_BRANCH']
    environment['image'] = os.getenv('SINGULARITY_CONTAINER')
    if not environment['image']:
        environment['image'] = '/unknown.sif'
    if environment['image'] != '/unknown.sif':
        environment['name'] = \
            osp.splitext(osp.basename(environment['image']))[0]
    else:
        environment['name'] = '{}-{}'.format(environment['distro'],
                                             time.strftime('%Y%m%d'))
    json.dump(environment,
              open(osp.join(setup_dir, 'conf',
                            'casa_distro.json'), 'w'),
              indent=4)

    write_environment_homedir(osp.join(setup_dir, 'home'))


def setup_dev(setup_dir, distro, branch=None, system=None, image=None,
              name=None):
    if not branch:
        branch = os.environ['CASA_BRANCH']

    if not system:
        system = os.getenv('CASA_SYSTEM')
    if not system:
        system = \
            '-'.join(platform.linux_distribution()[:2]).lower()

    if name is None:
        name = '-'.join([distro, branch, system])

    if not osp.exists(setup_dir):
        print('Directory {} does not exist.'.format(setup_dir),
              file=sys.stderr)
        sys.exit(1)

    all_subdirs = ('conf', 'src', 'build', 'install',)
    for subdir in all_subdirs:
        if not osp.exists(osp.join(setup_dir, subdir)):
            os.makedirs(osp.join(setup_dir, subdir))

    bin = osp.join(setup_dir, 'bin')
    if not osp.exists(bin):
        os.makedirs(bin)

    bv = osp.join(osp.dirname(osp.dirname(osp.dirname(__file__))),
                  'bin', 'bv')
    shutil.copy(bv, osp.join(bin, 'bv'))

    casa_distro_dir = osp.join(setup_dir, 'casa-distro')
    install_casa_distro(casa_distro_dir)

    distro_dir = osp.join(casa_distro_dir, 'share', 'distro', distro)
    casa_distro_json = osp.join(distro_dir, 'casa_distro.json')
    if not osp.exists(casa_distro_json):
        print('ERROR - invalid distro:', distro, file=sys.stderr)
        sys.exit(1)
    for i in os.listdir(distro_dir):
        if i == 'casa_distro.json':
            continue
        fp = osp.join(distro_dir, i)
        if osp.isdir(fp):
            copytree(fp, osp.join(setup_dir, i))
        else:
            cp(fp, osp.join(setup_dir, i))

    environment = json.load(open(casa_distro_json))
    environment.pop('description', None)
    environment.update({
        'casa_distro_compatibility': str(casa_distro.version_major),
        'distro': distro,
        'type': 'dev',
        'system': system,
        'branch': branch,
        'container_type': 'singularity',
    })
    if image is None:
        image = os.getenv('SINGULARITY_CONTAINER')
        if not image:
            images = glob(osp.join(osp.expanduser(
                '~/casa_distro/casa-dev-*.sif')))
            if len(images) == 1:
                image = images[0]
            if not image:
                raise ValueError('No image found')
    environment['image'] = image
    environment['name'] = name
    json.dump(environment,
              open(osp.join(setup_dir, 'conf',
                            'casa_distro.json'), 'w'),
              indent=4)

    write_environment_homedir(osp.join(setup_dir, 'home'))

    svn_secret = osp.join(setup_dir, 'conf', 'svn.secret')
    open(svn_secret, 'w').write(
        "# This is a shell script that must set the variables SVN_USERNAME\n"
        "# and SVN_PASSWORD. Do not forget to properly quote the variable\n"
        "# especially if values contains special characters.\n\n"
        "SVN_USERNAME='brainvisa'\n"
        "SVN_PASSWORD='Soma2009'\n")

    print('\n------------------------------------------------------------')
    print('** WARNING: svn secret **')
    print('Before using "casa_distro bv_maker" you will have to '
          'setup svn to access the Biporoj server, which needs a login '
          'and a password.\n'
          'There are 2 methods for this, and 2 situations, which we could '
          'simplify as this:\n\n'
          '* opensource distro: if you are only using open-source '
          'projects, you can use the preconfigured "public" '
          'login/password: brainvisa / Soma2009.\n'
          'Credentials are stored in the followinf file:\n')
    print(svn_secret)
    print('\nYou may leave it as is or replace with your own login/password '
          'if you need to access restricted resources. Svn will be used '
          'non-interactively, it will not ask for password confirmation '
          '/ storage, but will reject any interactive input, including '
          'commit comments etc.')
    print('This file is a shell script that must set the variables '
          'SVN_USERNAME and SVN_PASSWORD. Do not forget to properly quote '
          'the values if they contains special characters.')
    print('For instance, the file could contain the two following lines '
          '(replacing "your_login" and "your_password" by appropriate '
          'values:\n')
    print("SVN_USERNAME='your_login'")
    print("SVN_PASSWORD='your_password'\n")
    print('If you need more interaction, then remove the svn.secret file, '
          'and let svn interactively ask you for login/password and store '
          'it appropriately, like in the following case.\n')
    print('* brainvisa and other non-totally opensource distros: they '
          'need a personal login and password. You can either use the '
          'above svn.secret method (create the file if it doesn\'t exist '
          'and fill in your information), or let svn interactively ask '
          'you a login and password, and let it store it the way it suits '
          'it. In this mode svn is used "directly", without interactive '
          'restrictions.\n\n')
    print('Remember also that you can edit and customize the projects to '
          'be built, by editing the following file:\n')
    print(osp.join(setup_dir, 'conf', 'bv_maker.cfg'))
    print('------------------------------------------------------------')
    print()


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
        casa_distro_json = osp.join(
            directory, 'conf', 'casa_distro.json')
        if osp.exists(casa_distro_json):
            distro = json.load(open(casa_distro_json))
            distro['directory'] = directory
            return distro
    raise ValueError('Invalid distro: {0}'.format(distro))


_casa_distro_directory = None


def casa_distro_directory():
    """
    Return the defaut casa_distro directory.
    Either $CASA_BASE_DIRECTORY or ~/casa_distro.
    """
    global _casa_distro_directory

    if _casa_distro_directory is None:
        _casa_distro_directory = os.environ.get('CASA_BASE_DIRECTORY')
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
    casa_distro_jsons = glob(osp.join(base_directory, '*',
                                      'conf', 'casa_distro.json'))
    if not casa_distro_jsons:
        # Special case where base_directroy is the directory of an environment
        casa_distro_jsons = glob(osp.join(base_directory, 'conf',
                                          'casa_distro.json'))
    for casa_distro_json in sorted(casa_distro_jsons):
        environment_config = json.load(open(casa_distro_json))
        directory = osp.dirname(osp.dirname(casa_distro_json))
        config = {}
        config['config_files'] = [casa_distro_json]
        config['directory'] = directory
        config['mounts'] = {
            '/casa/host': '{directory}',
            '/host': '/',
        }
        config['env'] = {
            'CASA_ENVIRONMENT': '{name}',
            'CASA_SYSTEM': '{system}',
            'CASA_HOST_DIR': '{directory}',
            'CASA_DISTRO': '{distro}',
        }
        if 'bv_maker_branch' in config:
            config['env']['CASA_BRANCH'] = config['bv_maker_branch']
        if environment_config['container_type'] == 'singularity':
            config.setdefault('gui_env', {}).update({
                'DISPLAY': '$DISPLAY',
                'XAUTHORITY': '/casa/home/.Xauthority'})

        update_config(config, environment_config)

        for i in ('~/.config/casa-distro/casa_distro_3.json',):
            f = osp.expanduser(i).format(name=config['name'])
            if osp.exists(f):
                config['config_files'].append(f)
                update_config(config, json.load(open(f)))

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
            or filter.get('branch') or filter.get('type'):
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
        # for image in docker.iter_images(base_directory=base_directory):
        #     if not filter or fnmatch.filter([image], filter):
        #         yield ('docker', image)
        # for image in vbox.iter_images(base_directory=base_directory):
        #     if not filter or fnmatch.filter([image], filter):
        #         yield ('vbox', image)


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

    metadata_file = '%s.json' % image_name
    if new_only and osp.exists(metadata_file) and osp.exists(image_name):
        print('image %s already exists.' % image, file=verbose)
        return  # don't update

    metadata = json.loads(
        urlopen('%s.json' % remote_image).read().decode('utf-8'))

    if image not in url_listdir(url):
        if image.endswith('.simg') and not verbose:
            # probably a casa-distro 2 image: don't even warn
            return
        print('File {image_name} does not exist and cannot be downloaded '
              'from {remote_image}'.format(
                  image_name=image, remote_image=remote_image))
        return

    if not force and osp.exists(metadata_file):
        local_metadata = json.load(open(metadata_file))
        if local_metadata.get('md5') == metadata.get('md5') \
                and local_metadata.get('size') == metadata.get('size') \
                and osp.isfile(image_name) \
                and os.stat(image_name).st_size == metadata.get('size'):
            # if verbose:
            print('image %s is up-to-date.' % image)
            return
    # if verbose:
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
    downloader.download_file(remote_image, image_name,
                             allow_continue=not download_all,
                             use_tmp=True,
                             md5_check=metadata['md5'],
                             callback=downloader.stdout_progress)

    # move metadata to final location
    os.rename(tmp_metadata_file, metadata_file)


def delete_image(container_type, image_name):
    """
    Delete a container image files
    """
    if container_type in ('singularity', 'vbox'):
        if not os.path.isabs(image_name) and not osp.exists(image_name):
            image_name = osp.join(casa_distro_directory(), image_name)
        if os.path.exists(image_name):
            os.unlink(image_name)
        metadata = '%s.json' % image_name
        if os.path.exists(metadata):
            os.unlink(metadata)
    elif container_type == 'docker':
        raise NotImplementedError('docker case not implemented yet.')
    else:
        raise ValueError('unknown container type: %s' % container_type)


def select_environment(base_directory, **kwargs):
    """
    Select a single distro given its name or an existing distro directory.
    """
    env_list = list(iter_environments(base_directory, **kwargs))
    if len(env_list) == 1:
        return env_list[0]
    if len(env_list) > 1:
        raise ValueError(
            'Several distros found, use a more selective criterion: {0}'
            .format(', '.join(i['name'] for i in env_list))
        )
    raise ValueError('Cannot find any distro to perform requested action. '
                     'base_directory="{0}", selection={1}'.format(
                         base_directory, kwargs))


def write_environment_homedir(casa_home_host_path):
    """Create a new home directory for an environment."""
    if not osp.exists(casa_home_host_path):
        os.makedirs(casa_home_host_path)
    bashrc = osp.join(casa_home_host_path, '.bashrc')
    if not osp.exists(bashrc):
        with open(bashrc, 'w') as f:
            print(r'''
if [ -f /etc/profile ]; then
    . /etc/profile
fi

# source any bash_completion scripts
if [ -n "$CASA_BUILD" -a -d "$CASA_BUILD/etc/bash_completion.d" ]; then
    # from a build directory
    for d in "$CASA_BUILD/etc/bash_completion.d/"*; do
        if [ -f "$d" ]; then
            . "$d"
        fi
    done
elif [ -d "/casa/install/etc/bash_completion.d" ]; then
    # else from an install directory
    for d in "/casa/install/etc/bash_completion.d/"*; do
        if [ -f "$d" ]; then
            . "$d"
        fi
    done
fi

export PS1="\[\033[33m\]\u@\h \$\[\033[0m\] "

''', file=f)


exclude_from_bin = {
    'python', 'python2', 'python3', 'casa_distro', 'casa_distro_admin', 'bv',
    'bv_env', 'bv_env.sh', 'bv_env.bat', 'bv_env.py', 'bv_env_host',
    'bv_env_test', 'bv_unenv', 'bv_unenv.sh', 'bv_unit_test',
    'bv_wine_regedit',
}


def create_environment_bin_commands(source, dest):
    """
    Create, in dest, a symlink pointing to 'bv' for each file present in
    source except those in exclude_from_bin.
    """
    commands = {'casa_distro', 'casa_distro_admin'}
    commands.update(os.listdir(source))
    for command in commands:
        if command in exclude_from_bin:
            continue
        script = osp.join(dest, command)
        if osp.exists(script):
            os.remove(script)
        os.symlink('bv', script)


def run_container(config, command, gui, opengl, root, cwd, env, image,
                  container_options, base_directory, verbose):
    """
    Run a command in the container defined in the environment

    Return the exit code of the command, or raise an exception if the command
    cannot be run.
    """
    casa_home_host_path = osp.join(config['directory'], 'home')
    if not osp.exists(casa_home_host_path):
        write_environment_homedir(casa_home_host_path)

    # env_directory = config['directory']
    # if config.get('user_specific_home'):
    #     env_relative_subdirectory = osp.normcase(
    #         osp.abspath(env_directory)).lstrip(os.sep)
    #     home_path = os.path.join(
    #         os.path.expanduser('~'), '.config', 'casa-distro',
    #         env_relative_subdirectory, 'home')
    #     config.setdefault('mounts', {})
    #     config['mounts']['/casa/home'] = home_path
    #     if not os.path.exists(home_path):
    #         In case of user-specific home directories, the home dir has not
    #         been initialized at the creation of the build-workflow, so it
    #         needs to be done at first launch.
    #         os.makedirs(home_path)
    #         prepare_home(env_directory, home_path)

    container_type = config.get('container_type')
    if container_type == 'singularity':
        module = singularity
    elif container_type == 'vbox':
        raise NotImplementedError(
            'run command is not implemented for VirtualBox')
        module = vbox
    elif container_type == 'docker':
        raise NotImplementedError('run command is not implemented for Docker')
    else:
        raise ValueError('Invalid container type: {0}'.format(container_type))
    env = (env.copy() if env else {})
    branch = config.get('branch')
    if branch:
        env['CASA_BRANCH'] = bv_maker_branches[branch]
    return module.run(config,
                      command=command,
                      gui=gui,
                      opengl=opengl,
                      root=root,
                      cwd=cwd,
                      env=env,
                      image=image,
                      container_options=container_options,
                      base_directory=base_directory,
                      verbose=verbose)


class BBIDaily:
    def __init__(self,
                 jenkins=None):
        self.bbe_name = 'BBE-{0}-{1}'.format(os.getlogin(),
                                             subprocess.check_output(
                                                 ['hostname']).strip())
        self.casa_distro_src = osp.expanduser('~/casa_distro/src')
        self.casa_distro = osp.join(self.casa_distro_src, 'bin',
                                    'casa_distro')
        self.casa_distro_admin = self.casa_distro + '_admin'
        self.jenkins = jenkins
        if self.jenkins:
            if not self.jenkins.job_exists(self.bbe_name):
                self.jenkins.create_job(self.bbe_name)

    def log(self, environment, task_name, result, log,
            duration=None):
        if self.jenkins:
            self.jenkins.create_build(environment=environment,
                                      task=task_name,
                                      result=result,
                                      log=log+'\n',
                                      duration=duration)
        else:
            name = '{0}:{1}'.format(environment, task_name)
            print()
            print('  /-' + '-' * len(name) + '-/')
            print(' / ' + name + ' /')
            print('/-' + '-' * len(name) + '-/')
            print()
            print(log)

    def call_output(self, *args, **kwargs):
        p = subprocess.Popen(*args, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, **kwargs)
        output, nothing = p.communicate()
        log = ['-'*40,
               ' '.join("'{}'".format(i) for i in args),
               '-'*40,
               output]

        return p.returncode, '\n'.join(log)

    def update_casa_distro(self):
        start = time.time()
        result, log = self.call_output(['git',
                                        '-C', self.casa_distro_src,
                                        'pull'])
        duration = int(1000 * (time.time() - start))
        self.log(self.bbe_name, 'update casa_distro',
                 result, log,
                 duration=duration)
        return result == 0

    def update_base_images(self, images):
        start = time.time()
        log = []
        for image in images:
            result, output = self.call_output([self.casa_distro,
                                               'pull_image',
                                               'image={0}'.format(image)])
            log.append(output)
            if result:
                break
        duration = int(1000 * (time.time() - start))
        self.log(self.bbe_name,
                 'update images',
                 result, '\n'.join(log),
                 duration=duration)
        return result == 0

    def bv_maker(self, config, steps):
        environment = config['name']
        if self.jenkins:
            if not self.jenkins.job_exists(environment):
                self.jenkins.create_job(environment,
                                        **config)
        done = []
        failed = None
        for step in steps:
            start = time.time()
            result, log = self.call_output([self.casa_distro,
                                            'bv_maker',
                                            'name={0}'.format(config['name']),
                                            step])
            duration = int(1000 * (time.time() - start))
            self.log(environment, step, result, log, duration=duration)
            if result:
                failed = step
                break
            else:
                done.append(step)
        return (done, failed)

    def tests(self, test_config, dev_config):
        environment = test_config['name']
        if self.jenkins:
            if not self.jenkins.job_exists(environment):
                self.jenkins.create_job(environment,
                                        **test_config)
        tests = self.get_test_commands(dev_config)
        successful_tests = []
        failed_tests = []
        for test, commands in tests.items():
            log = []
            start = time.time()
            success = True
            for command in commands:
                if test_config['type'] == 'run':
                    command = command.replace('/casa/host/build/bin/bv_env',
                                              '/casa/host/install/bin/bv_env')
                result, output = self.call_output([self.casa_distro,
                                                   'run',
                                                   'name={0}'.format(
                                                       test_config['name']),
                                                   'env=BRAINVISA_'
                                                   'TEST_RUN_DATA_DIR='
                                                   '/casa/host/tests/test,'
                                                   'BRAINVISA_'
                                                   'TEST_REF_DATA_DIR='
                                                   '/casa/host/tests/ref',
                                                   '--',
                                                   'sh', '-c', command])
                if result:
                    success = False
                    log.append('FAILED: {0}\n'.format(command))
                    log.append('-' * 80)
                    log.append(output)
                    log.append('=' * 80)
                else:
                    log.append('SUCCESS: {0}\n'.format(command))
            duration = int(1000 * (time.time() - start))
            self.log(environment, test, (0 if success else 1),
                     '\n'.join(log), duration=duration)
            if success:
                successful_tests.append(test)
            else:
                failed_tests.append(test)
        if failed_tests:
            self.log(environment, 'tests failed', 1,
                     'The following tests failed: {0}'.format(
                         ', '.join(failed_tests)))
        return (successful_tests, failed_tests)

    def get_test_commands(self, config):
        '''
        Given the config of a dev environment, return a dictionary
        whose keys are name of a test (i.e. 'axon', 'soma', etc.) and
        values are a list of commands to run to perform the test.
        '''
        o = subprocess.check_output([self.casa_distro,
                                     'run',
                                     'name={0}'.format(config['name']),
                                     'cwd={0}/build'.format(
                                         config['directory']),
                                     'ctest', '--print-labels'])
        labels = [i.strip() for i in o.split('\n')[2:] if i.strip()]
        tests = {}
        for label in labels:
            p = subprocess.Popen(
                [
                    self.casa_distro,
                    'run',
                    'name={0}'.format(config['name']),
                    'cwd={0}/build'.format(
                        config['directory']),
                    'env=BRAINVISA_TEST_REMOTE_COMMAND'
                    '=echo',
                    'ctest', '-V', '-L',
                    '^{0}$'.format(label)
                ] + config.get('ctest_options', []),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            o, stderr = p.communicate()
            if p.returncode != 0:
                # We want to hide stderr unless ctest returns a nonzero exit
                # code. In the case of test filtering where no tests are
                # matched (e.g. with ctest_options=['-R', 'dummyfilter']), the
                # annoying message 'No tests were found!!!' is printed to
                # stderr by ctest, but it exits with return code 0.
                sys.stderr.write(stderr)
                raise RuntimeError('ctest failed with the above error')
            o = o.split('\n')
            # Extract the third line that follows each line containing ': Test
            # command:'
            commands = [o[i+3][o[i+3].find(':')+2:].strip()
                        for i in range(len(o))
                        if ': Test command:' in o[i]]
            if commands:  # skip empty command lists
                tests[label] = commands
        return tests

    def update_user_image(self, user_config, dev_config):
        environment = user_config['name']
        if self.jenkins:
            if not self.jenkins.job_exists(environment):
                self.jenkins.create_job(environment,
                                        **user_config)
        start = time.time()
        image = user_config['image']
        if osp.exists(image):
            os.remove(image)
        result, log = self.call_output([self.casa_distro_admin,
                                        'create_user_image',
                                        'version={0}'.format(
                                            user_config['version']),
                                        'environment_name={0}'.format(
                                            dev_config['name']),
                                        'force=yes'])
        duration = int(1000 * (time.time() - start))
        self.log(user_config['name'], 'update user image', result, log,
                 duration=duration)
        return result == 0
