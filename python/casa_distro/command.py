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

from casa_distro.info import __version__
from casa_distro.defaults import default_build_workflow_repository

commands = OrderedDict()
def command(f):
    global commands
    commands[f.__name__] = f
    return f

def get_doc(command, wrap_width=None):
    paragraphs = []
    current = []
    for line in command.__doc__.strip().split('\n'):
        line = line.strip()
        if line:
            current.append(line)
        else:
            paragraphs.append(' '.join(current))
            current = []
    if current:
        paragraphs.append(' '.join(current))
    if wrap_width:
        paragraphs = [(textwrap.fill(i, wrap_width) if i else i) for i in paragraphs]
    return '\n'.join(paragraphs)

@command
def help(args_list=['help'], **kwargs):
    '''print help about a command'''
    
    command_set = set(args_list)
    if 'command' in kwargs:
        command_set.add(kwargs['command'])
    
    if len(command_set) == 0:
        parser.print_help()
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
       
def main():
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

    args_list = []
    if '--' in sys.argv:
        ind = sys.argv.index('--')
        args_list = sys.argv[ind + 1:]
        sys.argv = sys.argv[:ind]

    parser = argparse.ArgumentParser(description='Casa distribution creation tool. Version %s' % __version__,
                                     formatter_class=ArgumentLineBreakFormatter)

    parser.add_argument('-r', '--repository', default=None,
                        help='Path of the directory containing build workflow (default=%s)' % default_build_workflow_repository)
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Display information during processing')
    parser.add_argument('command', nargs=1, choices=list(commands.keys()),
                        help='\n\n'.join('"%s": %s;\n\n' % (i, get_doc(commands[i])) for i in commands))
    parser.add_argument('command_options', nargs=argparse.REMAINDER,
                        help='command specific options (use help <command> to list these options).')
    options = parser.parse_args()

    tmp_share = None
    result = None
    try:
        # Manage share directory in Zip file distribution
        if not osp.exists(__file__) and osp.dirname(__file__).endswith('.zip'):
            tmp_share = tempfile.mkdtemp()
            with zipfile.ZipFile(osp.dirname(__file__)) as zip:
                for i in zip.namelist():
                    if i.startswith('share'):
                        zip.extract(i, tmp_share)
            import casa_distro
            casa_distro.share_directory = osp.join(tmp_share, 'share')

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
        
    finally:
        if tmp_share:
            shutil.rmtree(tmp_share)
    sys.exit(result)
