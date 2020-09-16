# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function

import datetime
from fnmatch import fnmatchcase
from getpass import getpass
import glob
import json
import os
import os.path as osp
from pprint import pprint
import re
from subprocess import check_call
import sys
import tempfile

from casa_distro.build_workflow import iter_environments
from casa_distro.info import __version__ as casa_distro_version
from casa_distro.info import version_major, version_minor

from casa_distro import six
from casa_distro.command import command, check_boolean
from casa_distro.defaults import (default_build_workflow_repository,
                                  default_repository_server,
                                  default_repository_server_directory,
                                  default_repository_login,
                                  default_download_url,
                                  default_system)
from casa_distro.environment import (casa_distro_directory,
                                     run_container,
                                     select_environment,
                                     update_container_image)
from casa_distro.log import verbose_file, boolean_value
import casa_distro.singularity
import casa_distro.vbox
from casa_distro.hash import file_hash
from casa_distro.web import url_listdir, urlretrieve, urlopen


_true_str = re.compile('^(?:yes|true|y|1)$', re.I)
_false_str = re.compile('^(?:no|false|n|0|none)$', re.I)
def str_to_bool(string):
    if _false_str.match(string):
        return False
    if _true_str.match(string):
        return True
    raise ValueError('Invalid value for boolean: ' + repr(string))

@command
def download_image(type,
                   filename='casa-{type}-*.{extension}',
                   url= default_download_url + '/{container_type}',
                   output=osp.join(default_build_workflow_repository, '{filename}'),
                   container_type='singularity',
                   force=False,
                   verbose=True):
    """
    Download an image from brainvisa.info web site

    type
    filename
    url
    output
    container_type
    force
    verbose
    """
    verbose = verbose_file(verbose)

    if type not in ('system', 'run', 'dev'):
        raise ValueError('Unsupported image type: {0}'.format(type))
    
    if container_type == 'singularity':
        extension = 'sif'
    elif container_type == 'vbox':
        extension = 'vdi'
    else:
        raise ValueError('Unsupported container type: %s' % container_type)
    
    filename = filename.format(type=type, extension=extension)
    url = url.format(container_type=container_type)
    filenames = [i for i in url_listdir(url) 
              if fnmatchcase(i, filename)]
    if len(filenames) == 0:
        raise ValueError('Cannot find file corresponding to pattern {0} in {1}'.format(filename, url))
    elif len(filenames) > 1:
        raise ValueError('Several image files found in {1}: {0}'.format(', '.join(filenames), url))
    filename = filenames[0]
    output = output.format(filename=filename)
    output = osp.expandvars(osp.expanduser(output))

    update_container_image(container_type, output, url, force=force,
                           verbose=verbose, new_only=False)

@command
def create_base_image(type,
                 name='casa-{type}-{system}',
                 base=None,
                 output=osp.join(default_build_workflow_repository, '{name}.{extension}'),
                 container_type='singularity',
                 memory='8192',
                 disk_size='131072',
                 gui='no',
                 cleanup='yes',
                 verbose=True):
    """
    Create a new virtual image

    Parameters
    ----------
    type
        type of image to create. Either "system" for a base system image, or "run"
        for an image used in a user environment, or "dev" for a developer image.

    name
        default={name_default}
        name of the virtual image (no other image must have the same name).

    base
        Source file use to buld the image. The default value depends on image type and
        container type.
        
    output
        default={output_default}
        File location where the image is created.
        
    container_type
        default={container_type_default}
        Type of virtual appliance to use. Either "singularity", "vbox" or "docker".
        
    memory
        default={memory_default}
        For vbox container type only. Size in MiB of memory allocated for virtual machine.
        
    disk_size
        default={disk_size_default}
        For vbox container type only. Size in MiB of maximum disk size of virtual machine.
        
    gui
        default={gui_default}
        For vbox container type only. If value is "yes", "true" or "1", display VirtualBox window.
 
    cleanup
        default={cleanup_default}
        If "no", "false" or "0", do not cleanup after a failure during image building. This may 
        allow to debug a problem after the failure. For instance, with Singularity one can use a
        command like :
          sudo singularity run --writable /tmp/rootfs-79744fb2-f3a7-11ea-a080-ce9ed5978945 /bin/bash
          
    verbose
        default={verbose_default}
        Print more detailed information if value is "yes", "true" or "1".
     """
    verbose = verbose_file(verbose)
    gui = boolean_value(gui)
    cleanup = boolean_value(cleanup)
    
    if type not in ('system', 'run', 'dev'):
        raise ValueError('Image type can only be "system", "run" or "dev"')
    
    if container_type == 'singularity':
        origin_extension = 'sif'
        extension = 'sif'
    elif container_type == 'vbox':
        origin_extension = 'iso'
        extension = 'vdi'
    else:
        raise ValueError('Unsupported container type: %s' % container_type)

    if base is None:
        if type == 'system':
            base = osp.join(default_build_workflow_repository, 'ubuntu-*.{extension}').format(
                extension=origin_extension)
        elif type == 'run':
            base = osp.join(default_build_workflow_repository, 'casa-system-ubuntu-*.{extension}').format(
                extension=extension)
        else:
            base = osp.join(default_build_workflow_repository, 'casa-run-ubuntu-*.{extension}').format(
                extension=extension)
    
    if not osp.exists(base):
        base_pattern = osp.expandvars(osp.expanduser(base))
        if verbose:
            print('Looking for base in', base_pattern,
                    file=verbose)
        bases = glob.glob(base_pattern)
        if len(bases) == 0:
            # Raise appropriate error for non existing file
            open(base)
        elif len(bases) > 1:
            raise ValueError('Several base images found : {0}'.format(', '.join(bases)))
        base = bases[0]
        
    if osp.exists(base + '.json'):
        base_metadata = json.load(open(base + '.json'))
    else:
        base_metadata = {}
    system = base_metadata.get('system', default_system)        
    
    name = name.format(type=type, system=system)
    output = osp.expandvars(osp.expanduser(output)).format(name=name,
                                                           system=system,
                                                           extension=extension)

    if type == 'system':
        build_file = None
    else:
        share_dir = osp.join(osp.dirname(osp.dirname(osp.dirname(__file__))), 
                             'share')
        casa_docker = osp.join(share_dir, 'docker', 'casa-%s' % type, system)

        build_file = osp.join(casa_docker, 'build_image.py')
        open(build_file) # raise appropriate exception if file does not exist
        
    metadata_output = output + '.json'
    metadata = {
        'name': name,
        'type': type,
        'system': system,
        'container_type': container_type,
        'creation_time': datetime.datetime.now().isoformat(),
    }
    origin = base_metadata.get('origin')
    if origin:
        metadata['origin'] = origin
    elif type == 'system':
        metadata['origin'] = os.path.basename(base)

    if verbose:
        print('Creating', output, file=verbose)
        print('based on', base, file=verbose)
        if build_file:
            print('using', build_file, file=verbose)
        print('metadata = ', end='', file=verbose)
        pprint(metadata, stream=verbose, indent=4)
    json.dump(metadata, open(metadata_output, 'w'), indent=4)

    if container_type == 'vbox':
        module = casa_distro.vbox
    else:
        module = casa_distro.singularity
        
    msg = module.create_image(base, base_metadata, 
                              output, metadata,
                              build_file=build_file,
                              cleanup=cleanup,
                              verbose=verbose,
                              memory=memory,
                              disk_size=disk_size,
                              gui=gui)
    if msg:
        print(msg)
    elif osp.isfile(output):
        metadata['size'] = os.stat(output).st_size
        metadata['md5'] = file_hash(output)
        json.dump(metadata, open(metadata_output, 'w'), indent=4)



@command
def publish_base_image(type,
                       image=osp.join(default_build_workflow_repository, 'casa-{type}-*.{extension}'),
                       container_type='singularity',
                       verbose=True):
    """
    Upload an image to BrainVISA web site.
    
    Parameters
    ----------
    
    type
        type of image to publish. Either "system" for a base system image, or "run"
        for an image used in a user environment, or "dev" for a developer image.

    image
        default={image_default}
        Image file to upload (as well as the corresponding JSON file)
        
    container_type
        default={container_type_default}
        Type of virtual appliance to use. Either "singularity", "vbox" or "docker".

    verbose
        default={verbose_default}
        Print more detailed information if value is "yes", "true" or "1".
    """
    verbose = verbose_file(verbose)
    if container_type == 'singularity':
        extension = 'sif'
    elif container_type == 'vbox':
        extension = 'vdi'
    else:
        raise ValueError('Unsupported container type: %s' % container_type)
    
    image = image.format(type=type,
                         extension=extension)
    if not osp.exists(image):
        images = glob.glob(osp.expandvars(osp.expanduser(image)))
        if len(images) == 0:
            # Raise appropriate error for non existing file
            open(image)
        elif len(images) > 1:
            raise ValueError('Several image files found : {0}'.format(', '.join(images)))
        image = images[0]
    
    # Add image file md5 hash to JSON metadata file
    metadata_file = image + '.json'
    metadata = json.load(open(metadata_file))
    metadata['size'] = os.stat(image).st_size
    metadata['md5'] = file_hash(image)
    json.dump(metadata, open(metadata_file, 'w'), indent=4)
    
    check_call(['rsync', '-P', '--progress', '--chmod=a+r',
                metadata_file, image, 
                'brainvisa@brainvisa.info:prod/www/casa-distro/%s/' % container_type])


@command
def create_user_image(version,
                      name='{distro}-{version}',
                      base_image='{base_directory}/casa-run-{system}{extension}',
                      distro=None,
                      system=None,
                      environment_name=None,
                      container_type='singularity',
                      output=osp.join(default_build_workflow_repository, 'releases', '{name}{extension}'),
                      base_directory=casa_distro_directory(),
                      install='yes',
                      generate='yes',
                      upload='no',
                      verbose=True):
    """
    Create a run image given a development environment.
    The development environment is selected among existing ones its
    distro and system or simply by its name. Only developement environments
    using the master branch are considered.
    This command can perform three steps. Each step can be ignored by setting
    the corresponding option to "no" :
    
    - install: perform an installation of the development environment into its installation directory. This modify the development environment by updating its installation directory.
    
    - generate: generate a new image for the run environment. The ne image is based on base_image and the installation directory of the development environment is copied into the image in /casa/install.
    
    - upload: upload the run image on BrainVISA web site.
    
    
    Parameters
    ----------
    version
        Version of the release to create.
    name
        default={name_default}
        Name given to the created image.
    distro
        If given, select environment having the given distro name.
    system
        If given, select environments having the given system name.
    environment_name
        If given, select environment by its name.
    container_type
        default={container_type_default}
        Type of virtual appliance to use. Either "singularity", "vbox" or "docker".
    base_directory
        default={base_directory_default}
        Directory where images and environments are stored
    install
        default={install_default}
        If "true", "yes" or "1", perform the installation step.
        If "false", "no" or "0", skip this step
    generate
        default={generate_default}
        If "true", "yes" or "1", perform the image creation step.
        If "false", "no" or "0", skip this step
    upload
        default={upload_default}
        If "true", "yes" or "1", upload the image on BrainVISA web site.
        If "false", "no" or "0", skip this step
    verbose
        default={verbose_default}
        Print more detailed information if value is "yes", "true" or "1".
    """
    install = check_boolean('install', install)
    generate = check_boolean('generate', generate)
    upload = check_boolean('upload', upload)

    verbose = verbose_file(verbose)    
    if container_type == 'singularity':
        extension = '.sif'
    elif container_type == 'vbox':
        extension = '.vdi'
    else:
        raise ValueError('Unsupported container type: %s' % container_type)
    config = select_environment(base_directory,
                                type='dev',
                                distro=distro,
                                branch='master',
                                system=system,
                                name=environment_name)
    name = name.format(version=version, **config)
    kwargs = config.copy()
    kwargs.pop('name', None)
    output = osp.expandvars(osp.expanduser(output)).format(name=name,
                                                           extension=extension,
                                                           **kwargs)
    if container_type == 'vbox':
        module = casa_distro.vbox
    else:
        module = casa_distro.singularity
    
    metadata = {
        'name': name,
        'type': 'run',
        'distro': config['distro'],
        'system': config['system'],
        'version': version,
        'container_type': container_type,
        'creation_time': datetime.datetime.now().isoformat(),
    }        
    base_image=base_image.format(base_directory=base_directory,
                                 extension=extension,
                                 **metadata)
    
    if install:
        run_container(config=config, 
            command=['make', 'BRAINVISA_INSTALL_PREFIX=/casa/host/install', 'install-runtime'],
            gui=False, 
            opengl="auto",
            root=False, 
            cwd='/casa/host/build',
            env={},
            image=None, 
            container_options=None,
            base_directory=base_directory, 
            verbose=verbose)

    metadata_file = output + '.json'
    
    if generate:
        msg = module.create_user_image(
                    base_image=base_image,
                    dev_config=config,
                    output=output,
                    base_directory=base_directory,
                    verbose=verbose)
        if msg:
            print(msg)

        # Add image file md5 hash to JSON metadata file
        metadata['size'] = os.stat(output).st_size
        metadata['md5'] = file_hash(output)
        json.dump(metadata, open(metadata_file, 'w'), indent=4)
    
    if upload:
        check_call(['rsync', '-P', '--progress', '--chmod=a+r',
                    metadata_file, output, 
                    'brainvisa@brainvisa.info:prod/www/casa-distro/releases/'])
