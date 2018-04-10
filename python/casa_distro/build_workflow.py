from __future__ import absolute_import
from __future__ import print_function

import os
import os.path as osp
import glob
import shutil
import json

from casa_distro import share_directory, linux_os_ids
from casa_distro.docker import run_docker
from casa_distro.singularity import run_singularity


def iter_build_workflow(build_workflows_repository, distro='*', branch='*',
                        system='*'):
    for i in glob.glob(osp.join(build_workflows_repository, distro, '%s_%s' % (branch, system), 'conf')):
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
              if os.path.exists(d):
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
        print('\nThis file should contain the two following lines (replacing '
              '"your_login" and "your_password" by appropriate values:\n')
        print('SVN_USERNAME=your_login')
        print('SVN_PASSWORD=your_password\n')
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
    distro_name:
        Name of the distro that will be created. If omited, the name
        of the distro source (or distro source directory) is used.
    container_type: type of container thechnology to use. It can be either 
        'singularity', 'docker' or None (the default). If it is None,
        it first try to see if Singularity is installed or try to see if
        Docker is installed.
    container_image: image to use for the compilation container. If no
        value is given, uses the one defined in the distro. In the name
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
    if not osp.isdir(distro_source):
        distro_source_dir = osp.join(share_directory, 'distro', distro_source)
    else:
        raise ValueError('distro value %s is not a predefined value: '
                            'base_distro should be provided' % distro)
    if not osp.isdir(distro_source_dir):
        raise ValueError('%s is not a valid value for distro_source because '
                         '%s is not a directory' % (repr(distro_source),
                                                    repr(distro_source_dir)))
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
    
    if casa_branch not in ('bug_fix', 'trunk', 'latest_release'):
        raise ValueError('Invalid value for casa_branch: %s' % repr(casa_branch))
    
    casa_distro_source_json = osp.join(distro_source_dir, 'conf', 'casa_distro.json')
    if os.path.exists(casa_distro_source_json):
        casa_distro = json.load(open(casa_distro_source_json))
    else:
        casa_distro = {}

    casa_distro.update(dict(
        distro_source = distro_source,
        distro_name = distro_name,
        container_type = container_type,
        casa_branch = casa_branch,
        system = system,
        container_volumes = {'%(build_workflow_dir)s/conf': '/casa/conf',
                             '%(build_workflow_dir)s/src': '/casa/src',
                             '%(build_workflow_dir)s/build': '/casa/build',
                             '%(build_workflow_dir)s/install': '/casa/install',
                             '%(build_workflow_dir)s/pack': '/casa/pack',
                             '%(build_workflow_dir)s/tests': '/casa/tests',
                             '%(build_workflow_dir)s/custom/src': '/casa/custom/src',
                             '%(build_workflow_dir)s/custom/build': '/casa/custom/build',
                             '$HOME/.ssh/id_rsa': '/root/.ssh/id_rsa',
                             '$HOME/.ssh/id_rsa.pub': '/root/.ssh/id_rsa.pub'},
        container_env = {'CASA_DISTRO': '%(distro_name)s',
                         'CASA_BRANCH': '%(casa_branch)s',
                         'CASA_SYSTEM': '%(system)s',
                         'CASA_HOST_DIR': '%(build_workflow_dir)s'}))
    if container_type == 'docker':
        container_options = ['--net=host']
    else:
        container_options = None
    if container_options:
        casa_distro['container_options'] = container_options
    
    if not container_image:
        container_image = casa_distro.get('container_image')
        if container_image is None:
            raise ValueError('No container_image found in %s' % casa_distro_source_json)
    container_image = container_image % casa_distro
    casa_distro['container_image'] = container_image
    
    build_workflow_directory = build_workflow_directory % casa_distro
    bwf_dir = osp.normpath(osp.abspath(build_workflow_directory))
    print('build_workflow_directory:', build_workflow_directory)
    if not osp.exists(bwf_dir):
        os.makedirs(bwf_dir)
    
    os_dir = osp.join(distro_source_dir, system)
    all_subdirs = ('conf', 'src', 'build', 'install', 'tests', 'pack',
                   'custom', 'custom/src', 'custom/build')
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



def run_container(bwf_directory, command, gui=False, interactive=False, tmp_container=True, container_options=[], verbose=False):
    '''Run any command in the container defined in the build workflow directory
    '''
    casa_distro_json = osp.join(bwf_directory, 'conf', 'casa_distro.json')
    casa_distro = json.load(open(casa_distro_json))
    casa_distro['build_workflow_dir'] = bwf_directory
    container_type = casa_distro.get('container_type')
    if container_type:
        if container_type == 'singularity':
            run_singularity(casa_distro, command, gui=gui, interactive=interactive, tmp_container=tmp_container, container_options=container_options, verbose=verbose)
        elif container_type == 'docker':
            run_docker(casa_distro, command, gui=gui, interactive=interactive, tmp_container=tmp_container, container_options=container_options, verbose=verbose)            
        else:
            raise ValueError('%s is no a valid container system (in "%s")' % (container_type, casa_distro_json))
    else:
        raise ValueError('No container_type in "%s"' % casa_distro_json)

