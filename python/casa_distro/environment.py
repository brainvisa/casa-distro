# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function

from fnmatch import fnmatchcase
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

bv_maker_branches = {
    'latest_release': 'latest_release',
    'master': 'bug_fix',
    'integration': 'trunk'
}


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
            oldv = d[k]
            if isinstance(oldv, dict):
                merge_config(oldv, v)
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



def iter_distros():
    """
    Iterate over all available distros. For each one, yield a
    dictionary corresponding to the casa_distro.json file
    with the "directory" item added.
    """
    for share_directory in share_directories():
        for root, dirs, files in os.walk(share_directory):
            if 'casa_distro.json' in files:
                distro = json.load(open(osp.join(root, 'casa_distro.json')))
                distro['directory'] = osp.dirname(osp.dirname(root))
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
    Iterate over environments created with "setup" command in the given
    base directory. For each one, yield a dictionary corrasponding to the
    casa_distro.json file with the "directory" item added.
    """
    for casa_dsitro_json in sorted(glob(osp.join(base_directory, '*', 'host', 'conf', 
                                  'casa_distro.json'))):
        environment_config = json.load(open(casa_dsitro_json))
        directory = osp.dirname(osp.dirname(osp.dirname(casa_dsitro_json)))
        config = {}
        config['config_files'] = [casa_dsitro_json]
        config['directory'] = directory
        config['mounts'] = {'/casa/host':'{directory}/host'}
        config['env'] = {
            'CASA_DISTRO': '{name}',
            'CASA_BRANCH': '{bv_maker_branch}',
            'CASA_SYSTEM': '{system}',
            'CASA_HOST_DIR': '{directory}',
            'HOME': '/casa/home'}
        if environment_config['container_type'] == 'singularity':
            config.setdefault('gui_env', {}).update({
                'DISPLAY': '$DISPLAY',
                'XAUTHORITY': '$HOME/.Xauthority'})

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
            if v is None or v != p:
                break
        else:
            match = True
        if match:
            yield config


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


def setup(type, distro, branch, system, name, container_type, writable,
          base_directory, image, output, verbose, force):
    '''
    Create a new run or dev environment.

    Parameters
    ----------
    type
        Environment type to setup. Either "run" for users or "dev" for
        developers
    distro
        Distro used to build this environment. This is typically "brainvisa",
        "opensource" or "cati_platform". Use "casa_distro distro" to list all
        currently available distro. Choosing a distro is mandatory to create a
        new environment. If the environment already exists, distro must be set
        only to reset configuration files to their default values.
    branch
        Name of the source branch to use for dev environments. Either "latest_release",
        "master" or "integration".
    system
        System to use with this environment. By default, it uses the first supported
        system of the selected distro.
    name
        Name of the environment (no other environment must have the same name).
    container_type
        Type of virtual appliance to use. Either "singularity", "vbox" or "docker".
        If not given try to gues according to installed container software in the
        following order : Singularity, VirtualBox and Docker.
    writable
        size in bytes of a writable file system that can be used to make environement specific
        modification to the container file system. If not 0, this will create an
        overlay.img file in the base environment directory. This file will contain the
        any modification done to the container file system.
    base_directory
        Directory where images and environments are stored
    image
        Location of the virtual image for this environement.
    url
*        URL where to download image if it is not found.
    output
        Directory where the environement will be stored.
    verbose
        Print more detailed information if value is "yes", "true" or "1".
    force
        Allow to perform setup with unsuported configuration.
    '''
        
    environment = {}
    environment['casa_distro_compatibility'] = '3'
    environment['type'] = type
    environment['name'] = name
    environment['distro'] = distro['name']
    environment['branch'] = branch
    environment['bv_maker_branch'] = bv_maker_branches[branch]
    environment['system'] = system
    environment['container_type'] = container_type
    environment['image'] = image
    
    
    if not osp.exists(output):
        os.makedirs(output)
    
    src = osp.join(distro['directory'], 'host')
    dst = osp.join(output, 'host')
    copytree(src, dst)
        
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
                resize_ext3_file(overlay, size)
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
