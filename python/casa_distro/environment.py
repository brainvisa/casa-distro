# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function

from fnmatch import fnmatchcase
from glob import glob
import json
import os
import os.path as osp
import shutil

from casa_distro import (share_directories,
                         singularity,
                         vbox)
from casa_distro.build_workflow import prepare_home  # should be moved here

bv_maker_branches = {
    'latest_release': 'latest_release',
    'master': 'bug_fix',
    'integration': 'trunk'
}

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


def iter_user_config_files(env_directory):
    ''' List the possible user-specific casa_distro.json configuration files
        for the current user, corresponding to the given build workflow
        directory. Files are listed from lowest to highest priority, i.e. in
        the order that the configurations should be merged.
    '''
    env_relative_subdirectory = osp.normcase(
        osp.abspath(env_directory)).lstrip(os.sep)
    user_config_home = os.path.join(
        os.path.expanduser('~'), '.config', 'casa-distro'
    )
    yield os.path.join(user_config_home, 'casa_distro.json')
    yield os.path.join(
        user_config_home, env_relative_subdirectory,
        'conf', 'casa_distro.json'
    )


def iter_distros():
    """
    Iterate over all available distros. For each one, yield a
    dictionary corrasponding to the casa_distro.json file
    with the "directory" item added.
    """
    for share_directory in share_directories():
        for root, dirs, files in os.walk(share_directory):
            if 'casa_distro.json' in files:
                distro = json.load(open(osp.join(root, 'casa_distro.json')))
                # TODO: load user-specific configuration files stored in
                # ~/.config/casa-distro (see iter_user_config_files above and
                # https://github.com/brainvisa/casa-distro/issues/98)
                distro['directory'] = osp.dirname(osp.dirname(root))
                yield distro


def select_distro(distro):
    """
    Select a distro given its name or an existing distro directory.
    """
    if osp.isdir(distro):
        directory = distro
        casa_distro_json = osp.join(directory, 'host', 'conf', 'casa_distro.json')
        if osp.exists(casa_distro_json):
            distro = json.load(open(casa_distro_json))
            distro['directory'] = directory
            return distro
    else:
        for d in iter_distros():
            if d['name'] == distro:
                return d
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


def iter_environments(base_directory, **kwargs):
    """
    Iterate over environments created with "setup" command in the given
    base directory. For each one, yield a dictionary corrasponding to the
    casa_distro.json file with the "directory" item added.
    """
    for i in sorted(glob(osp.join(base_directory, '*', 'host', 'conf', 
                                  'casa_distro.json'))):
        env_conf = json.load(open(i))
        env_conf['directory'] = osp.dirname(osp.dirname(osp.dirname(i)))
        match = False
        for k, p in kwargs.items():
            if p is None:
                continue
            v = env_conf.get(k)
            if v is None or v != p:
                break
        else:
            match = True
        if match:
            yield env_conf


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


def setup(type, distro, branch, system, name, container_type, base_directory,
          image, output, vm_memory, vm_disk_size, verbose, force):
    '''
    Initialize a new build workflow directory. This creates a conf
    subdirectory with build_workflow.json, bv_maker.cfg and svn.secret
    files that can be edited before compilation.

    Parameters
    ----------
    build_workflow_directory:
        Directory containing all files of a build workflow. The following
        subdirectories are expected:
            conf: configuration of the build workflow (BioProj passwords,
                  bv_maker.cfg, etc.)
            src*: source of selected components for the workflow.
            build*: build directory used for compilation. 
            install*: directory where workflow components are installed.
            pack*: directory containing distribution packages
            wine: for Windows compilation, it is necessary to configure
                  wine according to build_workflow. All wine specific files
                  goes in that directory.
    distro_source:
        Either the name of a predefined distro (on of the directory
        located in share/distro) or a directory containing the distro
        source.
        A predefinied distro definition may be one of the buitin ones found in
        casa-distro (brainvisa, opensource, cati_platform), or one user-defined
        which will be looked for in $HOME/.config/casa-distro/distro,
        $HOME/.casa-distro/distro, or in the share/distro subdirectory inside
        the main repository directory.
    distro_name:
        Name of the distro that will be created. If omited, the name
        of the distro source (or distro source directory) is used.
    container_type: type of container thechnology to use. It can be either 
        'singularity', 'vbox', 'docker' or None (the default). If it is None,
        it tries to see if Singularity, VirtualBox or Docker is 
        installed (in that order).
    container_image: image to use for the compilation container. If no
        value is given, uses the one defined in the distro. The name
        of the image can contain the following substring are replaced:
          {distro_name}: the name of the distro
          {distro_source}: the name of the distro source template
          {casa_branch}: the name of the CASA source branch
          {sysem}: the name of the operating system
    container_test_image: image to use for the packages test container. If no
        value is given, uses the one defined in the distro. The name
        of the image can contain the following substring are replaced:
          {distro_name}: the name of the distro
          {distro_source}: the name of the distro source template
          {casa_branch}: the name of the CASA source branch
          {sysem}: the name of the operating system
    casa_branch:
        bv_maker branch to use (latest_release, bug_fix or trunk)
    system:
        Name of the target system.
    not_override:
        a list of file name that must not be overriden if they already exist

    * Typically created by bv_maker but may be extended in the future.

    '''
        
    environment = {}
    environment['casa_distro_compatibility'] = '3.0'
    environment['type'] = type
    environment['name'] = name
    environment['distro'] = distro['name']
    environment['branch'] = branch
    environment['bv_maker_branch'] = bv_maker_branches[branch]
    environment['system'] = system
    environment['container_type'] = container_type
    environment['image'] = image
    environment['vm_memory'] = vm_memory
    environment['vm_disk_size'] = vm_disk_size
    
    config = environment.setdefault('configs', {}).setdefault('default', {})
    config.setdefault('mounts', {})['/casa/host'] = '{directory}/host'
        
    config.setdefault('env', {}).update({
        'CASA_DISTRO': '{name}',
        'CASA_BRANCH': '{bv_maker_branch}',
        'CASA_SYSTEM': '{system}',
        'CASA_HOST_DIR': '{directory}',
        'HOME': '/casa/host/home'})

    if container_type == 'singularity':
        config.setdefault('gui_env', {}).update({
            'DISPLAY': '$DISPLAY',
            'XAUTHORITY': '$HOME/.Xauthority'})
    
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
    
    #TODO check_svn_secret(bwf_dir)


def run_container(environment, command, gui, cwd, env, image, 
                  container_options, base_directory, verbose):
    """
    Run a command in the container defined in the environment
    """
    env_directory = environment['directory']
    # TODO: make user_specific_home work under casa-distro 3 (see prepare_home
    # in build_workflow.py and
    # https://github.com/brainvisa/casa-distro/issues/99)
    if environment.get('user_specific_home'):
        env_relative_subdirectory = osp.normcase(
            osp.abspath(env_directory)).lstrip(os.sep)
        home_path = os.path.join(
            os.path.expanduser('~'), '.config', 'casa-distro',
            env_relative_subdirectory, 'home')
        environment.setdefault('mounts', {})
        environment['mounts']['/casa/home'] = home_path
        if not os.path.exists(home_path):
            # In case of user-specific home directories, the home dir has not
            # been initialized at the creation of the build-workflow, so it
            # needs to be done at first launch.
            os.makedirs(home_path)
            prepare_home(env_directory, home_path)

    container_type = environment.get('container_type')
    if container_type == 'singularity':
        module = singularity
    elif container_type == 'vbox':
        raise NotImplementedError('run command is not implemented for Docker')
        module = vbox
    elif container_type == 'docker':
        raise NotImplementedError('run command is not implemented for Docker')
    else:
        raise ValueError('Invalid container type: {0}'.format(container_type))
    module.run(environment, 
               command=command, 
               gui=gui, 
               cwd=cwd, 
               env=env,
               image=image,
               container_options=container_options,
               base_directory=base_directory,
               verbose=verbose)
