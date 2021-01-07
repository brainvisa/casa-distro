# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

import sys
import shutil

from casa_distro import six
from casa_distro.command import command, check_boolean
from casa_distro.defaults import default_download_url
from casa_distro.environment import (casa_distro_directory,
                                     setup_user as env_setup_user,
                                     setup_dev as env_setup_dev,
                                     iter_distros,
                                     iter_environments,
                                     run_container,
                                     select_environment,
                                     iter_images,
                                     update_container_image,
                                     delete_image)
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
def setup_user(dir='/casa/setup'):
    """
    Create all necessary directories and files to setup a user environement.
    This command is not supposed to be called directly but using a user image::

        mkdir ~/brainvisa
        singularity run --bind ~/brainvisa:/casa/setup brainvisa-5.0.sif

    Parameters
    ----------

    dir
        dir={dir_default}
        Target environment directory
    """
    env_setup_user(dir)


@command
def setup_dev(distro, branch=None, system=None, dir='/casa/setup', name=None):
    """
    Create all necessary directories and files to setup a developer *
    environement.
    This command is not supposed to be called directly but using a user image::

        mkdir ~/brainvisa
        singularity run -B \\
            ~/brainvisa:/casa/setup casa-dev-ubuntu-18.04.sif brainvisa master

    Parameters
    ----------

    {distro}
    {branch}
    {system}
    dir
        dir={dir_default}
        Target environment directory
    {name}
    """
    env_setup_dev(dir, distro, branch, system, name=name)


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
def list_command(type=None, distro=None, branch=None, system=None, name=None,
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
                                    name=name):
        if json_output:
            json_result.append(config)
        else:
            print(config['name'])
            for i in ('type', 'distro', 'branch', 'version', 'system',
                      'container_type', 'image'):
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
                for line in json.dumps(config, indent=2).split('\n'):
                    print('   ', line)
    if json_output:
        json.dump(json_result, sys.stdout)


@command
def run(type=None, distro=None, branch=None, system=None,
        name=None, version=None,
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
def pull_image(distro=None, branch=None, system=None, name=None, type=None,
               image='*', base_directory=casa_distro_directory(),
               url=default_download_url + '/{container_type}',
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
                                        system=system, name=name, type=type,
                                        image=image))

    if not images_to_update and image not in (None, '') and '*' not in image:
        if image.endswith('.sif') or image.endswith('.simg'):
            container_type = 'singularity'
            images_to_update = [(container_type, image)]

    if verbose:
        print('images_to_update:\n %s'
              % '\n'.join(['%s\t: %s' % i for i in images_to_update]),
              file=verbose)

    for container_type, image in images_to_update:
        update_container_image(container_type, image, verbose=verbose,
                               url=url, force=force)
    if not images_to_update:
        print('No build workflow match selection criteria',
              file=sys.stderr)
        return 1


@command
def list_images(distro=None, branch=None, system=None, name=None, type=None,
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
    {name}
    {type}
    {image}
    {base_directory}
    {verbose}

    '''
    images_to_update = list(iter_images(base_directory=base_directory,
                                        distro=distro, branch=branch,
                                        system=system, name=name, type=type,
                                        image=image))

    print('\n'.join(['%s\t: %s' % i for i in images_to_update]))


@command
def shell(type=None, distro=None, branch=None, system=None, name=None,
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
def mrun(type=None, distro=None, branch=None, system=None, name=None,
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
def bv_maker(type='dev', distro=None, branch=None, system=None, name=None,
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
    {name}
    {base_directory}
    {env}
    {image}
    {container_options}
    {verbose}

    '''
    args_list = ['bv_maker'] + args_list
    return run(type=type, distro=distro, branch=branch, system=system,
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
def clean_images(distro=None, branch=None, system=None, name=None, type=None,
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
                                        system=system, name=name, type=type,
                                        image=image))

    print('\n'.join(['%s\t: %s' % i for i in images_to_update]))

    for container_type, image_name \
            in iter_images(base_directory=base_directory,
                           distro=distro, branch=branch,
                           system=system, name=name, type=type,
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
def delete(type=None, distro=None, branch=None, system=None, name=None,
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
    {name}
    {base_directory}
    interactive
        default={interactive_default}
        if true (or 1, or yes), ask confirmation interactively for each
        selected environement.
    """
    interactive = check_boolean('interactive', interactive)
    if not interactive and type is None and distro is None and system is None \
            and name is None:
        raise RuntimeError(
            'Refusing to delete all environments without confirmation. '
            'Either use interactive=True, or provide an explicit pattern for '
            'environment selection parameters')

    for config in iter_environments(base_directory,
                                    type=type,
                                    distro=distro,
                                    branch=branch,
                                    system=system,
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
