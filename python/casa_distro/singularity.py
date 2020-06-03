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


def get_image_filename(image, build_workflows_repository):
    return osp.join(build_workflows_repository, image + '.sif')


class RecipeBuilder:
    '''
    Class to interact with an existing VirtualBox machine.
    This machine is suposed to be based on a casa_distro system image.
    '''
    def __init__(self, name):
        self.name = name
        self.tmpdir = None
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


def run_singularity(casa_distro, command, gui=False, interactive=False,
                    tmp_container=True, container_image=None,
                    cwd=None, env=None, container_options=[],
                    verbose=None):
    verbose = verbose_file(verbose)
    
    # With --cleanenv only variables prefixd by SINGULARITYENV_ are transmitted 
    # to the container
    singularity = ['singularity', 'run', '--cleanenv', '--home', '/casa/host/home']
    if cwd:
        singularity += ['--pwd', cwd]
    
    if gui:
        xauthority = osp.expanduser('~/.Xauthority')
        if osp.exists(xauthority):
            shutil.copy(xauthority,
                        osp.join(casa_distro['build_workflow_dir'], 'host/home/.Xauthority'))
        
    for source, dest in six.iteritems(casa_distro.get('container_volumes',{})):
        source = source % casa_distro
        source = osp.expandvars(source)
        dest = dest % casa_distro
        dest = osp.expandvars(dest)
        singularity += ['--bind', '%s:%s' % (source, dest)]
        
    container_env = os.environ.copy()
    tmp_env = dict(casa_distro.get('container_env', {}))
    if gui:
        tmp_env.update(casa_distro.get('container_gui_env', {}))
    if env is not None:
        tmp_env.update(env)
    
    # Creates environment with variables prefixed by SINGULARITYENV_
    # with --cleanenv only these variables are given to the container
    for name, value in six.iteritems(tmp_env):
        value = value % casa_distro
        value = osp.expandvars(value)
        container_env['SINGULARITYENV_' + name] = value
    conf_options = casa_distro.get('container_options', [])
    if cwd:
        for i, opt in enumerate(conf_options):
            if opt == '--pwd':
                conf_options = conf_options[:i] + conf_options[i+2:]
                break
    options = list(conf_options)
    options += container_options
    if gui:
        gui_options = casa_distro.get('container_gui_options', [])
        if gui_options:
            options += [osp.expandvars(i) for i in gui_options
                        if i != '--no-nv']
        # handle --nv option, if a nvidia device is found
        if '--nv' not in options and os.path.exists('/dev/nvidiactl') \
                and '--no-nv' not in options:
            options.append('--nv')
        # remove --no-nv which is not a singularity option
        if '--no-nv' in options:
            options.remove('--no-nv')
    singularity += options
    if container_image is None:
        container_image = casa_distro.get('container_image')
        if container_image is None:
            raise ValueError('container_image is missing from casa_distro.json')
        container_image = get_image_filename(
            container_image,
            osp.dirname(osp.dirname(casa_distro['build_workflow_dir'])))
        if not osp.exists(container_image):
            raise ValueError("'%s' does not exist" % container_image)
    singularity += [container_image]
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



def create_writable_singularity_image(image, 
                                      build_workflow_directory,
                                      build_workflows_repository,            
                                      verbose):
    verbose = verbose_file(verbose)
    if build_workflow_directory:
        casa_distro_json = osp.join(build_workflow_directory, 'conf', 'casa_distro.json')
        casa_distro = json.load(open(casa_distro_json))
        image = casa_distro.get('container_image')
        
    read_image = get_image_filename(image, build_workflows_repository)
    write_image = read_image[:-4] + 'writable'
    check_call(['sudo', 'singularity', 'build', '--sandbox', write_image, read_image])


def singularity_root_shell(image, 
                           build_workflow_directory,
                           build_workflows_repository,            
                           verbose):
    verbose = verbose_file(verbose)
    if build_workflow_directory:
        casa_distro_json = osp.join(build_workflow_directory, 'conf', 'casa_distro.json')
        casa_distro = json.load(open(casa_distro_json))
        image = casa_distro.get('container_image')
        
    write_image = get_image_filename(image, build_workflows_repository)
    if not write_image.endswith('.writable.simg') \
            and not write_image.endswith('.writable'):
        if write_image.endswith('.simg'):
            write_image = write_image[:-5]
        write_image = write_image + '.writable'
    check_call(['sudo', 'singularity', 'shell', '--writable', write_image])

