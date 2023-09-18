# -*- coding: utf-8 -*-
from __future__ import print_function

import glob
import os
import os.path as osp
import sys

from casa_distro import six
from casa_distro.command import command, check_boolean
from casa_distro.defaults import default_download_url
from casa_distro.environment import (casa_distro_directory,
                                     iter_distros,
                                     iter_environments,
                                     run_container,
                                     select_environment,
                                     update_image,
                                     find_image_update_url)
from casa_distro.log import verbose_file


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
def distro():
    """
    List all available distro and provide information for each one.
    """
    for distro in iter_distros():
        directory = distro['directory']
        print(distro['name'])
        if 'description' in distro:
            print('  Description:', distro['description'])
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
    json = sys.modules['json']
    verbose = verbose_file(verbose)

    # json parameter is hiding json module.
    # it is not possible to get back to a global
    # variable for json. Therefore, the json module is
    # stored in the local variable
    import json

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
               image=None, base_directory=casa_distro_directory(),
               url=default_download_url,
               mode='standard', cleanup='yes', verbose=None):
    '''Update the container images. By default the current image and
    all images that are used by at least one casa-distro environment
    are selected (these environments are listed by the ``list`` command).
    There are two ways of selecting the image(s) to be updated:

    1. filtered by environment, using the ``name`` selector, or a combination
       of ``distro``, ``branch``, and ``image_version``.

           casa_distro pull_image type=dev image_version=5.0

    2. directly specifying an image file name

           casa_distro pull_image image=/home/me/casa-run-5.0.sif

    Then the command look for an updated version of selected images in the
    site given by ``url`` parameter. These files are downloaded (as well as
    the corresponding JSON metadata file) and the config files using the
    current images are modified to use the updated ones. Finally, the original
    images are deleted (unless ``cleanup=no`` is used).

    Updated images are located using file name pattern. An updatable image
    file name must match the following pattern:

        ``{{name}}-{{version}}[-{{patch}}].{{extension}}``

    Where:

        ``{{name}}`` is the name of the image (e.g ``casa-dev``)
        ``{{version}}`` is the image version with pattern x.y[.z]
        ``{{patch}}`` is an integer
        ``{{version}}`` is the file name extension (e.g. ``sif``)

    An updated version of a given image is any other image with the same
    pattern having the same ``name``, ``version`` and ``extension`` and a
    higher ``patch``. If several updated version are available for an image,
    the one with the greatest ``patch`` is selected.

    Parameters
    ----------
    {distro}
    {branch}
    {system}
    {type}
    {image_version}
    {version}
    {name}
    {base_directory}
    {image}
    url
        default={url_default}
        URL where to download images.
    mode
        default={mode_default}
        Possible values are:
            - standard: download only newer version of existing image
            - force: re-download of images even if they are locally present
              and up-to-date.
            - fake: don't change anything to images. Just display what images
              and config files would be modified by other modes.
    cleanup
        default={cleanup_default}
        if true (or 1, or yes), remove current image when successfully finished
        to download new one.
    {verbose}
    '''
    mode = mode.lower()
    if mode == 'fake':
        verbose = 'yes'
    elif mode == 'force':
        raise NotImplementedError('mode=force is not implemented yet')
    verbose = verbose_file(verbose)

    to_update = {}
    if image:
        full_image = image
        if not osp.isabs(full_image):
            full_image = osp.normpath(osp.join(os.getcwd(), image))
        to_update[full_image] = []
    for environment in iter_environments(base_directory,
                                         distro=distro,
                                         branch=branch,
                                         system=system,
                                         type=type,
                                         image_version=image_version,
                                         version=version,
                                         name=name):
        compatible_run_images = []
        full_image = environment['image']
        if not osp.isabs(full_image):
            full_image = osp.normpath(osp.join(
                environment.get('directory', os.getcwd()), full_image))
        if image:
            if image == environment['image']:
                to_update[full_image].append(environment)
        else:
            # don't look for a run image associated with a user image
            # (especially because they don't have an image_version and
            # this inroduces ambiguities)
            if environment.get('type') != 'user':
                env_image = full_image
                to_update.setdefault(env_image, []).append(environment)

                # Check for update of run image associated with environment
                _, extension = osp.splitext(env_image)
                g = ('{}/'
                     'casa-run-{}*{}').format(
                        osp.dirname(env_image),
                        environment.get("image_version", ""),
                        extension)  # noqa: E261,E128
                for run_image in glob.glob(g):
                    if osp.exists(run_image):
                        compatible_run_images.append(run_image)
        if len(compatible_run_images) == 1:
            to_update[compatible_run_images[0]] = []
        elif len(compatible_run_images) > 1:
            raise RuntimeError(('{} run images are compatible with {}, '
                'cannot select which one to update: {}').format(  # noqa: E127,E128,E501
                    len(compatible_run_images),
                    env_image,
                    ', '.join(compatible_run_images)
            ))
    # Find updated version of images
    updates = {}
    up_to_date = set()
    for image in to_update:
        update_url, uptodate = find_image_update_url(image, url)
        if update_url:
            if not uptodate:
                updates[image] = update_url
            else:
                up_to_date.add(update_url)

    if verbose:
        for image, environments in to_update.items():
            update_url = updates.get(image)
            if update_url:
                if update_url not in up_to_date:
                    print(full_image, '<-', update_url, file=verbose)
                else:
                    print(full_image, '==', update_url, '[done]',
                          file=verbose)
                for e in environments:
                    print('  ->', '{}/conf/casa_distro.json'.format(
                        e["directory"]), file=verbose)
            else:
                print(image, '==', file=verbose)
    if mode != 'fake':
        for image, environments in to_update.items():
            update_url = updates.get(image)
            if update_url:
                if update_url not in up_to_date:
                    up_to_date.add(update_url)
                    do_update = True
                else:
                    do_update = False
                config_files = ['{}/conf/casa_distro.json'.format(
                    e["directory"]) for e in environments]
                rel_images = [e.get('image') for e in environments]
                update_image(image, update_url, config_files,
                             do_update=do_update, rel_images=rel_images)


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
