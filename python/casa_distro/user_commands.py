# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function

import glob
import json
import os
import os.path as osp
import sys
import subprocess
import tempfile
import time
import traceback

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
                                     update_environment,
                                     run_container,
                                     select_distro,
                                     select_environment,
                                     iter_images,
                                     update_container_image)
from casa_distro.build_workflow import (merge_config,
                                        update_build_workflow,
                                        delete_build_workflow)
from casa_distro.log import verbose_file
from casa_distro.web import url_listdir, urlopen, wget_command


def size_to_string(full_size):
  size = full_size
  if size >= 1024:
    unit = 'K'
    size /= 1024.0
    if size >= 1024:
      unit = 'M'
      size /= 1024.0
      if size >= 1024:
        unit = 'G'
        size /= 1024.0
    s = '%.2f' % ( size, )
    if s.endswith( '.00' ): s = s[:-3]
    elif s[-1] == '0': s = s[:-1]
    return s + unit + ' (' + str( full_size ) + ')'
  else:
    return str(size)


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
def setup_dev(distro=None,
              branch=default_branch,
              system=None,
              name='{distro}-dev-{system}',
              container_type = None,
              writable=None,
              base_directory=casa_distro_directory(),
              image = '{base_directory}/casa-dev-{system}{extension}',
              url=default_download_url + '/{container_type}',
              output='{base_directory}/{name}',
              #vm_memory='8192',
              #vm_disk_size='131072',
              verbose=True):
    """
    Create a new developer environment

    Parameters
    ----------
    distro
        default={distro_default}
        Distro used to build this environment. This is typically "brainvisa",
        "opensource" or "cati_platform". Use "casa_distro distro" to list all
        currently available distro. Choosing a distro is mandatory to create a
        new environment. If the environment already exists, distro must be set
        only to reset configuration files to their default values.
    branch
        default={branch_default}
        Name of the source branch to use for dev environments. Either "latest_release",
        "master" or "integration".
    system
        System to use with this environment. By default, it uses the first supported
        system of the selected distro.
    name
        default={name_default}
        Name of the environment. No other environment must have the same name (including
        non developer environments).
        This name may be used later to select the environment to run.
    container_type
        default={container_type_default}
        Type of virtual appliance to use. Either "singularity", "vbox" or "docker".
        If not given try to gues according to installed container software in the
        following order : Singularity, VirtualBox and Docker.
    writable
        size of a writable file system that can be used to make environement specific
        modification to the container file system. The size can be written in bytes as
        an integer, or in kilobytes with suffix "K", or in megabytes qith suffix "M", 
        or in gygabytes with suffix "G". If size is not 0, this will create an
        overlay.img file in the base environment directory. This file will contain the
        any modification done to the container file system.
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
    """
    verbose = verbose_file(verbose)
    
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
    
    if system not in distro['systems']:
        raise ValueError('The system {0} is not supported by the distro {1}. Please select one of the following systems: {2}'.format(system, distro['name'], ', '.join(distro['systems'])))
    if verbose:
        print('System:', system,
              file=verbose)
    
    name = name.format(distro=distro['name'],
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
    
    image = image.format(distro=distro['name'],
                         branch=branch,
                         system=system,
                         base_directory=base_directory,
                         container_type=container_type,
                         extension=extension)
    if verbose:
        print('image:', image,
              file=verbose)

    url = url.format(distro=distro['name'],
                     branch=branch,
                     system=system,
                     base_directory=base_directory,
                     container_type=container_type,
                     extension=extension)
    if verbose:
        print('download image url:', url,
              file=verbose)

    output = output.format(distro=distro['name'],
                           branch=branch,
                           system=system,
                           base_directory=base_directory,
                           name=name,
                           extension=extension)
    if verbose:
        print('output:', output,
              file=verbose)

    metadata_file = image + '.json'
    update_container_image(container_type, image, url, new_only=True)

    if writable and container_type != 'singularity':
        raise ValueError('Only Singularity supports writable file system overlay')
    
    
    metadata = {
        'name': name,
        'type': 'dev',
        'distro': distro['name'],
        'branch': branch,
        'system': system,
        'container_type': container_type,
        'image': image,
    }
        
    environment.setup_dev(metadata=metadata,
                          distro=distro,
                          writable=writable,
                          base_directory=base_directory,
                          output=output,
                          verbose=verbose)



@command
def setup(distro=None,
          version=None,
          system=None,
          name='{distro}-{version}',
          container_type = None,
          writable=None,
          base_directory=casa_distro_directory(),
          image = '{base_directory}/{distro}-{version}{extension}',
          url=default_download_url + '/release/{container_type}',
          output='{base_directory}/{name}',
          #vm_memory='8192',
          #vm_disk_size='131072',
          verbose=True):
    """
    Create a new user environment

    Parameters
    ----------
    distro
        default={distro_default}
        Distro used to build this environment. This is typically "brainvisa",
        "opensource" or "cati_platform". Use "casa_distro distro" to list all
        currently available distro. Choosing a distro is mandatory to create a
        new environment. If the environment already exists, distro must be set
        only to reset configuration files to their default values.
    version
        version of the distro to use. By default the release with highest version
        is selected.
    system
        System to use inside this environment.
    name
        default={name_default}
        Name of the environment. No other environment must have the same name (including
        developer environments).
        This name may be used later to select the environment to run.
    container_type
        default={container_type_default}
        Type of virtual appliance to use. Either "singularity", "vbox" or "docker".
        If not given try to gues according to installed container software in the
        following order : Singularity, VirtualBox and Docker.
    writable
        size of a writable file system that can be used to make environement specific
        modification to the container file system. The size can be written in bytes as
        an integer, or in kilobytes with suffix "K", or in megabytes qith suffix "M", 
        or in gygabytes with suffix "G". If size is not 0, this will create an
        overlay.img file in the base environment directory. This file will contain the
        any modification done to the container file system.
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
    """
    verbose = verbose_file(verbose)
    
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

    if distro is None or version is None or system is None:
        selected = None
        for metadata_file in glob.glob(osp.join(base_directory, 'run', '*.json')):
            metadata = json.load(open(metadata_file))
            if ((distro is None or distro == metadata['distro']) and
                (version is None or version == metadata['version']) and
                (system is None or system == metadata['system'])):
                if selected:
                    raise ValueError('Several releases found. Please adjust, distro, version and system to select only one')
                metadata['image'] = metadata_file[:metadata_file.rfind('.')]
                selected = metadata
        if selected is None:
            raise ValueError('No release found. Please adjust, distro, version and system to select one')
        distro = selected['distro']
        version = selected['version']
        system = selected['version']
    name = name.format(distro=distro,
                       version=version,
                       system=system)
    if verbose:
        print('name:', name,
              file=verbose)
    
    if not osp.isdir(base_directory):
        raise ValueError('No such directory: {0}'.format(base_directory))
    if verbose:
        print('base directory:', base_directory,
              file=verbose)
    
    image = image.format(distro=distro,
                         version=version,
                         system=system,
                         base_directory=base_directory,
                         container_type=container_type,
                         extension=extension)
    if verbose:
        print('image:', image,
              file=verbose)

    #url = url.format(distro=distro,
                     #version=version,
                     #system=system,
                     #base_directory=base_directory,
                     #container_type=container_type,
                     #extension=extension)
    #if verbose:
        #print('download image url:', url,
              #file=verbose)

    output = output.format(distro=distro,
                           version=version,
                           system=system,
                           base_directory=base_directory,
                           name=name,
                           extension=extension)
    if verbose:
        print('output:', output,
              file=verbose)
    
    if writable and container_type != 'singularity':
        raise ValueError('Only Singularity supports writable file system overlay')
    
    environment.setup(selected,
          writable=writable,
          base_directory=base_directory,
          output=output,
          verbose=verbose)



# "list" cannot be used as a function name in Python. Therefore, the
# command name in the command-line is not the same as the corresponding
# Python function.
@command('list')
def list_command(type=None, distro=None, branch=None, system=None, name=None,
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
    name
        If given, select environment by its name. It replaces type, distro,
        branch and system and is shorter to select one.
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
                                    system=system,
                                    name=name):
        print(config['name'])
        for i in ('type', 'distro', 'branch', 'version', 'system', 'container_type', 'image'):
            v = config.get(i)
            if v is not None:
                print('  %s:' % i, config[i])
        overlay = config.get('overlay')
        if overlay:
            print('  writable file system:', overlay)
            print('  writable file system size:', size_to_string(config['overlay_size']))
        print('  directory:', config['directory'])
            
        if verbose:
            print('  full environment:')
            for line in json.dumps(config, indent=2).split('\n'):
                print('   ', line)

@command
def run(type=None, distro=None, branch=None, system=None,
        name=None,
        base_directory=casa_distro_directory(),
        gui=True,
        root=False,
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
    name
        If given, select environment by its name. It replaces type, distro,
        branch and system and is shorter to select one.
    base_directory
        default={base_directory_default}
        Directory where images and environments are stored
    gui
        default={gui_default}
        If "no", "false" or "0", command is not using a graphical user 
        interface (GUI). Nothing is done to connect the container to a 
        graphical interface. This option may be necessary in context where 
        a graphical interface is not available.
    root
        default={root_default}
        If "yes", "true" or "1", start execution as system administrator. For 
        Singularity container, this requires administrator privileges on host
        system.
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
    gui = check_boolean('gui', gui)
    root = check_boolean('root', root)
    config = select_environment(base_directory,
                                type=type,
                                distro=distro,
                                branch=branch,
                                system=system,
                                name=name)
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
                  root=root,
                  cwd=cwd, 
                  env=env,
                  image=image,
                  container_options=container_options,
                  base_directory=base_directory,
                  verbose=verbose)

@command
def update(type=None, distro=None, branch=None, system=None, name=None,
        base_directory=casa_distro_directory(),
        writable=None,
        verbose=None):
    """
    Update an existing environment.

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
    writable
        size of a writable file system that can be used to make environement specific
        modification to the container file system. The size can be written in bytes as
        an integer, or in kilobytes with suffix "K", or in megabytes qith suffix "M", 
        or in gygabytes with suffix "G". If size is not 0, this will create or resize an
        overlay.img file in the base environment directory. This file will contain the
        any modification done to the container file system. If size is 0, the overlay.img
        file is deleted and all its content is lost.
    verbose
        default={verbose_default}
        Print more detailed information if value is "yes", "true" or "1".
    """
    verbose = verbose_file(verbose)
    config = select_environment(base_directory,
                                type=type,
                                distro=distro,
                                branch=branch,
                                system=system,
                                name=name)

    update_environment(config, 
                       base_directory=base_directory,
                       writable=writable,
                       verbose=verbose)

@command
def pull_image(distro=None, branch=None, system=None, name=None, type=None,
               image='*', base_directory=casa_distro_directory(),
               url=default_download_url + '/{container_type}',
               force=False, verbose=None):
    '''
    Update the container images, possibly filtered by environments
    created by "setup_dev" command.

    Parameters
    ----------
    distro
        default=None
        Distro used to build this environment. This is typically "brainvisa",
        "opensource" or "cati_platform". Use "casa_distro distro" to list all
        currently available distro. Choosing a distro is mandatory to create a
        new environment. If the environment already exists, distro must be set
        only to reset configuration files to their default values.
    branch
        default=None
        Name of the source branch to use for dev environments. Either "latest_release",
        "master" or "integration".
    system
        default=None
        System to use with this environment. By default, it uses the first supported
        system of the selected distro.
    name
        default=None
        Name of the environment. No other environment must have the same name (including
        non developer environments).
        This name may be used later to select the environment to run.
    base_directory
        default={base_directory_default}
        Directory where images and environments are stored
    image
        default="*"
        Location of the virtual image for this environement.
    url
        default={url_default}
        URL where to download image if it is not found.
    force
        default=False
        force re-download of images even if they are locally present and up-to-date.
    verbose
        default={verbose_default}
        Print more detailed information if value is "yes", "true" or "1".
     '''
    verbose = verbose_file(verbose)
    images_to_update = list(iter_images(base_directory=base_directory,
                                        distro=distro, branch=branch,
                                        system=system, name=name, type=type,
                                        image=image))

    if not images_to_update and image not in (None, '') and '*' not in image:
        if image.endswith('.sif') or image.endswith('.simg'):
            image_url = url + '/' + image
            container_type = 'singularity'
            images_to_update = [container_type, image_url]

    if verbose:
        print('images_to_update:\n %s'
              % '\n'.join(['%s\t: %s' % i for i in images_to_update]),
              file=verbose)

    for container_type, image in images_to_update:
        update_container_image(container_type, image, verbose=verbose,
                               url=url, force=force)
    else:
        print('No build workflow match selection criteria',
              file=sys.stderr)
        return 1


@command
def list_images(distro=None, branch=None, system=None, name=None, type=None,
                image='*', base_directory=casa_distro_directory(),
                verbose=None):
    images_to_update = list(iter_images(base_directory=base_directory,
                                        distro=distro, branch=branch,
                                        system=system, name=name, type=type,
                                        image=image))

    print('\n'.join(['%s\t: %s' % i for i in images_to_update]))


@command
def shell(type=None, distro=None, branch=None, system=None, name=None,
          base_directory=casa_distro_directory(),
          gui=True, cwd=None,
          env=None, image=None, container_options=[], args_list=['-norc'],
          verbose=None):
    '''
    Start a bash shell in the configured container with the given repository
    configuration.
    '''
    run(type=type, distro=distro, branch=branch, system=system,
        name=name,
        base_directory=base_directory,
        gui=gui,
        cwd=cwd,
        env=env,
        image=image,
        container_options=container_options,
        args_list=['/bin/bash'] + args_list,
        verbose=verbose)



@command
def mrun(distro='*', branch='*', system='*', name=None,
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
def bv_maker(type=None, distro=None, branch=None, system=None, name=None,
             base_directory=casa_distro_directory(),
             gui=False, cwd=None,
             env=None, image=None, container_options=[], args_list=[],
             verbose=None):
    '''
    Start a bv_maker in the configured container with the given repository
    configuration.
    '''
    args_list = ['bv_maker' ] + args_list
    run(type=type, distro=distro, branch=branch, system=system,
        name=name,
        base_directory=base_directory,
        gui=gui,
        cwd=cwd,
        env=env,
        image=image,
        container_options=container_options,
        args_list=args_list,
        verbose=verbose)



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


