# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function

import datetime
from fnmatch import fnmatchcase
from getpass import getpass
import glob
import json
import os
import os.path as osp
import re
from subprocess import check_call
import sys
import tempfile

from casa_distro.build_workflow import iter_build_workflow
from casa_distro.info import __version__ as casa_distro_version
from casa_distro.info import version_major, version_minor

from casa_distro import log, six
from casa_distro.command import command
from casa_distro.defaults import (default_build_workflow_repository,
                                  default_repository_server,
                                  default_repository_server_directory,
                                  default_repository_login)
from casa_distro.defaults import default_download_url

from casa_distro.vbox import (vbox_create_system,
                              vbox_import_image,
                              VBoxMachine)

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
def create_release_plan(components=None, build_workflows_repository=default_build_workflow_repository, verbose=None):
    '''create a release plan file by reading sources.'''
    from casa_distro.bv_maker import update_release_plan_file
    
    update_release_plan_file(erase_file=True,
                             components=components,
                             build_workflows_repository=build_workflows_repository,
                             verbose=verbose)


@command
def update_release_plan(components=None, build_workflows_repository=default_build_workflow_repository, verbose=None):
    '''update a release plan file by reading sources.'''
    from casa_distro.bv_maker import update_release_plan_file

    update_release_plan_file(erase_file=False,
                             components=components,
                             build_workflows_repository=build_workflows_repository,
                             verbose=verbose)


@command
def html_release_plan(login=None, password=None, build_workflows_repository=default_build_workflow_repository, verbose=None):
    '''Convert a release plan to an HTML file for human inspection'''
    from casa_distro.bv_maker import release_plan_to_html
    release_plan_file = osp.join(build_workflows_repository, 'release_plan.yaml')
    release_plan_html = osp.join(build_workflows_repository, 'release_plan.html')
    release_plan_to_html(release_plan_file, release_plan_html)


@command
def create_latest_release(build_workflows_repository=default_build_workflow_repository, dry=None, ignore_warning = False, verbose=True):
    '''apply actions defined in the release plan file for the creation of the latest_release branch.'''
    import os, types
    from distutils.util import strtobool
    from casa_distro.bv_maker import apply_latest_release_todo
    
    try:
        if isinstance(dry, (bytes, str)):
            dry = bool(strtobool(dry))

        else:
            dry = bool(dry)
    except:
        print('dry argument must contain a value convertible to boolean', 
              file = sys.stderr)
        sys.exit(1)

    try:
        if isinstance(ignore_warning, (bytes, str)):
            ignore_warning = bool(strtobool(ignore_warning))

        else:
            ignore_warning = bool(ignore_warning)
    except:
        print('ignore_warning argument must contain a value convertible to',
              'boolean', file = sys.stderr)
        sys.exit(1)
    
    
    release_plan_file = osp.join(build_workflows_repository, 
                                 'release_plan.yaml')
    previous_run_output = osp.join(build_workflows_repository, 
                                   'create_latest_release.log')
        
    try:
        fail_on_error = True
        fail_on_warning = not ignore_warning
        
        apply_latest_release_todo(release_plan_file, previous_run_output, dry, fail_on_warning, fail_on_error, verbose)
        
    except RuntimeError as e:
        print('Impossible to apply release plan.', e.message,
              file = sys.stderr)
        raise
        
@command
def create_docker(image_names = '*', verbose=None, no_host_network=False):
    '''create or update all casa-test and casa-dev docker images

      image_names:
          filter for images which should be rebuilt. May be a coma-separated list, wildcards are allowed. Default: *

          Image names have generally the shape "cati/<type>:<system>". Image
          types and systems may be one of the buitin ones found in
          casa-distro (casa-test, casa-dev, cati_platform), or one user-defined
          which will be looked for in $HOME/.config/casa-distro/docker,
          $HOME/.casa-distro/docker, or in the share/docker subdirectory inside
          the main repository directory.
    '''
    from casa_distro.docker import create_docker_images
    
    image_name_filters = image_names.split(',')
    count = create_docker_images(
        image_name_filters = image_name_filters,
        no_host_network=bool(no_host_network))
    if count == 0:
        print('No image match filter "%s"' % image_names, file=sys.stderr)
        return 1

@command
def update_docker(image_names = '*', verbose=None):
    '''pull all casa-test and casa-dev docker images from DockerHub'''
    from casa_distro.docker import update_docker_images
    
    image_name_filters = image_names.split(',')
    count = update_docker_images(
        image_name_filters = image_name_filters)
    if count == 0:
        print('No image match filter "%s"' % image_names, file=sys.stderr)
        return 1


@command
def publish_docker(image_names = '*', verbose=None):
    '''publish docker images on dockerhub.com for public images or sandbox.brainvisa.info for private images'''
    from casa_distro.docker import publish_docker_images
    image_name_filters = image_names.split(',')
    count = publish_docker_images(
        image_name_filters = image_name_filters)
    if count == 0:
        print('No image match filter "%s"' % image_names, file=sys.stderr)
        return 1

@command
def create_singularity(image_names = 'cati/*',
                       build_workflows_repository=default_build_workflow_repository,
                       verbose=None):
    '''create or update all casa-test and casa-dev docker images'''
    from casa_distro.singularity import create_singularity_images
    
    image_name_filters = image_names.split(',')
    count = create_singularity_images(
        bwf_dir=build_workflows_repository,
        image_name_filters = image_name_filters,
        verbose=verbose)
    if count == 0:
        print('No image match filter "%s"' % image_names, file=sys.stderr)
        return 1

@command
def publish_singularity(image_names = 'cati/*',
                        build_workflows_repository=default_build_workflow_repository,
                        repository_server=default_repository_server, 
                        repository_server_directory=default_repository_server_directory,
                        login=default_repository_login, verbose=None):
    '''Publish singularity images to the sftp server'''
    verbose = log.getLogFile(verbose)
    
    image_name_filters = [i.replace('/', '_').replace(':', '_') for i in image_names.split(',')]
    image_files = []
    for filter in image_name_filters:
        image_files += glob.glob(osp.join(build_workflows_repository, filter + '.simg'))
    if not image_files:
        print('No image match filter "%s"' % image_names, file=sys.stderr)
        return 1

    # check if uploads are needed or if images already habe valid md5 on the
    # server
    server_url = default_download_url
    valid_files = []
    for image_file in image_files:
        hash_path = image_file + '.md5'
        hash_file = os.path.basename(hash_path)
        with open(hash_path) as f:
            local_hash = f.read()
        tmp = tempfile.NamedTemporaryFile()
        url = '%s/%s' % (server_url, hash_file)
        try:
            if verbose:
                print('check image:', url)
            urlretrieve(url, tmp.name)
            with open(tmp.name) as f:
                remote_hash = f.read()
            if remote_hash == local_hash:
                valid_files.append(image_file)
                if verbose:
                    print('Not updating', image_file, 'which is up-to-date',
                          file=verbose)
        except Exception as e:
            pass # not on server
    image_files = [f2 for f2 in image_files if f2 not in valid_files]
    if len(image_files) == 0:
        # nothing to do
        if verbose:
            print('All images are up-to-date.')
        return

    lftp_script = tempfile.NamedTemporaryFile()
    if login:
        remote = 'sftp://%s@%s' % (login, repository_server)
    else:
        remote = 'sftp://%s' % repository_server
    print('connect', remote, file=lftp_script)
    print('cd', repository_server_directory, file=lftp_script)
    for f in image_files:
        print('put', f, file=lftp_script)
        print('put', f + '.md5', file=lftp_script)
        if os.path.exists(f + '.dockerid'):
            print('put', f + '.dockerid', file=lftp_script)
    lftp_script.flush()
    cmd = ['lftp', '-f', lftp_script.name]
    if verbose:
        print('Running', *cmd, file=verbose)
        print('-' * 10, lftp_script.name, '-'*10, file=verbose)
        with open(lftp_script.name) as f:
            print(f.read(), file=verbose)
        print('-'*40, file=verbose)
    check_call(cmd)

@command
def publish_build_workflows(distro='*', branch='*', system='*', 
                            build_workflows_repository=default_build_workflow_repository, 
                            repository_server=default_repository_server, 
                            repository_server_directory=default_repository_server_directory,
                            login=default_repository_login, verbose=None):
    '''Upload a build workflow to sftp server (require lftp command to be installed).'''
        
    verbose = log.getLogFile(verbose)
    if login:
        remote = '%s@%s:' % (login, repository_server)
    else:
        remote = '%s:' % repository_server
    for d, b, s, bwf_dir in iter_build_workflow(build_workflows_repository, distro=distro, branch=branch, system=system):
        relative_bwf_dir = bwf_dir[len(build_workflows_repository)+1:]
        
        cmd = ['rsync', '-rR', '--delete',
               '--inplace', '--partial', '--links', '--times', '--perms',
               osp.join(build_workflows_repository, '.', relative_bwf_dir) + '/', 
               remote + repository_server_directory + '/']
        if verbose:
            print('Publish', bwf_dir, file=verbose)
            cmd.append('--progress')
        check_call(cmd)


@command
def create_system(source=osp.join(default_build_workflow_repository, 'ubuntu-*.{extension}'), 
                  image_name='casa-{source}',
                  output=osp.join(default_build_workflow_repository, '{image_name}.{extension}'),
                  container_type='singularity'):
    '''First step for the creation of base system VirtualBox image'''
    
    if container_type == 'singularity':
        source_extension = 'simg'
        output_extension = 'simg'
    elif container_type == 'vbox':
        source_extension = 'iso'
        output_extension = 'vdi'
    else:
        raise ValueError('Unsupported container type: %s' % container_type)

    source = source.format(extension=source_extension)
    if not osp.exists(source):
        sources = glob.glob(osp.expandvars(osp.expanduser(source)))
        if len(sources) == 0:
            # Raise appropriate error for non existing file
            open(source)
        elif len(sources) > 1:
            raise ValueError('Several source files found : {0}'.format(', '.join(sources)))
        source = sources[0]

    image_name = image_name.format(source=osp.splitext(osp.basename(iso))[0])
    output = osp.expandvars(osp.expanduser(output)).format(image_name=image_name,
                                                           extension=output_extension)


    metadata_output = output + '.json'
    print('Create metadata in', metadata_output)
    metadata = {
        'image_name': image_name,
        'container_type': container_type,
        'creation_time': datetime.datetime.now().isoformat(),
        'source': osp.basename(source),
        'source_time': datetime.datetime.fromtimestamp(os.stat(iso).st_mtime).isoformat(),
    }
    json.dump(metadata, open(metadata_output, 'w'), indent=4)
    
    if container_type == 'singularity':
        message = singularity_create_system(image_name=image_name, 
                                            source_image=source,
                                            output=output,
                                            verbose=sys.stdout)
    elif container_type == 'vbox':
        message = vbox_create_system(image_name=image_name, 
                                    iso=source,
                                    output=output,
                                    verbose=sys.stdout)
    
    if message:
        print(message)
    


@command
def publish_system(system=osp.join(default_build_workflow_repository, 'casa-ubuntu-*'),
                   container_type='vbox'):
    '''Upload a system image on brainvisa.info web site'''
    
    if container_type != 'vbox':
        raise ValueError('Only "vbox" container type requires to create a system image')
    
    system = system + '.vdi'
    if not osp.exists(system):
        systems = glob.glob(osp.expandvars(osp.expanduser(system)))
        if len(systems) == 0:
            # Raise appropriate error for non existing file
            open(system)
        elif len(systems) > 1:
            raise ValueError('Several system files found : {0}'.format(', '.join(systems)))
        system = systems[0]
    
    # Add system file size and md5 hash to JSON metadata file
    metadata_file = system + '.json'
    metadata = json.load(open(metadata_file))
    metadata['size'] = os.stat(system).st_size
    metadata['md5'] = file_hash(system)
    json.dump(metadata, open(metadata_file, 'w'), indent=4)
    
    check_call(['rsync', '--partial', '--inplace', '--progress',
                system, metadata_file,
                'brainvisa@brainvisa.info:prod/www/casa-distro/vbox/'])


@command
def download_system(system='casa-ubuntu-*',
                    url= default_download_url + '/vbox',
                    output=osp.join(default_build_workflow_repository, '{system}'),
                    container_type='vbox'):
    '''Download a system image from brainvisa.info web site'''
    
    if container_type != 'vbox':
        raise ValueError('Only "vbox" container type requires to create a system image')
    
    system = system + '.vdi'
    systems = [i for i in url_listdir(url) 
               if fnmatchcase(i, system)]
    if len(systems) == 0:
        raise ValueError('Cannot find file corresponding to pattern {0} in {1}'.format(system, url))
    elif len(systems) > 1:
        raise ValueError('Several system files found in {1}: {0}'.format(', '.join(systems), url))
    system = systems[0]
    output = output.format(system=system)
    output = osp.expandvars(osp.expanduser(output))
    
    system_dict = json.loads(urlopen(url + '/%s.json' % system).read())
    json_output = output + '.json'
    download_all = True
    if osp.exists(json_output):
        output_dict = json.load(open(json_output))
        if output_dict['md5'] == system_dict['md5']:
            download_all = False
    
    json.dump(system_dict, open(json_output, 'w'))
    if download_all:
        check_call(['wget', 
                    '{url}/{system}'.format(url=url, system=system),
                    '-O', output])
    else:
        check_call(['wget', '--continue', 
                    '{url}/{system}'.format(url=url, system=system),
                    '-O', output])


@command
def create_casa_run(system_image=osp.join(default_build_workflow_repository, 'casa-ubuntu-*.vdi'),
                    vbox_machine='casa-run', 
                    output=osp.join(default_build_workflow_repository, '{vbox_machine}.vdi'),
                    container_type='vbox',
                    memory='8192',
                    disk_size='131072',
                    gui='no'):
    '''Create a casa-run image'''
    
    if container_type not in ('singularity', 'vbox'):
        raise ValueError('Unsupported container type: %s' % container_type)

    if system_image:
        if not osp.exists(system_image):
            systems = glob.glob(osp.expandvars(osp.expanduser(system_image)))
            if len(systems) == 0:
                # Raise appropriate error for non existing file
                open(system_image)
            elif len(systems) > 1:
                raise ValueError('Several system images found : {0}'.format(', '.join(systems)))
            system_image = systems[0]
        output = osp.expandvars(osp.expanduser(output)).format(vbox_machine=vbox_machine)
        vbox_import_image(system_image, vbox_machine, output,
                          verbose=sys.stdout,
                          memory=memory,
                          disk_size=disk_size)
        parent_metadata = json.load(open(system_image + '.json'))
    else:
        # system_image was forced to empty in order to reuse an existing VBox VM
        # therefore no metadata can be found.
        parent_metadata = {}
    
    image_name = osp.splitext(osp.basename(output))[0]
    metadata_output = output + '.json'
    metadata = {
        'image_name': image_name,
        'container_type': container_type,
        'creation_time': datetime.datetime.now().isoformat(),
    }
    for key in ('iso', 'system'):
        value = parent_metadata.get(key)
        if value is not None:
            metadata[key] = value
    json.dump(metadata, open(metadata_output, 'w'), indent=4)

    vbox = VBoxMachine(vbox_machine)
    vbox.install('run', verbose=sys.stdout,
                 gui=str_to_bool(gui))


@command
def create_casa_dev(system_image=osp.join(default_build_workflow_repository, 'casa-ubuntu-*.vdi'),
                    casa_run_image=osp.join(default_build_workflow_repository, 'casa-run.vdi'),
                    vbox_machine='casa-dev', 
                    output=osp.join(default_build_workflow_repository, '{vbox_machine}.vdi'),
                    container_type='vbox',
                    memory='8192',
                    disk_size='131072',
                    gui='no'):
    '''Create a casa-dev image'''
    
    if container_type != 'vbox':
        raise NotImplementedError('Only "vbox" container type is implemented')
    
    if system_image:
        if not osp.exists(system_image):
            systems = glob.glob(osp.expandvars(osp.expanduser(system_image)))
            if len(systems) == 0:
                system_image = ''
            elif len(systems) > 1:
                raise ValueError('Several system images found : {0}'.format(', '.join(systems)))
            system_image = systems[0]

    if casa_run_image:
        if not osp.exists(casa_run_image):
            casa_runs = glob.glob(osp.expandvars(osp.expanduser(casa_run_image)))
            if len(casa_run_image) == 0:
                casa_run_image = ''
            elif len(casa_runs) > 1:
                raise ValueError('Several casa-run images found : '
                    '{0}'.format(', '.join(systems)))
            casa_run_image = casa_runs[0]

    if system_image and casa_run_image:
        raise ValueError('Cannot chose base image between system image (%s) '
                         'and casa-run image (%s)' % (system_image, 
                                                      casa_run_image))
    
    base_image = system_image or casa_run_image
    if base_image:
        output = osp.expandvars(osp.expanduser(output)).format(vbox_machine=vbox_machine)
        
        image_name = osp.splitext(osp.basename(output))[0]
        parent_metadata = json.load(open(base_image + '.json'))
        metadata_output = output + '.json'
        metadata = {
            'image_name': image_name,
            'container_type': container_type,
            'creation_time': datetime.datetime.now().isoformat(),
        }
        for key in ('iso', 'system'):
            value = parent_metadata.get(key)
            if value is not None:
                metadata[key] = value
        json.dump(metadata, open(metadata_output, 'w'), indent=4)
        
        vbox_import_image(base_image, vbox_machine, output,
                          verbose=sys.stdout,
                          memory=memory,
                          disk_size=disk_size)

    vbox = VBoxMachine(vbox_machine)

    if system_image:
        vbox.install('run', verbose=sys.stdout,
                     gui=str_to_bool(gui))

    vbox.install('dev', verbose=sys.stdout,
                 gui=str_to_bool(gui))


@command
def publish_image(image=osp.join(default_build_workflow_repository, 'casa-{image_type}{extension}'),
                  image_type='run',
                  container_type='vbox'):
    '''Upload a casa_run image on brainvisa.info web site'''
    
    if container_type != 'vbox':
        raise ValueError('Only "vbox" container type is supported for upload')
    
    extension = '.vdi'
    image = image.format(image_type=image_type,
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
    
    check_call(['rsync', '-P', '--progress',
                metadata_file, image, 
                'brainvisa@brainvisa.info:prod/www/casa-distro/vbox/'])
