# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function

import sys
import tempfile
import os
import os.path as osp
import time
import subprocess
import traceback
import json

from casa_distro import (environment,
                         six)
from casa_distro.command import command, check_boolean
from casa_distro.defaults import (default_build_workflow_repository,
                                  default_repository_server,
                                  default_repository_server_directory,
                                  default_repository_login,
                                  default_environment_type,
                                  default_distro,
                                  default_branch,
                                  default_download_url)
from casa_distro.environment import (casa_distro_directory,
                                     find_in_path,
                                     iter_distros,
                                     iter_environments,
                                     run_container,
                                     select_distro,
                                     select_environment)
from casa_distro.build_workflow import (merge_config,
                                        update_build_workflow,
                                        delete_build_workflow)
from casa_distro.log import verbose_file
from casa_distro.singularity import (create_writable_singularity_image,
                                     singularity_root_shell)
from casa_distro.web import url_listdir, urlopen

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


def parse_list(msg):
    """
    Parse a string containing a list of values separated by commas.
    Items can be quoted with simple or double quotes.
    Quotes and commas can be escaped by preceding them with a backslash.
    """
    out_msg = []
    sub_msg = []
    esc = False
    in_quote = None
    for c in msg:
        if esc:
            sub_msg.append(c)
            esc = False
        else:
            if c == '\\':
                esc = True
            elif in_quote and c == in_quote:
                in_quote = None
            elif in_quote:
                sub_msg.append(c)
            elif c in ('"', "'"):
                in_quote = c
            elif c == ',':
                m = ''.join(sub_msg).strip()
                if m != '':
                    out_msg.append(m)
                sub_msg = []
            else:
                sub_msg.append(c)
    if len(sub_msg) != 0:
        m = ''.join(sub_msg).strip()
        if m != '':
            out_msg.append(m)
    return out_msg


class ExecutionStatus(object):
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
def distro():
    """
    List all available distro and provide information for each one.
    """
    for distro in iter_distros():
        directory = distro['directory']
        print(distro['name'])
        if 'description' in distro:
            print('  Description:', distro['description'])
        if 'systems' in distro:
            print('  Supported systems:', ', '.join(distro['systems']))
        print('  Directory:', directory)


@command
def setup(type=default_environment_type,
          distro=default_distro,
          branch=default_branch,
          system=None,
          name='{distro}-{type}-{system}',
          container_type = None,
          base_directory=casa_distro_directory(),
          image = '{base_directory}/casa-{type}-{system}{extension}',
          url=default_download_url + '/{container_type}',
          output='{base_directory}/{name}',
          vm_memory='8192',
          vm_disk_size='131072',
          verbose=True,
          force=False):
    """
    Create a new run or dev environment

    Parameters
    ----------
    type
        default={type_default}
        Environment type to setup. Either "run" for users or "dev" for
        developers
    distro
        default={distro_default}
        Distro used to build this environment. This is typically "brainvisa",
        "opensource" or "cati_platform". Use "casa_distro distro" to list all
        currently available distro.
    branch
        default={branch_default}
        Name of the source branch to use for dev environments. Either "latest_release",
        "master" or "integration".
    system
        System to use with this environment. By default, it uses the first supported
        system of the selected distro.
    name
        default={name_default}
        Name of the environment (no other environment must have the same name).
    container_type
        default={container_type_default}
        Type of virtual appliance to use. Either "singularity", "vbox" or "docker".
        If not given try to gues according to installed container software in the
        following order : Singularity, VirtualBox and Docker.
    base_directory
        default={base_directory_default}
        Directory where images and environments are stored
    image
        default={image_default}
        Location of the virtual image for this environement.
    url
        default={url_default}
        URL where to download image if it is not found.
    output
        default={output_default}
        Directory where the environement will be stored.
    verbose
        default={verbose_default}
        Print more detailed information if value is "yes", "true" or "1".
    force
        default={force_default}
        Allow to perform setup with unsuported configuration.
    """
    verbose = verbose_file(verbose)
    force = check_boolean('force', force)
    
    if type not in ('run', 'dev'):
        raise ValueError('Invalid environment type: {0}'.format(type))
    if verbose:
        print('Type:', type,
              file=verbose)
    
    if not container_type:
        if find_in_path('singularity'):
            container_type = 'singularity'
        elif find_in_path('VBoxManage'):
            container_type = 'vbox'
        elif find_in_path('docker'):
            container_type = 'docker'
        else:
            raise ValueError('Cannot guess container_type according to '
                             'Singularity, VirtualBox or Docker command '
                             'research')

    if container_type == 'singularity':
        extension = '.sif'
    elif container_type == 'vbox':
        extension = '.vdi'
    elif container_type == 'docker':
        raise NotImplementedError('docker container type is not yet supported by this command')
    else:
        raise ValueError('Invalid container type: {0}'.format(container_type))
    if verbose:
        print('Container type:', container_type,
              file=verbose)

    distro = select_distro(distro)
    if verbose:
        print('Distro:', distro['name'],
              file=verbose)
        print('Distro directory:', distro['directory'],
              file=verbose)
    
    if branch not in ('latest_release', 'master', 'integration'):
        raise ValueError('Invalid branch : {0}'.format(branch))
    if verbose:
        print('Branch:', branch,
              file=verbose)

    if system is None:
        system = distro['systems'][0]
    
    if system not in distro['systems'] and not force:
        raise ValueError('The system {0} is not supported by the distro {1}. Use force=true or select one of the following systems: {2}'.format(system, distro['name'], ', '.join(distro['systems'])))
    if verbose:
        print('System:', system,
              file=verbose)
    
    name = name.format(type=type,
                       distro=distro['name'],
                       branch=branch,
                       system=system)
    if verbose:
        print('name:', name,
              file=verbose)
    
    if not osp.isdir(base_directory):
        raise ValueError('No such directory: {0}'.format(base_directory))
    if verbose:
        print('base directory:', base_directory,
              file=verbose)
    
    image = image.format(type=type,
                         distro=distro['name'],
                         branch=branch,
                         system=system,
                         base_directory=base_directory,
                         container_type=container_type,
                         extension=extension)
    if verbose:
        print('image:', image,
              file=verbose)

    url = url.format(type=type,
                     distro=distro['name'],
                     branch=branch,
                     system=system,
                     base_directory=base_directory,
                     container_type=container_type,
                     extension=extension)
    if verbose:
        print('download image url:', url,
              file=verbose)

    output = output.format(type=type,
                           distro=distro['name'],
                           branch=branch,
                           system=system,
                           base_directory=base_directory,
                           name=name,
                           extension=extension)
    if verbose:
        print('output:', output,
              file=verbose)

    metadata_file = image + '.json'
    image_file_name = osp.basename(image)
    if not osp.exists(image):
        if image_file_name not in url_listdir(url): 
            raise ValueError('File {image} does not exist and cannot be '
                             'downloaded from {url}/{image_file_name}'.format(
                                 image=image, 
                                 url=url, 
                                 image_file_name=image_file_name))
        metadata = json.loads(urlopen(url + '/%s.json' % image_file_name).read())
        json.dump(metadata, open(metadata_file, 'w'), indent=4)
        
        subprocess.check_call([
            'wget', 
            '{url}/{image_file_name}'.format(url=url,
                                             image_file_name=image_file_name),
            '-O', image])
    else:
        metadata = json.load(open(metadata_file))
        if 'size' in metadata and os.stat(image).st_size < metadata['size']:
            subprocess.check_call([
                'wget', '--continue',
                '{url}/{image_file_name}'.format(url=url, image_file_name=image_file_name),
                '-O', image])
    
    environment.setup(type=type,
          distro=distro,
          branch=branch,
          system=system,
          name=name,
          container_type=container_type,
          base_directory=base_directory,
          image=image,
          output=output,
          #vm_memory=vm_memory,
          #vm_disk_size=vm_disk_size,
          verbose=verbose,
          force=force)



# "list" cannot be used as a function name in Python. Therefore, the
# command name in the command-line is not the same as the corresponding
# Python function.
@command('list')
def list_command(type=None, distro=None, branch=None, system=None, 
                 base_directory=casa_distro_directory(),
                 verbose=None):
    '''
    List (eventually selected) run or dev environments created by "setup" command.

    Parameters
    ----------
    type
        If given, shows only environments having the given type.
    distro
        If given, shows only environments having the given distro name.
    branch
        If given, shows only environments having the given branch.
    system
        If given, shows only environments having the given system name.
    base_directory
        default={base_directory_default}
        Directory where images and environments are stored
    verbose
        default={verbose_default}
        Print more detailed information if value is "yes", "true" or "1".
    '''
    verbose = verbose_file(verbose)
    for config in iter_environments(base_directory,
                                    type=type,
                                    distro=distro,
                                    branch=branch,
                                    system=system):
        print(config['name'])
        for i in ('type', 'distro', 'branch', 'system', 'container_type'):
            print('  %s:' % i, config[i])
        print('  directory:', config['directory'])
        if verbose:
            print('  full environment:')
            for line in json.dumps(config, indent=2).split('\n'):
                print('   ', line)

@command
def run(type=None, distro=None, branch=None, system=None,
        base_directory=casa_distro_directory(),
        gui=True,
        cwd='/casa/host/home',
        env=None,
        image=None,
        container_options=None,
        args_list=[],
        verbose=None):
    """
    Start any command in a selected run or dev environment

    example:
        casa_distro -r /home/casa run branch=bug_fix ls -als /casa

    Parameters
    ----------
    type
        If given, select environment having the given type.
    distro
        If given, select environment having the given distro name.
    branch
        If given, select environment having the given branch.
    system
        If given, select environments having the given system name.
    base_directory
        default={base_directory_default}
        Directory where images and environments are stored
    gui
        default={gui_default}
        If "no", "false" or "0", command is not using a graphical user 
        interface (GUI). Nothing is done to connect the container to a 
        graphical interface. This option may be necessary in context where 
        a graphical interface is not available.
    cwd
        default={cwd_default}
        Set current working directory to the given value before launching
        the command.
    env
        Comma separated list of environment variables to pass to the command.
        Each variable must have the form name=value.
    image
        Force usage of a specific virtual image instead of the one defined
        in the environment configuration.
    container_options
        Comma separated list of options to add to the command line used to
        call the container system.
    verbose
        default={verbose_default}
        Print more detailed information if value is "yes", "true" or "1".
    """
    verbose = verbose_file(verbose)
    config = select_environment(base_directory,
                                type=type,
                                distro=distro,
                                branch=branch,
                                system=system)
    if container_options:
        container_options = parse_list(container_options)
    if env:
        env_list = parse_list(env)
        try:
            env = dict(e.split('=') for e in env_list)
        except:
            raise ValueError('env syntax error. Should be in the shape '
                             '"VAR1=value1,VAR2=value2" etc.')

    command = args_list
    run_container(config, 
                  command=command, 
                  gui=gui, 
                  cwd=cwd, 
                  env=env,
                  image=image,
                  container_options=container_options,
                  base_directory=base_directory,
                  verbose=verbose)

@command
def update(distro='*',
           branch='*',
           system='*',
           build_workflows_repository=default_build_workflow_repository,
           verbose=None, command=None):
    '''
    Update an existing build workflow directory. For now it only re-creates
    the run script in bin/casa_distro, pointing to the casa_distro command
    inside the build workflow sources tree if it is found there, or to the one
    used to actually perform the update if none is found in the sources. Using
    the ``command`` option allows to change this behavior.

    distro:
        Name of the distro that will be created. If omited, the name
        of the distro source (or distro source directory) is used.

    branch:
        bv_maker branch to use (latest_release, bug_fix or trunk)

    system:
        Name of the target system.

    command:
        casa_distro command actually called in the run script. May be either
        "host" (the calling command from the host system), "workflow" (use the
        sources from the build-workflow, the default), or a hard-coded path to
        the casa_distro command.
    '''
    images_to_update = {}
    #for d, b, s, bwf_dir in iter_build_workflow(build_workflows_repository,
                                                #distro=distro, branch=branch,
                                                #system=system):
        #update_build_workflow(bwf_dir, verbose=verbose, command=command)

@command
def update_image(distro='*', branch='*', system='*', 
         build_workflows_repository=default_build_workflow_repository,
         verbose=None):
    '''
    Update the container images of (eventually selected) build workflows
    created by "create" command.
    '''
    verbose = verbose_file(verbose)
    #images_to_update = {}
    #for d, b, s, bwf_dir in iter_build_workflow(build_workflows_repository,
                                                #distro=distro, branch=branch,
                                                #system=system):
        #casa_distro = json.load(open(osp.join(bwf_dir, 'conf',
                                              #'casa_distro.json')))
        #confs = set(['dev'])
        #confs.update(casa_distro.get('alt_configs', {}).keys())
        #for conf in confs:
            #wfconf = merge_config(casa_distro, conf)
            #images_to_update.setdefault(wfconf['container_type'], set()).add(
                #wfconf['container_image'].replace('.writable', ''))
        #if verbose:
            #print('images_to_update:', images_to_update,
                  #file=verbose)
    #if not images_to_update:
        #print('No build workflow match selection criteria', file=sys.stderr)
        #return 1
    #for container_type, container_images in six.iteritems(images_to_update):
        #for container_image in container_images:
            #update_container_image(build_workflows_repository,
                                   #container_type, container_image,
                                   #verbose=verbose) 


@command
def shell(distro='*', branch='*', system='*',
          build_workflows_repository=default_build_workflow_repository,
          gui=True, interactive=True, tmp_container=True, container_image=None,
          cwd=None, env=None, container_options=[], args_list=['-norc'],
          verbose=None,
          conf='dev'):
    '''
    Start a bash shell in the configured container with the given repository
    configuration.
    '''
    #build_workflows = list(iter_build_workflow(build_workflows_repository, 
                                               #distro=distro, 
                                               #branch=branch, 
                                               #system=system))
    #if not build_workflows:
        #print('Cannot find requested build workflow.',
              #'You can list existing workflows using:\n'
              #'    casa_distro list\n'
              #'Or create new one using:\n'
              #'    casa_distro create ...',
              #file=sys.stderr)
        #return 1
    
    #if len(build_workflows) > 1:
        #print('Several build workflows found, you must explicitely select one',
              #'giving values for distro, system and branch. You can list',
              #'existing workflows using:\n'
              #'casa_distro -r %s list' 
              #% build_workflows_repository, 
              #file=sys.stderr)
        #return 1

    #if isinstance(container_options, six.string_types) \
            #and len(container_options) != 0:
        #container_options = parse_string(container_options)
    #if isinstance(env, six.string_types) \
            #and len(env) != 0:
        #env_list = parse_string(env)
        #try:
            #env = dict(e.split('=') for e in env_list)
        #except:
            #raise ValueError('env syntax error. Should be in the shape '
                             #'"VAR1=value1 VAR2=value2" etc.')

    #distro, branch, system, bwf_dir = build_workflows[0]
    #bwf_directory = osp.join(build_workflows_repository, '%s' % distro,
                             #'%s_%s' % (branch, system))
    #command = ['/bin/bash' ] + args_list
    #run_container(bwf_directory, command=command, gui=gui, 
                  #interactive=interactive, tmp_container=tmp_container,
                  #container_image=container_image, cwd=cwd, env=env,
                  #container_options=container_options, verbose=verbose,
                  #conf=conf)




@command
def mrun(distro='*', branch='*', system='*',
         build_workflows_repository=default_build_workflow_repository,
         gui=True, interactive=False, tmp_container=True,
         container_image=None, cwd=None, env=None, container_options=[],
         args_list=[], verbose=None, conf='dev'):
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
    #build_workflows = list(iter_build_workflow(build_workflows_repository,
                                               #distro=distro, 
                                               #branch=branch, 
                                               #system=system))
    #if not build_workflows:
        #print('Cannot find requested build workflow.',
              #'You can list existing workflows using:\n'
              #'    casa_distro list\n'
              #'Or create new one using:\n'
              #'    casa_distro create ...',
              #file=sys.stderr)
        #return 1
    

    #if isinstance(container_options, six.string_types) \
            #and len(container_options) != 0:
        #container_options = parse_string(container_options)
    #if isinstance(env, six.string_types) \
            #and len(env) != 0:
        #env_list = parse_string(env)
        #try:
            #env = dict(e.split('=') for e in env_list)
        #except:
            #raise ValueError('env syntax error. Should be in the shape '
                             #'"VAR1=value1 VAR2=value2" etc.')

    #status = {}
    #global_failed = False

    #for d, b, s, bwf_dir in build_workflows:
        #es = ExecutionStatus(start_time = time.localtime())
        #status[(d, b, s)] = (es, bwf_dir)
        #try:
            #command = args_list
            #bwf_directory = osp.join(build_workflows_repository, '%s' % d,
                                    #'%s_%s' % (b, s))
            #run_container(bwf_directory, command=command, gui=gui, 
                        #interactive=interactive, tmp_container=tmp_container,
                        #container_image=container_image, cwd=cwd,
                        #env=env,
                        #container_options=container_options, verbose=verbose,
                        #conf=conf)
            #es.stop_time = time.localtime()
            #es.error_code = 0
            #es.status = 'succeeded'
        
        #except subprocess.CalledProcessError:
            #global_failed = True
            #es.stop_time = time.localtime()
            #es.exception = traceback.format_exc()
            #es.error_code = 1
            #es.status = 'failed'
            
        #except KeyboardInterrupt:
            #global_failed = True
            #es.stop_time = time.localtime()
            #es.error_code = 1
            #es.status = 'interrupted'
            #break

    #display_summary(status)
    #return global_failed


@command
def bv_maker(distro='*', branch='*', system='*',
             build_workflows_repository=default_build_workflow_repository,
             gui=False, interactive=False, tmp_container=True, 
             container_image=None, cwd=None, env=None, container_options=[],
             args_list=[], verbose=None):
    '''
    Start bv_maker in the configured container for all the selected build
    workflows (by default, all created build workflows).
    
    This is a shortcut to "mrun bv_maker"
    '''    
    args_list = ['bv_maker' ] + args_list
    mrun(distro=distro, branch=branch, system=system,
          build_workflows_repository=build_workflows_repository, gui=gui,
          interactive=interactive, tmp_container=tmp_container,
          container_image=container_image, cwd=cwd, env=env,
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
    workflow) to add ".writable" to the image name. For instance:
    
        "container_image": "cati/casa-dev:ubuntu-16.04.writable"

    The singularity image can be identified by its Docker-like name:
        casa_distro create_writable_image cati/casa-dev:ubuntu-16.04
    
    It is also possible to identify an image by selecting a build workflow:
        casa_distro create_writable_image distro=brainvisa branch=bug_fix

    Due to Singularity security, it is necessary to be root on the host 
    system to create an image (sudo is used for that and can ask you a password).
    
    '''
    if (distro or branch or system) and singularity_image:
        raise ValueError('Image selection must be done with either an image '
                        'name or a build workflow selection but not both')
    #if not singularity_image:
        #if not distro:
            #distro = '*'
        #if not branch:
            #branch = '*'
        #if not system:
            #system = '*'
        #build_workflows = list(iter_build_workflow(build_workflows_repository, 
                                                   #distro=distro, 
                                                   #branch=branch, 
                                                   #system=system))
        #if not build_workflows:
            #print('Cannot find requested build workflow.',
                #'You can list existing workflows using:\n'
                #'    casa_distro list\n'
                #'Or create new one using:\n'
                #'    casa_distro create ...',
                #file=sys.stderr)
            #return 1
        
        #if len(build_workflows) > 1:
            #print('Several build workflows found, you must explicitely select one',
                #'giving values for distro, system and branch. You can list '
                #'existing workflows using:\n'
                #'    casa_distro list',
                #file=sys.stderr)
            #return 1
        #d, b, s, bwf_dir = build_workflows[0]
    #else:
        #bwf_dir = None
        
    #create_writable_singularity_image(image=singularity_image, 
                                      #build_workflow_directory=bwf_dir,
                                      #build_workflows_repository=build_workflows_repository,
                                      #verbose=None)

@command
def root_shell(singularity_image=None, distro=None, branch=None, system=None,
               build_workflows_repository=default_build_workflow_repository,            
               verbose=None):
    '''
    Start a shell with root privileges allowing to modify a writable
    singularity image. Before using this command, a writable image 
    must have been created with the create_writable_image command. Using
    this command allows to modify the writable image (for instance to install
    packages).
    Due to Singularity security, it is necessary to be
    root on the host system to start a root shell within the container (sudo 
    is used for that and can ask you a password).
    
    The image can be identified by its Docker-like name:
        casa_distro root_shell cati/casa-dev:ubuntu-16.04
    
    It is also possible to identify an image by selecting a build workflow:
        casa_distro root_shell distro=brainvisa branch=bug_fix
    '''
    if (distro or branch or system) and singularity_image:
        raise ValueError('Image selection must be done with either an image '
                         'name or a build workflow selection but not both')
    #if not singularity_image:
        #if not distro:
            #distro = '*'
        #if not branch:
            #branch = '*'
        #if not system:
            #system = '*'
        #build_workflows = list(iter_build_workflow(build_workflows_repository, 
                                                   #distro=distro, 
                                                   #branch=branch, 
                                                   #system=system))
        #if not build_workflows:
            #print('Cannot find requested build workflow.',
                #'You can list existing workflows using:\n'
                #'    casa_distro list\n'
                #'Or create new one using:\n'
                #'    casa_distro create ...',
                #file=sys.stderr)
            #return 1
        
        #if len(build_workflows) > 1:
            #print('Several build workflows found, you must explicitely select one',
                #'giving values for distro, system and branch. You can list '
                #'existing workflows using:\n'
                #'    casa_distro list',
                #file=sys.stderr)
            #return 1
        #d, b, s, bwf_dir = build_workflows[0]
    #else:
        #bwf_dir = None
        
    #singularity_root_shell(image=singularity_image, 
                           #build_workflow_directory=bwf_dir,
                           #build_workflows_repository=build_workflows_repository,
                           #verbose=None)

@command
def delete(distro='*', branch='*', system='*',
        build_workflows_repository=default_build_workflow_repository,
        interactive=True):
    '''
    Delete (physically remove files) an entire build workflow.
    The container image will not be erased, see clean_images for that.

    example:
        casa_distro delete branch=bug_fix

    By default the "interactive" mode is on, and a confirmation will be asked before proceding. If interactive is disabled, then the deletion will be done without confirmation.
    '''
    #build_workflows = [bwf
                       #for bwf in iter_build_workflow(
                            #build_workflows_repository,
                            #distro=distro,
                            #branch=branch,
                            #system=system) if osp.exists(bwf[-1])]
    #print('the following build workflows will be permanently deleted:')
    #print('\n'.join([bwf[-1] for bwf in build_workflows]))

    #if len(build_workflows) != 0 and interactive:
        #print('delete build worflow(s) ? (y/[n]): ', end='')
        #sys.stdout.flush()
        #confirm = sys.stdin.readline()
        #if confirm.strip().lower() not in ('y', 'yes'):
            #print('abort.')
            #return 0

    #for d, b, s, bwf_directory in build_workflows:
        #delete_build_workflow(bwf_directory)

@command
def clean_images(build_workflows_repository=default_build_workflow_repository,
                 image_names='*', verbose=False, interactive=True):
    '''
    Delete singularity images which are no longer used in any build workflow,
    or those listed in image_names.
    '''
    images_to_keep = {}
    #for d, b, s, bwf_dir in iter_build_workflow(build_workflows_repository,
                                                #distro='*', branch='*',
                                                #system='*'):
        #casa_distro = json.load(open(osp.join(bwf_dir, 'conf',
                                              #'casa_distro.json')))
        #confs = set(['dev'])
        #confs.update(casa_distro.get('alt_configs', {}).keys())
        #for conf in confs:
            #wfconf = merge_config(casa_distro, conf)
            #images_to_keep.setdefault(wfconf['container_type'], set()).add(
                #wfconf['container_image'])

    #clean_singularity_images(build_workflows_repository, image_names,
                             #images_to_keep, verbose, interactive)


