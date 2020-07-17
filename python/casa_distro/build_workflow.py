# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function

import collections
import sys
import os
import os.path as osp
import glob
import shutil
import json
import copy

from casa_distro import six
from casa_distro import log, share_directories, linux_os_ids
from casa_distro.docker import run_docker, update_docker_image
from casa_distro.singularity import (download_singularity_image,
                                     run_singularity,
                                     update_singularity_image)


def update_dict_recursively(dict_to_update, dict_to_read):
    '''
    Recursively merge dict_to_read into dict_to_update
    '''
    for k, v in six.iteritems(dict_to_read):
        if (k in dict_to_update and isinstance(dict_to_update[k], dict)
                and isinstance(v, collections.Mapping)):
            update_dict_recursively(dict_to_update[k],
                                    dict_to_read[k])
        else:
            dict_to_update[k] = dict_to_read[k]



def iter_build_workflow(build_workflows_repository, distro='*', branch='*',
                        system='*'):
    for i in sorted(glob.glob(osp.join(build_workflows_repository, distro,
                                       '%s_%s' % (branch, system), 'conf'))):
        if not os.path.exists(osp.join(i, 'casa_distro.json')):
            continue # not a casa-distro 2.x directory
        d, branch_system = osp.split(osp.dirname(i))
        the_branch, the_system = branch_system.rsplit('_', 1)
        d, the_distro  = osp.split(d)
        yield (the_distro, the_branch, the_system, osp.dirname(i))


def find_in_path(file):
    '''
    Look for a file in a series of directories contained in ``PATH`` environment variable.
    '''
    path = os.environ.get('PATH').split(os.pathsep)
    for i in path:
        p = osp.normpath(osp.abspath(i))
        if p:
            r = glob.glob(osp.join(p, file))
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


def check_svn_secret(bwf_dir, warn_type='NOTE'):
    ''' Checks the svn.secret file does not exist. Print a message if it does
    not.

    Parameters:
    -----------
    bwf_dir: str
        build workflow directory
    warn_type: str
        warning message type ('NOTE', 'ERROR', ...)

    Returns:
    --------
        True if the file is here, False if it is missing
    '''
    if not os.path.exists(osp.join(bwf_dir, 'conf', 'svn.secret')):
        print('\n------------------------------------------------------------')
        print('**%s:**' % warn_type)
        print('Before using "casa_distro bv_maker" you will have to '
              'create the svn.secret file with your Bioproj login / password '
              'in order to access the BrainVisa repository.')
        print('Place it at the following location:\n')
        print(osp.join(bwf_dir, 'conf', 'svn.secret'))
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
        print(osp.join(bwf_dir, 'conf', 'bv_maker.cfg'))
        print('------------------------------------------------------------')
        print()
        return False
    return True


def create_build_workflow_directory(build_workflow_directory, 
                                    distro_source='opensource',
                                    distro_name=None,
                                    container_type = None,
                                    container_image = None,
                                    container_test_image = None,
                                    casa_branch='latest_release',
                                    system=linux_os_ids[0],
                                    not_override=[],
                                    verbose=None):
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
        'singularity', 'docker' or None (the default). If it is None,
        it first try to see if Singularity is installed or try to see if
        Docker is installed.
    container_image: image to use for the compilation container. If no
        value is given, uses the one defined in the distro. The name
        of the image can contain the following substring are replaced:
          %(distro_name): the name of the distro
          %(distro_source): the name of the distro source template
          %(casa_branch): the name of the CASA source branch
          %(sysem): the name of the operating system
    container_test_image: image to use for the packages test container. If no
        value is given, uses the one defined in the distro. The name
        of the image can contain the following substring are replaced:
          %(distro_name): the name of the distro
          %(distro_source): the name of the distro source template
          %(casa_branch): the name of the CASA source branch
          %(sysem): the name of the operating system
    casa_branch:
        bv_maker branch to use (latest_release, bug_fix or trunk)
    system:
        Name of the target system.
    not_override:
        a list of file name that must not be overriden if they already exist

    * Typically created by bv_maker but may be extended in the future.

    '''
    verbose = log.getLogFile(verbose)

    for share_directory in share_directories():
        distro_source_dir = osp.join(share_directory, 'distro', distro_source)
        if osp.isdir(distro_source_dir):
            break
    else:
        distro_source_dir = distro_source
        if not osp.isdir(distro_source_dir):
            raise ValueError('distro_source value %s is not a predefined '
                            'value nor a valid directory' % distro_source)
    if distro_name is None:
        distro_name = osp.basename(distro_source_dir)
        
    if not container_type:
        if find_in_path('singularity'):
            container_type = 'singularity'
        elif find_in_path('docker'):
            container_type = 'docker'
        else:
            raise ValueError('Cannot guess container_type according to '
                             'Singularity or Docker command research')
    
    if casa_branch not in ('bug_fix', 'trunk', 'latest_release',
                           'release_candidate'):
        raise ValueError('Invalid value for casa_branch: %s' % repr(casa_branch))
    
    casa_distro_source_json = osp.join(distro_source_dir, 'conf',
                                       'casa_distro.json')
    if os.path.exists(casa_distro_source_json):
        casa_distro = load_casa_distro_json(casa_distro_source_json)
    else:
        casa_distro = {}

    container_mounts = {'/casa/home': '%(build_workflow_dir)s/home',
                        '/casa/conf': '%(build_workflow_dir)s/conf',
                        '/casa/src': '%(build_workflow_dir)s/src',
                        '/casa/build': '%(build_workflow_dir)s/build',
                        '/casa/install': '%(build_workflow_dir)s/install',
                        '/casa/pack': '%(build_workflow_dir)s/pack',
                        '/casa/tests': '%(build_workflow_dir)s/tests',
                        '/casa/custom/src': '%(build_workflow_dir)s/custom/src',
                        '/casa/custom/build': '%(build_workflow_dir)s/custom/build'}
        
    container_env = {'CASA_DISTRO': '%(distro_name)s',
                     'CASA_BRANCH': '%(casa_branch)s',
                     'CASA_SYSTEM': '%(system)s',
                     'CASA_HOST_DIR': '%(build_workflow_dir)s',
                     'BRAINVISA_TESTS_DIR': '/casa/tests/test',
                     'BRAINVISA_TEST_REF_DATA_DIR': '/casa/tests/ref',
                     'BRAINVISA_TEST_RUN_DATA_DIR':'/casa/tests/test'}

    # Set default user home
    if casa_distro.get('container_env', {}).get('HOME') is None:
        container_env['HOME'] = '/casa/home'
    
    init_cmd = casa_distro.get('init_workflow_cmd')
    if system.startswith('windows'):
        container_mounts['/casa/sys'] = '%(build_workflow_dir)s/sys'
        
        if casa_distro.get('container_env', {}).get('WINEPREFIX') is None:
            container_env['WINEPREFIX'] = '/casa/sys/wine'
            container_env['WINEDLLOVERRIDES'] = 'mscoree,mshtml='

        if init_cmd is None:
            init_cmd = 'init-workflow'

            # Define the default command that must be used during initialization
            casa_distro['init_workflow_cmd'] = init_cmd

    alt_configs = {}

        
    update_dict_recursively(
        casa_distro,
        dict(distro_source = distro_source,
            distro_name = distro_name,
            container_type = container_type,
            casa_branch = casa_branch,
            system = system,
            container_mounts = container_mounts,
            container_env = container_env))

    if not container_image:
        container_image = casa_distro.get('container_image')
        if container_image is None:
            raise ValueError('No container_image found in %s' % casa_distro_source_json)
    container_image = container_image % casa_distro
    if os.path.exists(container_image) and not os.path.isabs(container_image):
        container_image = os.path.abspath(container_image)
    casa_distro['container_image'] = container_image
                
    if not container_test_image:
        container_test_image = casa_distro.get('alt_configs', {}).get(
            'test', {}).get('container_image')
        if container_test_image is not None:
            container_test_image = container_test_image % casa_distro
            if os.path.exists(container_test_image) \
                    and not os.path.isabs(container_test_image):
                container_test_image = os.path.abspath(container_test_image)
            casa_distro.setdefault('alt_configs', {}).setdefault(
                'test', {})['container_image'] = container_test_image

    if container_type == 'docker':
        # Set default ssh files to mount because docker does not support to 
        # mount a directory not readable by root
        casa_distro.setdefault('container_mounts', {}).setdefault(
            '%s/.ssh/id_rsa' % container_env.get('HOME', ''),
            '$HOME/.ssh/id_rsa')
        casa_distro.setdefault('container_mounts', {}).setdefault(
            '%s/.ssh/id_rsa.pub' % container_env.get('HOME', ''),
            '$HOME/.ssh/id_rsa.pub')
    
        container_options = ['--net=host']
        if not sys.platform.startswith('win'):
            container_options += ['--user={0}:{1}'.format(os.getuid(),os.getgid())]
        gui_options = ['-v', '/tmp/.X11-unix:/tmp/.X11-unix',
                       '-e', 'QT_X11_NO_MITSHM=1', 
                       '--privileged', 
                       '-e', 'DISPLAY=:0',
                       '-v', '/usr/share/X11/locale:/usr/share/X11/locale:ro']
        if osp.exists('/dev/nvidiactl'):
            nv_dirs = glob.glob('/usr/lib/nvidia-???')
            if nv_dirs:
                nv_dir = nv_dirs[0]
                gui_options += [ '--device=/dev/nvidia0:/dev/nvidia0',
                                 '--device=/dev/nvidiactl',
                                 '-v', '%s:/usr/lib/nvidia-drv:ro' % nv_dir, 
                                 '-e', 'LD_LIBRARY_PATH=/usr/lib/nvidia-drv' ]
        casa_distro['container_gui_options'] = gui_options
    elif container_type == 'singularity':
        container_options = ['--pwd', '/casa/home']
        container_gui_env = {'DISPLAY': '${DISPLAY}',
                             'XAUTHORITY': '${HOME}/.Xauthority'}
        casa_distro['container_gui_env'] = container_gui_env
        
    else:
        raise ValueError('Unsupported container type: %s' % container_type)
    if container_options:
        casa_distro['container_options'] = container_options
    
    build_workflow_directory = build_workflow_directory % casa_distro
    bwf_dir = osp.normpath(osp.abspath(build_workflow_directory))
    print('build_workflow_directory:', build_workflow_directory)
    if not osp.exists(bwf_dir):
        os.makedirs(bwf_dir)
    
    os_dir = osp.join(distro_source_dir, system)
    all_subdirs = ('conf', 'src', 'build', 'install', 'tests', 'pack',
                   'custom', 'custom/src', 'custom/build', 'home', 'home/tmp')
    more_dirs = tuple(i for i in os.listdir(distro_source_dir) if i not in all_subdirs and 
                      osp.isdir(osp.join(distro_source_dir,i)))
    all_subdirs = all_subdirs + more_dirs
    if system.startswith('windows'):
        all_subdirs += ('sys',)
    
    for subdir in all_subdirs:
        sub_bwf_dir = osp.join(bwf_dir, subdir)
        if not osp.exists(sub_bwf_dir):
            os.mkdir(sub_bwf_dir)
        sub_distro_dir = osp.join(distro_source_dir, subdir)
        if osp.exists(sub_distro_dir):
            for i in os.listdir(sub_distro_dir):
                cp(osp.join(sub_distro_dir, i), osp.join(sub_bwf_dir, i), 
                   not_override=not_override, verbose=verbose)
        sub_os_dir = osp.join(os_dir, subdir)
        if osp.exists(sub_os_dir):
            for i in os.listdir(sub_os_dir):
                cp(osp.join(sub_os_dir, i), osp.join(sub_bwf_dir, i),
                   not_override=not_override, verbose=verbose)
    
    casa_distro_json = osp.join(bwf_dir, 'conf', 'casa_distro.json')
    json.dump(casa_distro, open(casa_distro_json, 'w'), indent=4)

    check_svn_secret(bwf_dir)
    
    if container_type == 'singularity':
        update_singularity_image(
            osp.dirname(osp.dirname(build_workflow_directory)),
            container_image,
            verbose=verbose)

    update_build_workflow(build_workflow_directory)

    if init_cmd:
        # Initialize container for current user
        run_container(bwf_dir, [init_cmd], verbose=verbose)

def update_build_workflow(build_workflow_directory, verbose=None,
                          command=None):
    '''
    Update an existing build workflow directory. It basically:
    * recreates the casa_distro run script
    * creates a symlink to the home .Xauthority file, if it exists,
      in the casa home dir
    * writes a .bashrc in the casa home dir if there is not any yet.
    * runs the command 'git lfs install' if git-lfs is available

    Parameters
    ----------
    build_workflow_directory:
        Directory containing all files of a build workflow.
    verbose: bool
        verbose mode
    command: str
        casa_distro command actually called in the run script. May be either
        "host" (the calling command from the host system), "workflow" (use the
        sources from the build-workflow, the default), or a hard-coded path to
        the casa_distro command.
    '''
    bin_dir = os.path.join(build_workflow_directory, 'bin')
    if verbose:
        print('update_build_workflow:', build_workflow_directory)
    if not os.path.exists(bin_dir):
        if verbose:
            print('create directory:', bin_dir)
        os.mkdir(bin_dir)
    script_file = os.path.join(bin_dir, 'casa_distro')
    if command in (None, 'workflow'):
        # try to use casa_distro in sources from the build workflow, then if
        # it is not found, fallback to the calling one.
        branches = ['master', 'integration', 'release_candidate',
                    'latest_release']
        try_paths = [os.path.join(build_workflow_directory, 'src',
                                  'development', 'casa-distro', branch, 'bin',
                                  'casa_distro')
                    for branch in branches]
    elif command == 'host':
        # no default path, use the fallback
        try_paths = []
    else:
        try_paths = [command]
    try_paths = [p for p in try_paths if os.path.exists(p)]
    casa_distro_path = (try_paths
                        + [os.path.normpath(os.path.abspath(sys.argv[0]))])[0]
    if sys.platform.startswith('win'):
        # windows: .bat script
        script_file += '.bat'
        with open(script_file, 'w') as f:
            f.write('''@setlocal
@"%s" "%s" \%*
@endlocal''' % (sys.executable, casa_distro_path))
    else:
        # unix: bash script
        with open(script_file, 'w') as f:
            f.write('''#!/bin/bash
exec %s %s "$@"''' % (sys.executable, casa_distro_path))
    os.chmod(script_file, 0o775)
    if verbose:
        print('created run script:', script_file)

    prepare_home(build_workflow_directory,
                 os.path.join(build_workflow_directory, 'home'),
                 verbose=verbose)


def prepare_home(build_workflow_directory, home_path, verbose=None):
    '''
    Prepare the home directory of the container.
    * creates a symlink to the home .Xauthority file, if it exists,
      in the casa home dir
    * writes a .bashrc in the casa home dir if there is not any yet.
    * runs the command 'git lfs install' if git-lfs is available


    Parameters
    ----------
    build_workflow_directory:
        Directory containing all files of a build workflow.
    verbose: bool
        verbose mode
    '''
    # symlink $HOME/.Xauthority if this file exists, in order to enable display
    # through ssh ($HOME is mounted in singularity)
    homexauth = os.path.join(os.environ['HOME'], '.Xauthority')
    if os.path.exists(homexauth):
        casaxhauth = os.path.join(home_path, '.Xauthority')
        if os.path.exists(casaxhauth):
            os.unlink(casaxhauth)
        os.symlink(homexauth, casaxhauth)

    bashrc = os.path.join(home_path, '.bashrc')
    if not os.path.exists(bashrc):
        open(bashrc, 'w').write(r'''
if [ -f /etc/profile ]; then
    . /etc/profile
fi

# source any bash_completion scripts
if [ -d "$CASA_BUILD/etc/bash_completion.d" ]; then
    for d in "$CASA_BUILD/etc/bash_completion.d/"*; do
        if [ -f "$d" ]; then
            . "$d"
        fi
    done
fi

# colored prompt to show we are in a casa-distro shell
export PS1='\[\033[33m\]\u@\h \$\[\033[0m\] '
# convenient aliases
alias ls='ls -F --color'
alias ll='ls -als'
''')
    # initialize git-lfs for the local home
    run_container(
        build_workflow_directory,
        ['bash', '-c',
         'type git-lfs > /dev/null 2>&1 && git lfs install || echo "not using git-lfs"'],
        verbose=verbose)


def merge_dict(d, od):
    ''' Deep-merge JSON objects (dictionaries are merged recursively, lists are
        concatenated)
    '''
    for key, v in od.items():
        if key not in d:
            d[key] = v
        else:
            oldv = d[key]
            if isinstance(oldv, dict):
                merge_dict(oldv, v)
            elif isinstance(oldv, list):
                oldv += v
            else:
                d[key] = v


def load_casa_distro_json(filename):
    ''' Load a casa_distro.json file, converting it to the latest version.
    '''
    with open(filename) as f:
        conf = json.load(f)
    if 'container_volumes' in conf:
        # Convert values from the deprecated `container_volumes` key
        mounts = conf.setdefault('container_mounts', {})
        for host_dir, container_dir in six.iteritems(conf['container_volumes']):
            mounts[container_dir] = host_dir
        del conf['container_volumes']
    return conf


def merge_config(casa_distro, conf):
    ''' Merge casa_distro dictionary config with an alternative config
        sub-directory found as key ``conf``
    '''
    if conf not in ('dev', '', None, 'default'):
        # an alternative conf has been specified: merge sub-dictionary
        casa_distro = copy.deepcopy(casa_distro)
        merge_dict(casa_distro, casa_distro.get('alt_configs', {})[conf])
    return casa_distro


def list_user_config_files(bwf_directory):
    ''' List the possible user-specific casa_distro.json configuration files
        for the current user, corresponding to the given build workflow
        directory. Files are listed from lowest to highest priority, i.e. in
        the order that the configurations should be merged.
    '''
    bwf_relative_subdirectory = osp.normcase(
        osp.abspath(bwf_directory)).lstrip(os.sep)
    user_config_home = os.path.join(
        os.path.expanduser('~'), '.config', 'casa-distro'
    )
    yield os.path.join(user_config_home, 'casa_distro.json')
    yield os.path.join(
        user_config_home, bwf_relative_subdirectory,
        'conf', 'casa_distro.json'
    )


def run_container(bwf_directory, command, gui=False, interactive=False,
                  tmp_container=True, container_image=None,
                  cwd=None, env=None,
                  container_options=[], verbose=False, conf='dev'):
    '''Run any command in the container defined in the build workflow directory
    '''
    casa_distro_json = osp.join(bwf_directory, 'conf', 'casa_distro.json')
    casa_distro = load_casa_distro_json(casa_distro_json)

    # Read a user-specific configuration file stored in ~/.config/casa-distro
    for user_casa_distro_json in list_user_config_files(bwf_directory):
        if osp.exists(user_casa_distro_json):
            user_config = load_casa_distro_json(user_casa_distro_json)
            merge_dict(casa_distro, user_config)

    casa_distro = merge_config(casa_distro, conf)
    casa_distro['build_workflow_dir'] = bwf_directory
    container_type = casa_distro.get('container_type')

    if casa_distro.get('user_specific_home'):
        bwf_relative_subdirectory = osp.normcase(
            osp.abspath(bwf_directory)).lstrip(os.sep)
        home_path = os.path.join(
            os.path.expanduser('~'), '.config', 'casa-distro',
            bwf_relative_subdirectory, 'home')
        casa_distro.setdefault('container_mounts', {})
        casa_distro['container_mounts']['/casa/home'] = home_path
        if not os.path.exists(home_path):
            # In case of user-specific home directories, the home dir has not
            # been initialized at the creation of the build-workflow, so it
            # needs to be done at first launch.
            os.makedirs(home_path)
            prepare_home(bwf_directory, home_path)

    if container_type:
        if container_type == 'singularity':
            run_singularity(casa_distro, command, gui=gui,
                            interactive=interactive,
                            tmp_container=tmp_container,
                            container_image=container_image,
                            cwd=cwd, env=env,
                            container_options=container_options,
                            verbose=verbose)
        elif container_type == 'docker':
            run_docker(casa_distro, command, gui=gui,
                       interactive=interactive,
                       tmp_container=tmp_container,
                       cwd=cwd, env=env,
                       container_image=container_image,
                       container_options=container_options,
                       verbose=verbose)
        else:
            raise ValueError('%s is no a valid container system (in "%s")' % (container_type, casa_distro_json))
    else:
        raise ValueError('No container_type in "%s"' % casa_distro_json)

def update_container_image(build_workflows_repository, container_type,
                           container_image, verbose=False):
    if container_type == 'singularity':
        update_singularity_image(build_workflows_repository,
                                 container_image,
                                 verbose=verbose)
    elif container_type == 'docker':
        update_docker_image(container_image)
    else:
        raise ValueError('%s is no a valid container system' % container_type)
    
def delete_build_workflow(bwf_directory):
    shutil.rmtree(bwf_directory)

