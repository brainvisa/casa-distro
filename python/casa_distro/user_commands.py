# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

import sys
import shutil
import glob
import os
import os.path as osp
import json

from casa_distro import six
from casa_distro.command import command, check_boolean
from casa_distro.defaults import default_download_url
from casa_distro.environment import (casa_distro_directory,
                                     iter_distros,
                                     iter_environments,
                                     run_container,
                                     select_environment,
                                     iter_images,
                                     update_container_image,
                                     delete_image,
                                     find_in_path,
                                     select_distro)
from casa_distro.log import verbose_file

if six.PY3:
    interactive_input = input
else:
    interactive_input = raw_input  # noqa F821


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
        s = '%.2f' % (size, )
        if s.endswith('.00'):
            s = s[:-3]
        elif s[-1] == '0':
            s = s[:-1]
        return s + unit + ' (' + str(full_size) + ')'
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
    for (d, b, s, iv), (es, bwf_dir) in six.iteritems(status):
        status = es.get_status_mapped()
        if status != '':
            message = '%s distro=%s branch=%s system=%s image_version=%s: %s' \
                % (status, d, b, s, iv, bwf_dir)
            start = es.start_time
            if start:
                if first_start is None:
                    first_start = start
                message += ', started: %04d/%02d/%02d %02d:%02d' \
                    % start[:5]
            stop = es.stop_time
            if stop:
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
                 error_code=None,
                 exception=None,
                 status='not run',
                 start_time=None,
                 stop_time=None):
        self.error_code = error_code
        self.exception = exception
        self.status = status
        self.start_time = start_time
        self.stop_time = stop_time

    def get_status_mapped(self):
        return self.status_map.get(self.status)


@command
def setup_user(distro=None,
               version=None,
               system=None,
               name='{distro}-{version}',
               container_type=None,
               writable=None,
               base_directory=casa_distro_directory(),
               image='{base_directory}/{distro}-{version}{extension}',
               url=default_download_url + '/releases/{container_type}',
               output='{base_directory}/{name}',
               # vm_memory='8192',
               # vm_disk_size='131072',
               force=False,
               verbose=True):
    """Create a new user environment
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
        version of the distro to use. By default the release with highest
        version is selected.
    system
        System to use inside this environment.
    name
        default={name_default}
        Name of the environment. No other environment must have the same name
        (including developer environments).
        This name may be used later to select the environment to run.
    container_type
        default={container_type_default}
        Type of virtual appliance to use. Either "singularity", "vbox" or
        "docker". If not given try to gues according to installed container
        software in the following order : Singularity, VirtualBox and Docker.
    writable
        size of a writable file system that can be used to make environement
        specific modification to the container file system. The size can be
        written in bytes as an integer, or in kilobytes with suffix "K", or in
        megabytes qith suffix "M", or in gygabytes with suffix "G". If size is
        not 0, this will create an overlay.img file in the base environment
        directory. This file will contain the any modification done to the
        container file system.
    {base_directory}
    image
        default={image_default}
        Location of the virtual image for this environement.
    url
        default={url_default}
        URL where to download image if it is not found.
    output
        default={output_default}
        Directory where the environement will be stored.
    force
        default=False
        force overwriting any existing matching environement. By default
        casa_distro will refuse to overwrite an existing one.
    {verbose}
    """
    verbose = verbose_file(verbose)
    force = check_boolean('force', force)

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
        raise NotImplementedError(
            'docker container type is not yet supported by this command')
    else:
        raise ValueError('Invalid container type: {0}'.format(container_type))
    if verbose:
        print('Container type:', container_type,
              file=verbose)

    if distro is None or version is None or system is None:
        selected = None
        for metadata_file in glob.glob(osp.join(base_directory,
                                                'run', '*.json')):
            metadata = json.load(open(metadata_file))
            if ((distro is None or distro == metadata['distro'])
                and (version is None or version == metadata['version'])
                    and (system is None or system == metadata['system'])):
                if selected:
                    raise ValueError(
                        'Several releases found. Please adjust, distro, '
                        'version and system to select only one')
                metadata['image'] = metadata_file[:metadata_file.rfind('.')]
                selected = metadata
        if selected is None:
            raise ValueError(
                'No release found. Please adjust, distro, version and system '
                'to select one')
        distro = selected['distro']
        version = selected['version']
        system = selected['version']
    else:
        selected = {
            'distro': distro,
            'system': system,
            'version': version,
            'container_type': container_type,
        }

    name = name.format(distro=distro,
                       version=version,
                       system=system)
    selected['name'] = name

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
    selected['image'] = image

    if verbose:
        print('image:', image,
              file=verbose)

    url = url.format(distro=distro,
                     version=version,
                     system=system,
                     base_directory=base_directory,
                     container_type=container_type,
                     extension=extension)
    if verbose:
        print('download image url:', url,
              file=verbose)

    update_container_image(container_type, image, url,
                           base_directory=base_directory,
                           new_only=True, verbose=verbose)

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
        raise ValueError(
            'Only Singularity supports writable file system overlay')

    if not osp.exists(output):
        os.makedirs(output)

    selected.setdefault('mounts', {})['/casa/setup'] = output
    selected['directory'] = output

    run_container(
        selected,
        command=[],
        gui=False,
        opengl='container',
        root=False,
        cwd='/casa/home',
        env=None,
        image=image,
        container_options=None,
        base_directory=base_directory,
        verbose=verbose)


@command
def setup_dev(distro='opensource',
              branch='master',
              system=None,
              image_version='1.0',
              name='{distro}-{branch}-{image_version}',
              container_type=None,
              writable=None,
              base_directory=casa_distro_directory(),
              image='{base_directory}/casa-dev-{image_version}{extension}',
              url=default_download_url + '/{container_type}',
              output='{base_directory}/{name}',
              # vm_memory='8192',
              # vm_disk_size='131072',
              force=False,
              verbose=True):
    """Create a new developer environment
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
        Name of the source branch to use for dev environments. Either
        "latest_release", "master" or "integration".
    system
        System to use with this environment. By default, it uses the first
        supported system of the selected distro.
    {image_version}
    name
        default={name_default}
        Name of the environment. No other environment must have the same name
        (including non developer environments).
        This name may be used later to select the environment to run.
    container_type
        default={container_type_default}
        Type of virtual appliance to use. Either "singularity", "vbox" or
        "docker". If not given try to gues according to installed container
        software in the following order : Singularity, VirtualBox and Docker.
    writable
        size of a writable file system that can be used to make environement
        specific modification to the container file system. The size can be
        written in bytes as an integer, or in kilobytes with suffix "K", or in
        megabytes qith suffix "M", or in gygabytes with suffix "G". If size is
        not 0, this will create an overlay.img file in the base environment
        directory. This file will contain the any modification done to the
        container file system.
    {base_directory}
    image
        default={image_default}
        Location of the virtual image for this environement.
    url
        default={url_default}
        URL where to download image if it is not found.
    output
        default={output_default}
        Directory where the environement will be stored.
    force
        default=False
        force overwriting any existing matching environement. By default
        casa_distro will refuse to overwrite an existing one.
    {verbose}
    """

    verbose = verbose_file(verbose)
    force = check_boolean('force', force)

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
        raise NotImplementedError(
            'docker container type is not yet supported by this command')
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
        print('Warning: the branch: {0} is not officially supported and may '
              'not exist'.format(branch), file=sys.stderr)
    if verbose:
        print('Branch:', branch,
              file=verbose)

    if system is None:
        system = distro['systems'][0]

    if system not in distro['systems']:
        # FIXME: make this a warning, but allow the user (developer) to proceed
        raise ValueError('The system {0} is not supported by the distro {1}. '
                         'Please select one of the following systems: {2}'
                         .format(system, distro['name'],
                                 ', '.join(distro['systems'])))
    if verbose:
        print('System:', system,
              file=verbose)

    name = name.format(distro=distro['name'],
                       branch=branch,
                       image_version=image_version)
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
                         image_version=image_version,
                         base_directory=base_directory,
                         container_type=container_type,
                         extension=extension)
    if verbose:
        print('image:', image,
              file=verbose)

    url = url.format(distro=distro['name'],
                     branch=branch,
                     system=system,
                     image_version=image_version,
                     base_directory=base_directory,
                     container_type=container_type,
                     extension=extension)
    if verbose:
        print('download image url:', url,
              file=verbose)

    output = output.format(distro=distro['name'],
                           branch=branch,
                           system=system,
                           image_version=image_version,
                           base_directory=base_directory,
                           name=name,
                           extension=extension)
    if verbose:
        print('output:', output,
              file=verbose)

    update_container_image(container_type, image, url,
                           base_directory=base_directory,
                           new_only=True, verbose=verbose)

    if writable and container_type != 'singularity':
        raise ValueError(
            'Only Singularity supports writable file system overlay')

    metadata = {
        'name': name,
        'type': 'dev',
        'distro': distro['name'],
        'branch': branch,
        'system': system,
        'image_version': image_version,
        'container_type': container_type,
        'image': image,
    }

    if not osp.exists(output):
        os.makedirs(output)

    metadata.setdefault('mounts', {})['/casa/setup'] = output
    metadata['directory'] = output

    options = []
    if branch:
        options.append('branch=%s' % branch)
    if distro['name']:
        options.append('distro=%s' % distro['name'])
    if system:
        options.append('system=%s' % system)
    if image_version:
        options.append('image_version=%s' % image_version)
    if name:
        options.append('name=%s' % name)

    run_container(
        metadata,
        command=options,
        gui=False,
        opengl='container',
        root=False,
        cwd='/casa/home',
        env=None,
        image=image,
        container_options=None,
        base_directory=base_directory,
        verbose=verbose)


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


# "list" cannot be used as a function name in Python. Therefore, the
# command name in the command-line is not the same as the corresponding
# Python function.
@command('list')
def list_command(type=None, distro=None, branch=None, system=None,
                 image_version=None, name=None,
                 base_directory=casa_distro_directory(),
                 json='no',
                 verbose=None):
    '''List run or dev environments created by "setup"/"setup_dev" command.

    Parameters
    ----------
    {type}
    {distro}
    {branch}
    {system}
    {image_version}
    {name}
    {base_directory}
    json
        default = {json_default}
        The output is written as a list of configuration dictionaries in
        JSON format.
    {verbose}

    '''
    json_output = check_boolean('json', json)
    # json parameter is hiding json module.
    # it is not possible to get back to a global
    # variable for json. Therefore, the json module is
    # stored in the local variable
    json = sys.modules['json']
    verbose = verbose_file(verbose)

    json_result = []
    for config in iter_environments(base_directory,
                                    type=type,
                                    distro=distro,
                                    branch=branch,
                                    system=system,
                                    image_version=image_version,
                                    name=name):
        if json_output:
            json_result.append(config)
        else:
            print(config['name'])
            for i in ('type', 'distro', 'branch', 'version', 'system',
                      'image_version', 'container_type', 'image'):
                v = config.get(i)
                if v is not None:
                    print('  %s:' % i, config[i])
            overlay = config.get('overlay')
            if overlay:
                print('  writable file system:', overlay)
                print('  writable file system size:',
                      size_to_string(config['overlay_size']))
            print('  directory:', config['directory'])

            if verbose:
                print('  full environment:')
                for line in json.dumps(config, indent=2,
                                       separators=(',', ': ')).split('\n'):
                    print('   ', line)
    if json_output:
        json.dump(json_result, sys.stdout)


@command
def run(type=None, distro=None, branch=None, system=None, image_version=None,
        version=None, name=None,
        base_directory=casa_distro_directory(),
        gui=True,
        opengl="auto",
        root=False,
        cwd=None,
        env=None,
        image=None,
        container_options=None,
        args_list=[],
        verbose=None):
    """
    Start any command in a selected run or dev environment

    example::

        casa_distro branch=master ls -als /casa

    Parameters
    ----------
    {type}
    {distro}
    {branch}
    {system}
    {image_version}
    {name}
    {version}
    {base_directory}
    {gui}
    {opengl}
    {root}
    {cwd}
    {env}
    {image}
    {container_options}
    {verbose}

    """
    verbose = verbose_file(verbose)
    gui = check_boolean('gui', gui)
    root = check_boolean('root', root)
    config = select_environment(base_directory,
                                type=type,
                                distro=distro,
                                branch=branch,
                                system=system,
                                image_version=image_version,
                                name=name,
                                version=version)
    if container_options:
        container_options = parse_list(container_options)
    if env:
        env_list = parse_list(env)
        try:
            env = dict(e.split('=') for e in env_list)
        except ValueError:
            raise ValueError('env syntax error. Should be in the shape '
                             '"VAR1=value1,VAR2=value2" etc.')
    command = args_list

    return run_container(config,
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


@command
def pull_image(distro=None, branch=None, system=None, image_version=None,
               version=None, name=None, type=None,
               image='*', base_directory=casa_distro_directory(),
               url=default_download_url,
               force=False, verbose=None):
    '''Update the container images. By default all images that are used by at
    least one environment are updated. There are two ways of selecting the
    image(s) to be downloaded:

    1. filtered by environment, using the ``name`` selector, or a combination
       of ``distro``, ``branch``, and ``system``.

    2. directly specifying a full image name, e.g.::

           casa_distro pull_image image=casa-run-ubuntu-18.04.sif

    Parameters
    ----------
    {distro}
    {branch}
    {system}
    {image_version}
    {version}
    {name}
    {base_directory}
    {image}
    url
        default={url_default}
        URL where to download image if it is not found.
    force
        default=False
        force re-download of images even if they are locally present and
        up-to-date.
    {verbose}

    '''
    verbose = verbose_file(verbose)
    images_to_update = list(iter_images(base_directory=base_directory,
                                        distro=distro, branch=branch,
                                        system=system,
                                        image_version=image_version,
                                        version=version,
                                        name=name, type=type,
                                        image=image))

    if not images_to_update and image not in (None, '') and '*' not in image:
        if image.endswith('.sif') or image.endswith('.simg'):
            container_type = 'singularity'
            images_to_update = [(container_type, image)]

    if verbose:
        print('images_to_update:\n%s'
              % '\n'.join(['%s\t: %s' % i for i in images_to_update]),
              file=verbose)

    for container_type, image in images_to_update:
        update_container_image(container_type, image,
                               base_directory=base_directory,
                               verbose=verbose, url=url, force=force)
    if not images_to_update:
        print('No build workflow match selection criteria',
              file=sys.stderr)
        return 1


@command
def list_images(distro=None, branch=None, system=None, image_version=None,
                version=None, name=None, type=None,
                image='*', base_directory=casa_distro_directory(),
                verbose=None):
    '''List the locally installed container images.
    There are two ways of selecting the image(s):

    1. filtered by environment, using the ``name`` selector, or a combination
       of ``distro``, ``branch``, and ``system``.

    2. directly specifying a full image name, e.g.::

           casa_distro list_image image=casa-run-ubuntu-18.04.sif

    Parameters
    ----------
    {distro}
    {branch}
    {system}
    {image_version}
    {version}
    {name}
    {type}
    {image}
    {base_directory}
    {verbose}

    '''
    images_to_update = list(iter_images(base_directory=base_directory,
                                        distro=distro, branch=branch,
                                        system=system,
                                        image_version=image_version,
                                        version=version,
                                        name=name, type=type,
                                        image=image))

    print('\n'.join(['%s\t: %s' % i for i in images_to_update]))


@command
def shell(type=None, distro=None, branch=None, system=None, image_version=None,
          name=None,
          version=None,
          base_directory=casa_distro_directory(),
          gui=True,
          opengl="auto",
          root=False,
          cwd=None,
          env=None, image=None,
          container_options=[],
          args_list=['-norc'],
          verbose=None):
    '''
    Start a bash shell in the configured container with the given pository
    configuration.

    Parameters
    ----------
    {type}
    {distro}
    {branch}
    {system}
    {image_version}
    {name}
    {version}
    {base_directory}
    {gui}
    {opengl}
    {root}
    {cwd}
    {env}
    {image}
    {container_options}
    {verbose}
    '''
    run(type=type, distro=distro, branch=branch, system=system,
        image_version=image_version,
        name=name,
        version=version,
        base_directory=base_directory,
        gui=gui,
        opengl=opengl,
        root=root,
        cwd=cwd,
        env=env,
        image=image,
        container_options=container_options,
        args_list=['/bin/bash'] + args_list,
        verbose=verbose)


@command
def mrun(type=None, distro=None, branch=None, system=None,
         image_version=None, name=None,
         version=None,
         base_directory=casa_distro_directory(),
         gui=True,
         opengl="auto",
         root=False,
         cwd=None,
         env=None,
         image=None,
         container_options=[],
         args_list=[],
         verbose=None):
    '''
    Start any command in one or several container with the given
    repository configuration. By default, command is executed in
    all existing build workflows.

    example::

        # Launch bv_maker on all build workflows using any version of Ubuntu
        casa_distro mrun bv_maker system=ubuntu-*

    Parameters
    ----------
    {type}
    {distro}
    {branch}
    {system}
    {image_version}
    {name}
    {version}
    {base_directory}
    {gui}
    {opengl}
    {root}
    {cwd}
    {env}
    {image}
    {container_options}
    {verbose}

    '''

    verbose = verbose_file(verbose)
    gui = check_boolean('gui', gui)
    root = check_boolean('root', root)
    if container_options:
        container_options = parse_list(container_options)
    if env:
        env_list = parse_list(env)
        try:
            env = dict(e.split('=') for e in env_list)
        except ValueError:
            raise ValueError('env syntax error. Should be in the shape '
                             '"VAR1=value1,VAR2=value2" etc.')
    command = args_list
    res = []

    for config in iter_environments(base_directory,
                                    type=type,
                                    distro=distro,
                                    branch=branch,
                                    system=system,
                                    image_version=image_version,
                                    name=name,
                                    version=version):

        res.append(run_container(config,
                                 command=command,
                                 gui=gui,
                                 opengl=opengl,
                                 root=root,
                                 cwd=cwd,
                                 env=env,
                                 image=image,
                                 container_options=container_options,
                                 base_directory=base_directory,
                                 verbose=verbose))

    if all(r == 0 for r in res):
        return 0
    else:
        sys.stderr.write('Exit codes: {0}\n'.format(res))
        return max(res)


@command
def bv_maker(type='dev', distro=None, branch=None, system=None,
             image_version=None, name=None,
             base_directory=casa_distro_directory(),
             env=None, image=None, container_options=[], args_list=[],
             verbose=None):
    '''
    Start a bv_maker in the configured container with the given repository
    configuration.

    Parameters
    ----------
    {type}
    {distro}
    {branch}
    {system}
    {image_version}
    {name}
    {base_directory}
    {env}
    {image}
    {container_options}
    {verbose}

    '''
    args_list = ['bv_maker'] + args_list
    return run(type=type, distro=distro, branch=branch, system=system,
               image_version=image_version,
               name=name,
               base_directory=base_directory,
               gui=False,
               opengl="container",
               env=env,
               image=image,
               container_options=container_options,
               args_list=args_list,
               verbose=verbose)


@command
def clean_images(distro=None, branch=None, system=None,
                 image_version=None, version=None, name=None, type=None,
                 image=None, verbose=False,
                 base_directory=casa_distro_directory(), interactive=True):
    '''
    Delete singularity images which are no longer used in any build workflow,
    or those listed in the "image" parameter.
    There are two ways of selecting the image(s):

    1. filtered by environment, using the ``name`` selector, or a combination
       of ``distro``, ``branch``, and ``system``.

    2. directly specifying a full image name, e.g.::

           casa_distro clean_images image=casa-run-ubuntu-18.04.sif

    Parameters
    ----------
    {distro}
    {branch}
    {system}
    {image_version}
    {version}
    {name}
    {type}
    {image}
    {base_directory}
    interactive
        default={interactive_default}
        ask confirmation before deleting an image
    {verbose}

    '''

    images_to_update = list(iter_images(base_directory=base_directory,
                                        distro=distro, branch=branch,
                                        system=system,
                                        image_version=image_version,
                                        version=version,
                                        name=name, type=type,
                                        image=image))

    print('\n'.join(['%s\t: %s' % i for i in images_to_update]))

    for container_type, image_name \
            in iter_images(base_directory=base_directory,
                           distro=distro, branch=branch,
                           system=system, image_version=image_version,
                           name=name, type=type,
                           image=image):
        if interactive:
            confirm = interactive_input(
                'delete image %s : %s [y/N]: ' % (container_type, image_name))
            if confirm not in ('y', 'yes', 'Y', 'YES'):
                print('skip.')
                continue
        print('deleting image %s' % image_name)
        delete_image(container_type, image_name)


@command
def delete(type=None, distro=None, branch=None, system=None,
           image_version=None, version=None, name=None,
           base_directory=casa_distro_directory(),
           interactive=True):
    """
    Delete an existing environment.

    The whole environment directory will be removed and forgotten.

    Use with care.

    Image files will be left untouched - use clean_images for this.

    Parameters
    ----------
    {type}
    {distro}
    {branch}
    {system}
    {image_version}
    {version}
    {name}
    {base_directory}
    interactive
        default={interactive_default}
        if true (or 1, or yes), ask confirmation interactively for each
        selected environement.
    """
    interactive = check_boolean('interactive', interactive)
    if not interactive and type is None and distro is None and system is None \
            and image_version is None and name is None:
        raise RuntimeError(
            'Refusing to delete all environments without confirmation. '
            'Either use interactive=True, or provide an explicit pattern for '
            'environment selection parameters')

    for config in iter_environments(base_directory,
                                    type=type,
                                    distro=distro,
                                    branch=branch,
                                    system=system,
                                    image_version=image_version,
                                    version=version,
                                    name=name):
        if interactive:
            confirm = interactive_input(
                'delete environment %s [y/N]: ' % config['name'])
            if confirm not in ('y', 'yes', 'Y', 'YES'):
                print('skip.')
                continue
        print('deleting environment %s' % config['name'])
        directory = config['directory']
        print('rm -rf "%s"' % directory)
        shutil.rmtree(directory)
