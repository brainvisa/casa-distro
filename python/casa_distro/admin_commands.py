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
from casa_distro.command import command
from casa_distro.defaults import (default_build_workflow_repository,
                                  default_repository_server,
                                  default_repository_server_directory,
                                  default_repository_login,
                                  default_download_url,
                                  default_system)
from casa_distro.environment import (casa_distro_directory,
                                     select_environment)
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
                   verbose=True):
    """
    Download an image from brainvisa.info web site
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
    
    metadata = json.loads(urlopen(url + '/{0}.json'.format(filename)).read())
    json_output = output + '.json'
    download_all = True
    if osp.exists(json_output):
        output_metadata = json.load(open(json_output))
        if output_metadata['md5'] == metadata['md5']:
            download_all = False
    
    json.dump(metadata, open(json_output, 'w'), indent=4)
    if download_all:
        check_call(['wget', 
                    '{url}/{filename}'.format(url=url, filename=filename),
                    '-O', output])
    else:
        check_call(['wget', '--continue', 
                    '{url}/{filename}'.format(url=url, filename=filename),
                    '-O', output])


@command
def create_image(type,
                 name='casa-{type}-{system}',
                 base=None,
                 output=osp.join(default_build_workflow_repository, '{name}.{extension}'),
                 container_type='singularity',
                 memory='8192',
                 disk_size='131072',
                 gui='no',
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
 
    verbose
        default={verbose_default}
        Print more detailed information if value is "yes", "true" or "1".
     """
    verbose = verbose_file(verbose)
    gui = boolean_value(gui)
    
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
def publish_image(type,
                  image=osp.join(default_build_workflow_repository, 'casa-{type}-*.{extension}'),
                  container_type='singularity',
                  verbose=True):
    """
    Upload an image to BrainVISA web site.
    
    Parameters
    ----------
    
    type
        type of image to create. Either "system" for a base system image, or "run"
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
def create_release(version,
                   name='{distro}-{version}',
                   base_image='{base_directory}/casa-run-{system}{extension}',
                   distro=None,
                   system=None,
                   environment_name=None,
                   container_type='singularity',
                   output=osp.join(default_build_workflow_repository, 'release', '{name}{extension}'),
                   base_directory=casa_distro_directory(),
                   skip_install=False,
                   verbose=True):
    """
    Create a release image given a development environment.
    The development environment must be using the master branch.
    If several environments exist, one can be selected using its
    distro and system or simply by its name.
    
    Parameters
    ----------
    version
        Version of the release to create.
    name
        default={name_default}
        Name given to the created distro.
    distro
        If given, select environment having the given distro name.
    system
        If given, select environments having the given system name.
    environment_name
        If given, select environment by its name. It replaces type, distro,
        branch and system and is shorter to select one.
    container_type
        default={container_type_default}
        Type of virtual appliance to use. Either "singularity", "vbox" or "docker".
    base_directory
        default={base_directory_default}
        Directory where images and environments are stored
    skip_install
        default={skip_install_default}
        If "True", "Yes" or "1", skip the make install step.
    verbos
        default={verbose_default}
        Print more detailed information if value is "yes", "true" or "1".
    """
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
    print('Creating', name, 'from', config['directory'], 'in', output)
    if container_type == 'vbox':
        module = casa_distro.vbox
    else:
        module = casa_distro.singularity
    base_image=base_image.format(base_directory=base_directory,
                                 system=config['system'],
                                 extension=extension)
    msg = module.create_release(
                   base_image=base_image,
                   dev_config=config,
                   output=output,
                   base_directory=base_directory,
                   skip_install=skip_install,
                   verbose=verbose)
    if msg:
        print(msg)
    
