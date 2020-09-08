# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function

import os
import os.path as osp
import subprocess
import json
import tempfile
import shutil
import fnmatch
from subprocess import check_call, check_output
import glob
import sys

from casa_distro import six
from casa_distro.hash import file_hash, check_hash
from casa_distro.defaults import default_download_url
from casa_distro.log import verbose_file
from . import downloader


class RecipeBuilder:
    '''
    Class to interact with an existing VirtualBox machine.
    This machine is suposed to be based on a casa_distro system image.
    '''
    def __init__(self, name):
        self.name = name
        self.tmp_dir = None
        self.user = None
        self.sections = {}
        
    def run_user(self, command):
        '''
        Run a shell command in VM as self.user
        '''
        self.sections.setdefault('post', []).append(command)

    def run_root(self, command):
        '''
        Run a shell command in VM as root
        '''
        self.sections.setdefault('post', []).append(command)


    def copy_root(self, source_file, dest_dir):
        '''
        Copy a file in VM as root
        '''
        self.sections.setdefault('files', []).append('%s %s' % (source_file, dest_dir + '/' + osp.basename(source_file)))

    def copy_user(self, source_file, dest_dir):
        '''
        Copy a file in VM as self.user
        '''
        self.sections.setdefault('files', []).append('%s %s' % (source_file, dest_dir + '/' + osp.basename(source_file)))
    
    def write(self, file):
        for section, lines in self.sections.items():
            print('\n%%%s' % section, file=file)
            for line in lines:
                print('   ', line, file=file)
        file.flush()
    
    
def create_image(base, base_metadata, 
                 output, metadata,
                 build_file,
                 verbose, **kwargs):
    type = metadata['type']
    if type == 'system':
        shutil.copy(base, output)
    else:
        recipe = tempfile.NamedTemporaryFile()
        recipe.write('''Bootstrap: localimage
    From: {base}

%runscript
    . /usr/local/bin/entrypoint
'''.format(base=base))
        v = {}       
        exec(compile(open(build_file, "rb").read(), build_file, 'exec'), v, v)
        if 'install' not in v:
            raise RuntimeError('No install function defined in %s' % build_file)
        install_function = v['install']
        
        recipe_builder = RecipeBuilder(output)
        install_function(base_dir=osp.dirname(build_file),
                         builder=recipe_builder,
                         verbose=verbose)
        recipe_builder.write(recipe)
        if verbose:
            print('---------- Singularity recipe ----------', file=verbose)
            print(open(recipe.name).read(), file=verbose)
            print('----------------------------------------', file=verbose)
            verbose.flush()
        subprocess.check_call(['sudo', 'singularity', 'build', '--disable-cache', output, recipe.name])

    
_singularity_version = None

def singularity_major_version():
    return singularity_version()[0]

def singularity_version():
    global _singularity_version

    if _singularity_version is None:
        output = subprocess.check_output(['singularity', '--version']).decode('utf-8')
        version = output.split()[-1].split('-')[0]
        _singularity_version = [int(x) for x in version.split('.')]
    return _singularity_version


_singularity_run_help = None

def singularity_run_help():
    """
    Useful to get available commandline options, because they differ with
    versions and systems.
    """
    global _singularity_run_help

    if _singularity_run_help:
        return _singularity_run_help

    output = subprocess.check_output(['singularity', 'help',
                                      'run']).decode('utf-8')
    return output


def singularity_has_option(option):
    doc = singularity_run_help()
    return doc.find(' %s ' % option) >= 0 or doc.find('|%s ' % option) >= 0


def run(config, command, gui, root, cwd, env, image, container_options,
        base_directory, verbose):    
    # With --cleanenv only variables prefixd by SINGULARITYENV_ are transmitted 
    # to the container
    singularity = ['singularity', 'run']
    if singularity_has_option('--cleanenv'):
        singularity.append('--cleanenv')
    singularity += ['--home', '/casa/host/home']
    if cwd:
        singularity += ['--pwd', cwd]
    
    if root:
        singularity = ['sudo'] + singularity
        
    overlay = osp.join(config['directory'], 'overlay.img')
    if osp.exists(overlay):
        singularity += ['--overlay', overlay]
    
    if gui:
        xauthority = osp.expanduser('~/.Xauthority')
        if osp.exists(xauthority):
            shutil.copy(xauthority,
                        osp.join(config['directory'], 'host/home/.Xauthority'))
    
    for dest, source in config.get('mounts', {}).items():
        source = source.format(**config)
        source = osp.expandvars(source)
        dest = dest.format(**config)
        dest = osp.expandvars(dest)
        singularity += ['--bind', '%s:%s' % (source, dest)]
        
    tmp_env = dict(config.get('env', {}))
    if gui:
        tmp_env.update(config.get('gui_env', {}))
    if env is not None:
        tmp_env.update(env)
    
    # Creates environment with variables prefixed by SINGULARITYENV_
    # with --cleanenv only these variables are given to the container
    container_env = os.environ.copy()
    for name, value in tmp_env.items():
        if name == 'HOME':
            continue  # cannot be specified this way any longer.
        value = value.format(**config)
        value = osp.expandvars(value)
        container_env['SINGULARITYENV_' + name] = value
        
    container_options = config.get('container_options', []) + (container_options or [])
    if cwd:
        for i, opt in enumerate(container_options):
            if opt == '--pwd' and singularity_has_option('--pwd'):
                container_options = container_options[:i] + container_options[i+2:]
                break
    if gui:
        gui_options = config.get('container_gui_options', [])
        if gui_options:
            container_options += [osp.expandvars(i) for i in gui_options]
        # handle --nv option, if a nvidia device is found
        if ('--nv' not in container_options and 
            os.path.exists('/dev/nvidiactl') and
            '--no-nv' not in container_options and
            singularity_has_option('--nv')):
            container_options.append('--nv')
        # remove --no-nv which is not a singularity option
        if '--no-nv' in container_options:
            container_options.remove('--no-nv')
    if 'SINGULARITYENV_PS1' not in container_env \
            and not [x for x in container_options if x.startswith('PS1=')] \
            and singularity_has_option('--env'):
        # the prompt with singularity 3 is ugly and cannot be overriden in the
        # .bashrc of the container.
        container_options += ['--env',
                              b'PS1=\[\\033[33m\]\u@\h \$\[\\033[0m\] ']

    singularity += container_options
    if image is None:
        image = config.get('image')
        if image is None:
            raise ValueError('image is missing from environement configuration file (casa_distro.json)')
        image = osp.join(base_directory, image)
        if not osp.exists(image):
            raise ValueError("'%s' does not exist" % image)
    singularity += [image]
    singularity += command
    if verbose:
        print('-' * 40, file=verbose)
        print('Running singularity with the following command:', file=verbose)
        print(*("'%s'" % i for i in singularity), file=verbose)
        print('\nUsing the following environment:', file=verbose)
        for n in sorted(container_env):
            v = container_env[n]
            print('    %s=%s' % (n, v), file=verbose)
        print('-' * 40, file=verbose)
    check_call(singularity, env=container_env)




def setup(type, distro, branch, system, name, base_directory, image,
          output, vm_memory, vm_disk_size, verbose, force):
    """
    Singularity specific part of setup command
    """
    raise NotImplementedError('setup is not implemented for Singularity')
