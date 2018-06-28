from __future__ import print_function

import argparse
import sys
import zipfile
import tempfile
import shutil
import os.path as osp
import inspect
from collections import OrderedDict
import textwrap
import re
from functools import partial

from casa_distro import six
from casa_distro.info import __version__
from casa_distro.defaults import default_build_workflow_repository

commands = OrderedDict()
def command(f, name=None):
    if isinstance(f, six.string_types):
        return partial(command, name=f)
    
    global commands
    if name is None:
        name = f.__name__
    commands[name] = f
    return f

def get_doc(command, wrap_width=None):
    paragraphs = []
    lines = command.__doc__.split('\n')
    while lines and not lines[0].strip():
        lines = lines[1:]
    if lines:
        space_re = re.compile(r'^[ ]*')
        base_indent = len(space_re.match(lines[0]).group())
        last_indent = base_indent
        current = []
        for line in lines:
            sline = line.strip()
            if sline:
                new_indent = len(space_re.match(line).group())
                if new_indent == last_indent:
                    current.append(line.strip())
                else:
                    paragraphs.append((last_indent-base_indent, ' '.join(current)))
                    current = [line.strip()]
                    last_indent = new_indent
            else:
                paragraphs.append((last_indent-base_indent, ' '.join(current)))
                paragraphs.append((0, ''))
                current = []
                last_indent = base_indent
        if current:
            paragraphs.append((last_indent-base_indent, ' '.join(current)))
        if wrap_width:
            lines = [(textwrap.fill(t, wrap_width, initial_indent=' '*i, subsequent_indent=' '*i) if t else t) for i, t in paragraphs]
        else:
            lines = [t for i, t in paragraphs]
    return '\n'.join(lines)

@command
def help(args_list=['help'], **kwargs):
    '''print help about a command'''
    
    command_set = set(args_list)
    if 'command' in kwargs:
        command_set.add(kwargs['command'])
    
    if len(command_set) == 0:
        get_main_parser().print_help()
        return
    
    for command in command_set:
        command_help = get_doc(commands[command], wrap_width=80)

        #print('{s:{c}^{n}}'.format(s=' %s ' % command, n=80, c='-'))
        print()
        print(command)
        print('-' * len(command))
        print(command_help)
        cargs = inspect.getargspec(commands[command])
        if cargs.args:
            print()
            print('options:')
            print()
#            print('---------------------------')
            for i, arg in enumerate(cargs.args):
                if cargs.defaults is not None and len(cargs.defaults) > i:
                    print(' ' * 3, arg, '(default=%s)' % cargs.defaults[i])
                else:
                    print(' ' * 3, arg)
        print()

def get_main_parser():
    class ArgumentLineBreakFormatter(argparse.HelpFormatter):
        def _split_lines(self, text, width):
            result = []
            lines = text.split('\n')
            for line in lines:
                if line:
                    result.extend(super(ArgumentLineBreakFormatter, self)._split_lines(line, width))
                else:
                    result.append('')
            return result

    parser = argparse.ArgumentParser(
        description='Casa distribution creation tool. Version %s'
        % __version__,
        formatter_class=ArgumentLineBreakFormatter)

    parser.add_argument('-r', '--repository', default=None,
                        help='Path of the directory containing build workflow (default=%s)' % default_build_workflow_repository)
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Display information during processing')
    parser.add_argument('--version', action='version',
                        version='casa-distro version: %s' % __version__,
                        help='Display casa-distro version number and exit')
    parser.add_argument('command', nargs=1, choices=list(commands.keys()),
                        help='\n\n'.join('%s\n%s' % ('%s\n%s\n%s' % ('='*len(i), i, '=' * len(i)), get_doc(commands[i])) for i in commands))
    parser.add_argument('command_options', nargs=argparse.REMAINDER,
                        help='command specific options (use help <command> to list these options).')
    return parser

def main():
    args_list = []
    if '--' in sys.argv:
        ind = sys.argv.index('--')
        args_list = sys.argv[ind + 1:]
        sys.argv = sys.argv[:ind]

    parser = get_main_parser()
    options = parser.parse_args()

    result = None
    args = []
    kwargs = {}
    
    command = commands[options.command[0]]
    
    # Get command argument specification
    cargs = inspect.getargspec(command)

    if options.repository:
        kwargs['build_workflows_repository'] = options.repository
        
    if options.verbose and 'verbose' in cargs.args:
        kwargs['verbose'] = sys.stdout
        
    for i in options.command_options:
        l = i.split('=', 1)
        if len(l) == 2:
            kwargs[l[0]] = l[1]
        else:
            args.append(i)
    
    if 'args_list' in cargs.args:
        kwargs['args_list'] = args + args_list
        args= []

    result = command(*args, **kwargs)
    sys.exit(result)
