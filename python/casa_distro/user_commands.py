from __future__ import absolute_import
from __future__ import print_function

import sys
import tempfile
import os.path as osp
import time
import subprocess
import traceback
import json

from casa_distro import six
from casa_distro import linux_os_ids
from casa_distro.command import command
from casa_distro.defaults import (default_build_workflow_repository,
                                  default_repository_server,
                                  default_repository_server_directory,
                                  default_repository_login,
                                  default_distro,
                                  default_branch)
from casa_distro.build_workflow import (iter_build_workflow, run_container,
                                        create_build_workflow_directory,
                                        update_container_image, merge_config,
                                        update_build_workflow)
from casa_distro.singularity import (create_writable_singularity_image,
                                     singularity_root_shell)


def verbose_bool(verbose):
    verbose_b = False
    if verbose in ('True', 'true', '1'):
        verbose_b = True
    elif verbose in ('False', 'false', '0'):
        verbose_b = False
    elif verbose is not None:
        verbose_b = bool(int(verbose))
    return verbose_b


def display_summary(status):
    # Display summary
    sys.stdout.flush()
    sys.stderr.flush()
    messages = ['\ncasa_distro summary:']
    print(messages[0])

    global_failed = False
    first_start = None
    last_stop = None
    for (d, b, s), (es, bwf_dir) in six.iteritems(status):
        status = es.get_status_mapped()
        if status != '':
            message = '%s distro=%s branch=%s system=%s: %s' % (status, d, 
                                                                b, s, bwf_dir)
            start = es.start_time
            if start:
                if first_start is None:
                    first_start = start
                message += ', started: %04d/%02d/%02d %02d:%02d' \
                    % start[:5]
            stop = es.stop_time
            if stop:
                last_stop = stop
                message += ', stopped: %04d/%02d/%02d %02d:%02d' \
                    % stop[:5]
            messages.append(message)
            print(message)
            if es.error_code:
                global_failed = True

    if global_failed:
        status = 'There were errors.'
    else:
        status = 'All went good.'
    print(status)


class ExecutionStatus:
    status_map = {'not run': '',
                  'succeeded': 'OK         ',
                  'failed': 'FAILED     ',
                  'interrupted': 'INTERRUPTED'}
 
    def __init__(self,
                    error_code = None, 
                    exception = None, 
                    status = 'not run',
                    start_time = None,
                    stop_time = None):
        self.error_code = error_code
        self.exception = exception
        self.status = status
        self.start_time = start_time
        self.stop_time = stop_time

    def get_status_mapped(self):
        return self.status_map.get(self.status)


@command
def create(distro_source=default_distro,
           distro_name=None,
           container_type = None,
           container_image = None,
           container_test_image = None,
           branch=default_branch,
           system=linux_os_ids[0],
           not_override='bv_maker.cfg,svn.secret',
           build_workflows_repository=default_build_workflow_repository,
           verbose=None):
    '''
    Initialize a new build workflow directory. This creates a conf
    subdirectory with casa_distro.json, bv_maker.cfg and svn.secret
    files that can be edited before compilation.

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
        value is given, uses the one defined in the distro.
    
    container_test_image: image to use for the package tests container. If no
        value is given, uses the one defined in the distro.

    branch:
        bv_maker branch to use (latest_release, bug_fix or trunk)
    
    system:
        Name of the target system.
    
    not_override:
        a coma separated list of file name that must not be overriden 
        if they already exist.
    '''
    not_override_lst = not_override.split(',')
    bwf_directory = osp.join(build_workflows_repository, '%(distro_name)s',
                             '%(casa_branch)s_%(system)s')
    create_build_workflow_directory(build_workflow_directory=bwf_directory,
                                    distro_source=distro_source,
                                    distro_name=distro_name,
                                    container_type=container_type,
                                    container_image=container_image,
                                    container_test_image=container_test_image,
                                    casa_branch=branch,
                                    system=system,
                                    not_override=not_override_lst,
                                    verbose=verbose)

# "list" cannot be used as a function name in Python. Therefore, the
# command name in the command-line is not the same as the corresponding
# Python function.
@command('list')
def list_command(distro='*', branch='*', system='*', 
         build_workflows_repository=default_build_workflow_repository,
         verbose=None):
    '''
    List (eventually selected) build workflows created by "create" command.
    '''
    
    for d, b, s, bwf_dir in iter_build_workflow(build_workflows_repository,
                                                distro=distro, branch=branch,
                                                system=system):
        conf_file = osp.join(bwf_dir, 'conf', 'casa_distro.json')
        wf_conf = json.load(open(conf_file))
        print('distro=%s branch=%s system=%s'
              % (wf_conf['distro_name'], wf_conf['casa_branch'],
                 wf_conf['system']))
        print('  directory:', bwf_dir)
        if verbose_bool(verbose):
            print(open(osp.join(bwf_dir, 'conf', 'casa_distro.json')).read())

@command
def update(distro='*',
           branch='*',
           system='*',
           build_workflows_repository=default_build_workflow_repository,
           verbose=None):
    '''
    Update an existing build workflow directory. For now it only re-creates
    the run script in bin/casa_distro, pointing to the casa_distro command
    used to actually perform the update.

    distro:
        Name of the distro that will be created. If omited, the name
        of the distro source (or distro source directory) is used.

    branch:
        bv_maker branch to use (latest_release, bug_fix or trunk)

    system:
        Name of the target system.
    '''
    images_to_update = {}
    for d, b, s, bwf_dir in iter_build_workflow(build_workflows_repository,
                                                distro=distro, branch=branch,
                                                system=system):
        update_build_workflow(bwf_dir, verbose=verbose)

@command
def update_image(distro='*', branch='*', system='*', 
         build_workflows_repository=default_build_workflow_repository,
         verbose=None):
    '''
    Update the container images of (eventually selected) build workflows
    created by "create" command.
    '''
    images_to_update = {}
    for d, b, s, bwf_dir in iter_build_workflow(build_workflows_repository,
                                                distro=distro, branch=branch,
                                                system=system):
        casa_distro = json.load(open(osp.join(bwf_dir, 'conf',
                                              'casa_distro.json')))
        confs = set(['dev'])
        confs.update(casa_distro.get('alt_configs', {}).keys())
        for conf in confs:
            wfconf = merge_config(casa_distro, conf)
            images_to_update.setdefault(wfconf['container_type'], set()).add(
                wfconf['container_image'])
        if verbose_bool(verbose):
            print('images_to_update:', images_to_update)
    if not images_to_update:
        print('No build workflow match selection criteria', file=sys.stderr)
        return 1
    for container_type, container_images in six.iteritems(images_to_update):
        for container_image in container_images:
            update_container_image(build_workflows_repository,
                                   container_type, container_image,
                                   verbose=verbose) 


@command
def shell(distro='*', branch='*', system='*',
          build_workflows_repository=default_build_workflow_repository,
          gui=False, interactive=True, tmp_container=True, container_image=None,
          container_options=[], args_list=['-norc'], verbose=None,
          conf='dev'):
    '''
    Start a bash shell in the configured container with the given repository
    configuration.'''
    build_workflows = list(iter_build_workflow(build_workflows_repository, 
                                               distro=distro, 
                                               branch=branch, 
                                               system=system))
    if not build_workflows:
        print('Cannot find requested build workflow.',
              'You can list existing workflows using:\n'
              '    casa_distro list\n'
              'Or create new one using:\n'
              '    casa_distro create ...',
              file=sys.stderr)
        return 1
    
    if len(build_workflows) > 1:
        print('Several build workflows found, you must explicitely select one',
              'giving values for distro, system and branch. You can list',
              'existing workflows using:\n'
              'casa_distro -r %s list' 
              % build_workflows_repository, 
              file=sys.stderr)
        return 1
    if isinstance(container_options, six.string_types):
        container_options = container_options.split(' ')        
    distro, branch, system, bwf_dir = build_workflows[0]
    bwf_directory = osp.join(build_workflows_repository, '%s' % distro,
                             '%s_%s' % (branch, system))
    command = ['/bin/bash' ] + args_list
    run_container(bwf_directory, command=command, gui=gui, 
                  interactive=interactive, tmp_container=tmp_container,
                  container_image=container_image,
                  container_options=container_options, verbose=verbose,
                  conf=conf)


@command
def run(distro=None, branch=None, system=None,
        build_workflows_repository=default_build_workflow_repository,
        gui=True, interactive=False, tmp_container=True,
        container_image=None,container_options=[], args_list=[],
        verbose=None, conf='dev'):
    '''
    Start any command in the configured container (Docker or Singularity) with
    the given repository configuration.

    example:
        casa_distro -r /home/casa run branch=bug_fix ls -als /casa

    The "conf" parameter may address an additional config dictionary within the
    casa_distro.json config file. Typically, a test config may use a different
    system image (casa-test images), or options, or mounted directories.
    '''
    default_distro = default_branch = default_system = False
    if distro is None:
        default_distro = True
        distro = '*'
    if branch is None:
        default_branch = True
        branch = '*'
    if system is None:
        default_system = True
        system = '*'
    
    build_workflows = list(iter_build_workflow(build_workflows_repository, 
                                               distro=distro, 
                                               branch=branch, 
                                               system=system))
    if not build_workflows:
        print('Cannot find requested build workflow.',
              'You can list existing workflows using:\n'
              '    casa_distro list\n'
              'Or create new one using:\n'
              '    casa_distro create ...',
              file=sys.stderr)
        return 1
    
    if len(build_workflows) > 1:
        print('Several build workflows found, you must explicitely select one',
              'giving values for distro, system and branch. You can list '
              'existing workflows using:\n'
              '    casa_distro list\n'
              'You can run a command on all several workflows using:\n'
              '    casa_distro mrun ...',
              file=sys.stderr)
        return 1

    if isinstance(container_options, six.string_types):
        container_options = container_options.split(' ')
        
    status = {}
    global_failed = False

    d, b, s, bwf_dir = build_workflows[0]
    es = ExecutionStatus(start_time = time.localtime())
    status[(d, b, s)] = (es, bwf_dir)
    try:
        command = args_list
        bwf_directory = osp.join(build_workflows_repository, '%s' % d,
                                '%s_%s' % (b, s))
        run_container(bwf_directory, command=command, gui=gui, 
                    interactive=interactive, tmp_container=tmp_container,
                    container_image=container_image,
                    container_options=container_options, verbose=verbose,
                    conf=conf)
        es.stop_time = time.localtime()
        es.error_code = 0
        es.status = 'succeeded'
    
    except subprocess.CalledProcessError:
        global_failed = True
        es.stop_time = time.localtime()
        es.exception = traceback.format_exc()
        es.error_code = 1
        es.status = 'failed'
        
    except KeyboardInterrupt:
        global_failed = True
        es.stop_time = time.localtime()
        es.error_code = 1
        es.status = 'interrupted'

    display_summary(status)
    return global_failed


@command
def mrun(distro='*', branch='*', system='*',
         build_workflows_repository=default_build_workflow_repository,
         gui=True, interactive=False, tmp_container=True,
         container_image=None,container_options=[], args_list=[],
         verbose=None, conf='dev'):
    '''
    Start any command in one or several container with the given
    repository configuration. By default, command is executed in
    all existing build workflows.
    
    example:
        # Launch bv_maker on all build workflows using any version of Ubuntu
        casa_distro mrun bv_maker system=ubuntu-*

    The "conf" parameter may address an additional config dictionary within the
    casa_distro.json config file. Typically, a test config may use a different
    system image (casa-test images), or options, or mounted directories.
    '''
    build_workflows = list(iter_build_workflow(build_workflows_repository, 
                                               distro=distro, 
                                               branch=branch, 
                                               system=system))
    if not build_workflows:
        print('Cannot find requested build workflow.',
              'You can list existing workflows using:\n'
              '    casa_distro list\n'
              'Or create new one using:\n'
              '    casa_distro create ...',
              file=sys.stderr)
        return 1
    

    if isinstance(container_options, six.string_types):
        container_options = container_options.split(' ')
        
    status = {}
    global_failed = False

    for d, b, s, bwf_dir in build_workflows:
        es = ExecutionStatus(start_time = time.localtime())
        status[(d, b, s)] = (es, bwf_dir)
        try:
            command = args_list
            bwf_directory = osp.join(build_workflows_repository, '%s' % d,
                                    '%s_%s' % (b, s))
            run_container(bwf_directory, command=command, gui=gui, 
                        interactive=interactive, tmp_container=tmp_container,
                        container_image=container_image,
                        container_options=container_options, verbose=verbose,
                        conf=conf)
            es.stop_time = time.localtime()
            es.error_code = 0
            es.status = 'succeeded'
        
        except subprocess.CalledProcessError:
            global_failed = True
            es.stop_time = time.localtime()
            es.exception = traceback.format_exc()
            es.error_code = 1
            es.status = 'failed'
            
        except KeyboardInterrupt:
            global_failed = True
            es.stop_time = time.localtime()
            es.error_code = 1
            es.status = 'interrupted'
            break

    display_summary(status)
    return global_failed


@command
def bv_maker(distro='*', branch='*', system='*',
             build_workflows_repository=default_build_workflow_repository,
             gui=False, interactive=False, tmp_container=True, 
             container_image=None, container_options=[], args_list=[],
             verbose=None):
    '''
    Start bv_maker in the configured container for all the selected build
    workflows (by default, all created build workflows).
    
    This is a shortcut to "mrun bv_maker"
    '''    
    args_list = ['bv_maker' ] + args_list
    mrun(distro=distro, branch=branch, system=system,
          build_workflows_repository=build_workflows_repository, gui=gui,
          interactive=interactive, tmp_container=tmp_container,
          container_image=container_image,
          container_options=container_options, args_list=args_list,
          verbose=verbose)


@command
def create_writable_image(singularity_image=None, distro=None, branch=None, system=None,
             build_workflows_repository=default_build_workflow_repository,            
             verbose=None):
    '''
    Create a writable version of a Singularity image used to run containers.
    This allows to modify an image (for instance install custom packages). To
    use a writable image in a build workflow, it is necessary to edit its
    "casa_distro.json" file (located in the "conf" directory of the build
    workflow) to add ".writable" to the image name. For instance :
    
        "container_image": "cati/casa-dev:ubuntu-16.04.writable"

    The singularity image can be identified by its Docker-like name :
        casa_distro create_writable_image cati/casa-dev:ubuntu-16.04
    
    It is also possible to identify an image by selecting a build workflow:
        casa_distro create_writable_image distro=brainvisa branch=bug_fix

    Due to Singularity security, it is necessary to be root on the host 
    system to create an image (sudo is used for that and can ask you a password).
    
    '''
    if (distro or branch or system) and singularity_image:
        raise ValueError('Image selection must be done with either an image '
                        'name or a build workflow selection but not both')
    if not singularity_image:
        if not distro:
            distro = '*'
        if not branch:
            branch = '*'
        if not system:
            system = '*'
        build_workflows = list(iter_build_workflow(build_workflows_repository, 
                                                   distro=distro, 
                                                   branch=branch, 
                                                   system=system))
        if not build_workflows:
            print('Cannot find requested build workflow.',
                'You can list existing workflows using:\n'
                '    casa_distro list\n'
                'Or create new one using:\n'
                '    casa_distro create ...',
                file=sys.stderr)
            return 1
        
        if len(build_workflows) > 1:
            print('Several build workflows found, you must explicitely select one',
                'giving values for distro, system and branch. You can list '
                'existing workflows using:\n'
                '    casa_distro list',
                file=sys.stderr)
            return 1
        d, b, s, bwf_dir = build_workflows[0]
    else:
        bwf_dir = None
        
    create_writable_singularity_image(image=singularity_image, 
                                      build_workflow_directory=bwf_dir,
                                      build_workflows_repository=build_workflows_repository,
                                      verbose=None)

@command
def root_shell(singularity_image=None, distro=None, branch=None, system=None,
               build_workflows_repository=default_build_workflow_repository,            
               verbose=None):
    '''
    Start a shell with root privileges allowing to modify a writable
    singularity image. Before using this command, a writable image 
    must have been created with create_writable_image command. Using
    this command allow to modify the writable image (for instance install
    packages).
    Due to Singularity security, it is necessary to be
    root on the host system to start a root shell within the container (sudo 
    is used for that and can ask you a password).
    
    Image can be identified by its Docker-like name :
        casa_distro root_shell cati/casa-dev:ubuntu-16.04
    
    It is also possible to identify an image by selecting a build workflow:
        casa_distro root_shell distro=brainvisa branch=bug_fix
    '''
    if (distro or branch or system) and singularity_image:
        raise ValueError('Image selection must be done with either an image '
                         'name or a build workflow selection but not both')
    if not singularity_image:
        if not distro:
            distro = '*'
        if not branch:
            branch = '*'
        if not system:
            system = '*'
        build_workflows = list(iter_build_workflow(build_workflows_repository, 
                                                   distro=distro, 
                                                   branch=branch, 
                                                   system=system))
        if not build_workflows:
            print('Cannot find requested build workflow.',
                'You can list existing workflows using:\n'
                '    casa_distro list\n'
                'Or create new one using:\n'
                '    casa_distro create ...',
                file=sys.stderr)
            return 1
        
        if len(build_workflows) > 1:
            print('Several build workflows found, you must explicitely select one',
                'giving values for distro, system and branch. You can list '
                'existing workflows using:\n'
                '    casa_distro list',
                file=sys.stderr)
            return 1
        d, b, s, bwf_dir = build_workflows[0]
    else:
        bwf_dir = None
        
    singularity_root_shell(image=singularity_image, 
                           build_workflow_directory=bwf_dir,
                           build_workflows_repository=build_workflows_repository,
                           verbose=None)
