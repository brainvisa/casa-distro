# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function

import argparse
import sys
import zipfile
import tempfile
import shutil
import os
import os.path as osp
import inspect
from collections import OrderedDict
import textwrap
import re
from functools import partial

from casa_distro.defaults import default_build_workflow_repository
from casa_distro.info import __version__
from casa_distro.log import boolean_value
from casa_distro import six

def check_boolean(name, value):
    result = boolean_value(value)
    if result is None:
        raise ValueError('Invalid boolean value for {0}: {1}'.format(name, value))
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

def get_doc(command, indent=''):
    paragraphs = []
    cargs = inspect.getargspec(command)
    defaults = dict((i + '_default', j) for i, j in zip(cargs.args[-len(cargs.defaults or ()):], cargs.defaults or ()))
    doc = command.__doc__.format(**defaults)
    
    
    lines = doc.split('\n')
    while lines and not lines[0].strip():
        lines = lines[1:]
    new_lines = []
    if lines:
        space_re = re.compile(r'^[ ]*')
        begining_spaces = space_re.match(lines[0]).group()
        for line in lines:
            if line.strip():
                if line.startswith(begining_spaces):
                    line = line[len(begining_spaces):]
                new_lines.append(indent + line)
            else:
                new_lines.append('\n')
    return '\n'.join(new_lines)


@command
def help(command=None):
    """
    Print global help or help about a command.
    """
    if command:
        command_help = get_doc(commands[command], indent=' '*4)
        print('-' * len(command))
        print(command)
        print('-' * len(command))
        print(command_help)
    else:
        executable=osp.basename(sys.argv[0])
        global_help = '''Casa_distro is the BrainVISA suite distribution swiss knife. 
It allows to setup a virtual environment and launch BrainVISA software. 
See http://brainivsa.info/casa-distro for more information

Version : {version}

usage: {executable} [-r REPOSITORY] [-v] [--version] <command> [<command parameters>...]

optional arguments:
    -r REPOSITORY, --repository REPOSITORY
                    Path of the directory containing virtual images and configured 
                    environments.
                    (default={default_repository}) This base directory
                    may also be specified via an environment variable:
                    CASA_DEFAULT_REPOSITORY
    -v, --verbose   Display as much information as possible.
    --version       Display casa-distro version number and exit.
    -h, --help      Display help message and exit.
                    If used after command name, display only the help of this
                    command.

Commands:
'''.format(executable=executable,
           version=__version__,
           default_repository=default_build_workflow_repository)
    
        commands_summary = [global_help]
        for command in commands:
            command_doc = get_doc(commands[command], indent=' ' * 8)
            # Split the docstring in two to remove parameters documentation
            # The docstring is supposed to follow the Numpy style docstring
            # see https://numpydoc.readthedocs.io/en/latest/format.html#docstring-standard
            command_doc = re.split('\s*parameters\s*-+\s*', command_doc, flags=re.I)[0]
            commands_summary.append('    ' + '-' * len(command))
            commands_summary.append('    ' + command)
            commands_summary.append('    ' + '-' * len(command))
            commands_summary.append(command_doc)
        print('\n'.join(commands_summary))


def main():
    args_list = []
    if '--' in sys.argv:
        ind = sys.argv.index('--')
        args_list = sys.argv[ind + 1:]
        sys.argv = sys.argv[:ind]

    parser = argparse.ArgumentParser(add_help=False)

    parser.add_argument('-r', '--repository', default=None)
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

    if options.repository:
        kwargs['build_workflows_repository'] = options.repository
        from casa_distro import defaults
        # change the global repository dir
        defaults.default_build_workflow_repository = options.repository
        
    if options.verbose and 'verbose' in cargs.args:
        kwargs['verbose'] = sys.stdout
        
    allows_kwargs = True
    for i in options.command_options:
        l = i.split('=', 1)
        if allows_kwargs and len(l) == 2:
            kwargs[l[0]] = l[1]
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
                args= []
            result = command(*args, **kwargs)
    except (ValueError, RuntimeError, NotImplementedError) as e:
        print('ERROR:', e)
        result = os.EX_USAGE
    sys.exit(result)

