# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

import argparse
from collections import OrderedDict
from functools import partial
import inspect
import os
import os.path as osp
import re
import sys

from casa_distro.defaults import publish_url
from casa_distro.info import __version__
from casa_distro.log import boolean_value
from casa_distro import six
from casa_distro.environment import casa_distro_directory


def check_boolean(name, value):
    result = boolean_value(value)
    if result is None:
        raise ValueError(
            'Invalid boolean value for {0}: {1}'.format(name, value))
    return result


commands = OrderedDict()


def command(f, name=None):
    if isinstance(f, six.string_types):
        return partial(command, name=f)

    global commands
    if name is None:
        name = f.__name__
    commands[name] = f
    return f


param_help = {
    'base_directory': '''base_directory
{indent}default={base_directory_default}

{indent}Directory where images and environments are stored. This parameter
{indent}can be passed on the commandline, or set via the
{indent}``CASA_BASE_DIRECTORY`` environment variable.''',
    'type': ''':ref:`type <env_type>`
{indent}default={type_default}

{indent}If given, select environment having the given type.''',
    'distro': ''':ref:`distro`
{indent}default={distro_default}

{indent}If given, select environment having the given distro name.''',
    'branch': ''':ref:`branch`
{indent}default={branch_default}

{indent}If given, select environment having the given branch.''',
    'system': ''':ref:`system`
{indent}default={system_default}

{indent}If given, select environments having the given system name.''',
    'name': ''':ref:`name <env_name>`
{indent}default={name_default}

{indent}If given, select environment by its name. It replaces type, distro,
{indent}branch and system and is shorter to select one.''',
    'gui': '''gui
{indent}default={gui_default}

{indent}If ``no``, ``false`` or ``0``, command is not using a graphical user
{indent}interface (GUI). Nothing is done to connect the container to a
{indent}graphical interface. This option may be necessary in context where
{indent}a graphical interface is not available.''',
    'opengl': '''opengl
{indent}default={opengl_default}

{indent}Setup different ways of trying to use OpenGL 3D rendering and GPU.
{indent}``auto``, ``container``, ``nv``, or ``software``.

{indent}* ``auto``: use a heuristic to choose the best option that is safe
{indent}  based on the host configuration
{indent}* ``container``: passes no special options to Singularity: the mesa
{indent}  installed in the container is used
{indent}* ``nv`` tries to mount the proprietary NVidia driver of the host (linux)
{indent}  system in the container
{indent}* ``software`` sets LD_LIBRARY_PATH to use a software-only OpenGL
{indent}  rendering. This solution is the slowest but is a fallback when no
{indent}  other solution works.''',  # noqa: E501
    'cwd': '''cwd
{indent}Set current working directory to the given value before launching
{indent}the command. By default, it is the same working directory as on the
{indent}host''',
    'env': '''env
{indent}Comma separated list of environment variables to pass to the command.
{indent}Each variable must have the form name=value.''',
    'image': ''':ref:`image`
{indent}Force usage of a specific virtual image instead of the one defined
{indent}in the environment configuration.''',
    'container_options': '''container_options
{indent}Comma separated list of options to add to the command line used to
{indent}call the container system.''',
    'verbose': '''verbose
{indent}default={verbose_default}

{indent}Print more detailed information if value is ``yes``, ``true`` or ``1``.''',  # noqa: E501
    'root': '''root
{indent}default={root_default}

{indent}If ``yes``, ``true`` or ``1``, start execution as system administrator. For
{indent}Singularity container, this requires administrator privileges on host
{indent}system.''',  # noqa: E501
    'version': '''version
{indent}If given, select environment by its version (only applicable to user
{indent}environments, not dev)''',
}


def text_formatted(text):
    ftext = text
    ftext = re.sub(':[^:]+:`([^`<]+)( *<.*>)?`', lambda m: m.group(1), ftext)
    ftext = re.sub('`([^`<]+)( *<.*>)?`_', lambda m: m.group(1), ftext)
    ftext = re.sub('.. ([^:]+):: *', lambda m: m.group(1) + ':', ftext)
    ftext = ftext.replace('``', '"')
    ftext = ftext.replace('`', "'")
    ftext = ftext.replace('.. ', '')
    ftext = ftext.replace('::', ':')
    return ftext


def formatted_help(text, format='text'):
    if format == 'text':
        return text_formatted(text)
    return text


def get_doc(command, indent='', format='text'):
    doc = inspect.getdoc(command) or ''

    cargs = inspect.getargspec(command)
    defaults = {i + '_default': j
                for i, j in zip(cargs.args[-len(cargs.defaults or ()):],
                                cargs.defaults or ())}

    executable = osp.basename(sys.argv[0])
    if format == 'rst':
        base_directory_default = ' ``$HOME/casa_distro``'
    else:
        base_directory_default = casa_distro_directory()
    help_vars = dict(executable=executable,
                     casa_version=__version__,
                     base_directory_default=base_directory_default,
                     publish_url=publish_url,
                     indent='    ')
    help_vars.update(defaults)
    help_vars['base_directory_default'] = base_directory_default
    r = re.compile('{([^}]+)}')
    keys = set()
    for text in param_help.values():
        keys.update(r.findall(text))
    help_vars.update({k: '' for k in keys if k not in help_vars})
    help_vars.update({k: v.format(**help_vars)
                      for k, v in param_help.items()})

    doc = doc.format(**help_vars)
    if indent:
        doc = '\n'.join(indent + line for line in doc.split('\n'))
    return formatted_help(doc, format=format)


# The 'file' parameter is not documented in the docstring because it is not
# meant to be used from the command-line.
@command
def help(command=None, format='text', full=False, file=None):
    """
    Print global help or help about a command.

    Parameters
    ----------
    format
        format help text in a given text format. Valid values are "text"
        (default) for raw text, or rst (RST/sphinx format).
    full
        if ``true`` or ``yes`` or ``1``, display each subcommand parameters
        documentation in the general help.
    """
    full = check_boolean('full', full)
    if file is None:
        file = sys.stdout
    indent = ''
    if format == 'text':
        indent = ' ' * 4

    if format == 'rst':
        base_directory_default = ' ``$HOME/casa_distro``'
    else:
        base_directory_default = casa_distro_directory()

    if command:
        command_help = get_doc(commands[command], indent=indent,
                               format=format)
        print('-' * len(command), file=file)
        print(command, file=file)
        print('-' * len(command), file=file)
        print(command_help, file=file)
    else:
        executable = osp.basename(sys.argv[0])

        help_vars = dict(executable=executable,
                         casa_version=__version__,
                         base_directory_default=base_directory_default,
                         indent='    ')
        r = re.compile('{([^}]+)}')
        keys = set()
        for text in param_help.values():
            keys.update(r.findall(text))
        help_vars.update({k: '' for k in keys if k not in help_vars})
        help_vars.update({k: v.format(**help_vars)
                          for k, v in param_help.items()})

        global_help = '''\
Casa_distro is the BrainVISA suite distribution swiss knife.
It allows to setup a virtual environment and launch BrainVISA software.
See http://brainivsa.info/casa-distro and
https://github.com/brainvisa/casa-distro for more information

Version : {casa_version}

usage::

    {executable} <general options> <command> [<command parameters>...]

general optional arguments:
    -v, --verbose   Display as much information as possible.
    --version       Display casa-distro version number and exit.
    -h, --help      Display help message and exit.
                    If used after command name, display only the help of this
                    command.

Common parameters:
==================
Most commands accept more or less the same parameters.

Many subcommands need :ref:`environment` selection specifications: :ref:`see the documentation on how to specify an environment <environment_options>`.

{base_directory}

Commands:
========='''.format(**help_vars)  # noqa: E501

        help_vars['indent'] = indent
        global_help = formatted_help(global_help, format=format)

        commands_summary = [global_help]
        for command in commands:
            command_doc = get_doc(commands[command], indent=indent * 2,
                                  format=format)
            if not full:
                # Split the docstring in two to remove parameters documentation
                # The docstring is supposed to follow the Numpy style docstring
                # see
                # https://numpydoc.readthedocs.io/en/latest/format.html#docstring-standard
                command_doc = re.split(
                    r'\s*parameters\s*-+\s*', command_doc, flags=re.I)[0]
            commands_summary.append('')
            commands_summary.append(indent + '-' * len(command))
            commands_summary.append(indent + command)
            commands_summary.append(indent + '-' * len(command))
            commands_summary.append(command_doc)
        print('\n'.join(commands_summary), file=file)


def main(meant_for_container=False):
    args_list = []
    if '--' in sys.argv:
        ind = sys.argv.index('--')
        args_list = sys.argv[ind + 1:]
        sys.argv = sys.argv[:ind]

    parser = argparse.ArgumentParser(add_help=False)

    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('--version', action='version',
                        version='casa-distro version: %s' % __version__)
    parser.add_argument('-h', '--help', action='store_true')
    parser.add_argument('command', nargs='?', choices=list(commands.keys()))
    parser.add_argument('command_options', nargs=argparse.REMAINDER)
    options = parser.parse_args()

    if options.help or not options.command:
        help()
        return

    result = None
    args = []
    kwargs = {}

    if isinstance(options.command, list):
        command_name = options.command[0]
    else:
        command_name = options.command
    command = commands[command_name]

    # Get command argument specification
    cargs = inspect.getargspec(command)

    if options.verbose and 'verbose' in cargs.args:
        kwargs['verbose'] = 'yes'

    allows_kwargs = True
    for i in options.command_options:
        lst = i.split('=', 1)
        if allows_kwargs and len(lst) == 2:
            kwargs[lst[0]] = lst[1]
        elif i == '--':
            allows_kwargs = False
        else:
            args.append(i)
    try:
        if not kwargs and args == ['-h'] or args == ['--help']:
            h = commands['help']
            result = h(command_name)
        else:
            if 'args_list' in cargs.args:
                kwargs['args_list'] = args + args_list
                args = []
            # ensure we are running on the right side of the container
            if (not meant_for_container and command_name != 'help'
                    and 'CASA_HOST_DIR' in os.environ):
                print('the "%s" command has been called from within a '
                      'casa-distro container. This is not the way it should '
                      'be used: it must be called from the host system.'
                      % osp.basename(sys.argv[0]), file=sys.stderr)
                sys.exit(1)
            result = command(*args, **kwargs)
    except (ValueError, TypeError, RuntimeError, NotImplementedError) as e:
        print('ERROR: {0} raised the following error:'.format(command_name),
              file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        print('\nUsage:', file=sys.stderr)
        help(command_name, file=sys.stderr)
        sys.stderr.flush()
        print('\nERROR SUMMARY (details above): {0}:'.format(e),
              file=sys.stderr)
        try:
            sys.exit(os.EX_USAGE)
        except AttributeError:
            # On Windows os.EX_USAGE is not defined
            sys.exit(1)
    sys.exit(result)
