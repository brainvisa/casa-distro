from __future__ import print_function

from getpass import getpass
import sys
import tempfile
import os.path as osp
import six

from casa_distro.command import command
from casa_distro.defaults import (default_build_workflow_repository,
                                  default_repository_server,
                                  default_repository_server_directory,
                                  default_repository_login)

@command
def package_casa_distro(build_workflows_repository=default_build_workflow_repository):
    '''Create a casa_distro.zip containing a usable version of casa_distro'''
    import casa_distro
    import brainvisa.maker
    import tempfile
    import shutil
    import zipfile
    import os
    import os.path as osp
    from fnmatch import fnmatch
    
    from casa_distro.info import __version__ as casa_distro_version

    dirs = {
        osp.dirname(casa_distro.__file__): ('casa_distro', '*.py'),
        osp.dirname(brainvisa.maker.__file__): ('brainvisa/maker', '*.py'),
        casa_distro.share_directory: ('share', None),
    }
    tmp = tempfile.mkdtemp()
    try:
        # Copy files in temporary directory
        os.mkdir(osp.join(tmp,'brainvisa'))
        open(osp.join(tmp, 'brainvisa', '__init__.py'), 'w')
        shutil.copy(__file__, osp.join(tmp, '__main__.py'))
        for srcdir, dstdir_filter in dirs.items():
            dstdir, filter = dstdir_filter
            os.mkdir(osp.join(tmp, dstdir))
            len_srcdir = len(srcdir) + 1
            for dirpath, dirnames, filenames in os.walk(srcdir):
                zipdir = osp.join(dstdir, dirpath[len_srcdir:])
                for i in dirnames:
                    os.mkdir(osp.join(tmp, zipdir, i))
                for i in filenames:
                    if not filter or fnmatch(i, filter):
                        shutil.copy(osp.join(dirpath, i), osp.join(tmp, zipdir, i))

        # Create zip archive of temporary directory
        with zipfile.ZipFile(osp.join(build_workflows_repository, 'casa_distro-%s.zip' % casa_distro_version), mode='w') as zip:
            len_tmp = len(tmp)+1
            for dirpath, dirnames, filenames in os.walk(tmp):
                zipdir = dirpath[len_tmp:]
                for i in filenames:
                    f = zip.write(osp.join(dirpath,i), osp.join(zipdir,i))
    finally:
        shutil.rmtree(tmp)

@command
def publish_casa_distro(build_workflows_repository=default_build_workflow_repository, 
                        repository_server=default_repository_server, 
                        repository_server_directory=default_repository_server_directory,
                        login=default_repository_login, verbose=None):
    '''Publish casa_distro.zip file previously created with package_casa_distro to the sftp server'''
    from subprocess import check_call
    
    from casa_distro.info import __version__ as casa_distro_version
    
    
    lftp_script = tempfile.NamedTemporaryFile()
    if login:
        remote = 'sftp://%s@%s' % (login, repository_server)
    else:
        remote = 'sftp://%s' % repository_server
    print('connect', remote, file=lftp_script)
    print('cd', repository_server_directory, file=lftp_script)
            
    print('put %s/casa_distro-%s.zip' % (build_workflows_repository, casa_distro_version), file=lftp_script)
    print('rm -f casa_distro.zip', file=lftp_script)
    print('ln -s casa_distro-%s.zip casa_distro.zip' % casa_distro_version, file=lftp_script)
    lftp_script.flush()
    cmd = ['lftp', '-f', lftp_script.name]
    if verbose:
        print('Running', *cmd, file=verbose)
        print('-' * 10, lftp_script.name, '-'*10, file=verbose)
        print(open(lftp_script.name).read(), file=verbose)
        print('-'*40, file=verbose)
    check_call(cmd)
    

@command
def create_release_plan(components=None, build_workflows_repository=default_build_workflow_repository, verbose=None):
    '''create a release plan file by reading sources.'''
    from casa_distro.bv_maker import inspect_components_and_create_release_plan
    import yaml # TODO move related code into bv_maker.py
    
    if components:
        components = components.split(',')
    release_plan_file = open(osp.join(build_workflows_repository, 'release_plan.yaml'), 'w')
    release_plan = inspect_components_and_create_release_plan(components, verbose=verbose)
    print(yaml.dump(release_plan, default_flow_style=False), file=release_plan_file)


@command
def publish_release_plan(login=None, password=None, build_workflows_repository=default_build_workflow_repository, verbose=None):
    '''send information to the CASA forum about things that would be done with the release plan file'''
    from casa_distro.bv_maker import publish_release_plan_on_wiki
    if password is None:
        password = getpass('BioProj password for %s: ' % login)
    release_plan_file = osp.join(build_workflows_repository, 'release_plan.yaml')
    publish_release_plan_on_wiki(login, password, release_plan_file)


@command
def apply_release_plan(build_workflows_repository=default_build_workflow_repository, dry=None, ignore_warning = False, verbose=None):
    '''apply actions defined in release plan file'''
    import os, types
    from distutils.util import strtobool
    from casa_distro.bv_maker import FailOn, apply_release_plan
    
    try:
        if type(dry) in (types.StringType, types.UnicodeType):
            dry = bool(strtobool(dry))

        else:
            dry = bool(dry)
    except:
        print('dry argument must contain a value convertible to boolean', 
              file = sys.stderr)
        sys.exit(1)

    try:
        if type(ignore_warning) in (types.StringType, types.UnicodeType):
            ignore_warning = bool(strtobool(ignore_warning))

        else:
            ignore_warning = bool(ignore_warning)
    except:
        print('ignore_warning argument must contain a value convertible to',
              'boolean', file = sys.stderr)
        sys.exit(1)
    
    
    release_plan_file = osp.join(build_workflows_repository, 
                                 'release_plan.yaml')
        
    try:
        fail_on = FailOn.ERROR
        fail_on |= FailOn.NONE if ignore_warning else FailOn.WARNING
        
        apply_release_plan(release_plan_file, dry, fail_on, verbose)
        
    except RuntimeError as e:
        print('Impossible to apply release plan.', e.message,
              file = sys.stderr)
        sys.exit(1)
        
@command
def create_docker(image_names = '*', verbose=None):
    '''create or update all casa-test and casa-dev docker images'''
    from casa_distro.docker import create_docker_images
    
    image_name_filters = image_names.split(',')
    count = create_docker_images(
        image_name_filters = image_name_filters)
    if count == 0:
        print('No image match filter "%s"' % image_names, file=sys.stderr)
        sys.exit(1)

@command
def update_docker(image_names = '*', verbose=None):
    '''pull all casa-test and casa-dev docker images from DockerHub'''
    from casa_distro.docker import update_docker_images
    
    image_name_filters = image_names.split(',')
    count = update_docker_images(
        image_name_filters = image_name_filters)
    if count == 0:
        print('No image match filter "%s"' % image_names, file=sys.stderr)
        sys.exit(1)


@command
def publish_docker(image_names = '*', verbose=None):
    '''publish docker images on dockerhub.com for public images or sandbox.brainvisa.info for private images'''
    from casa_distro.docker import publish_docker_images
    image_name_filters = image_names.split(',')
    count = publish_docker_images(
        image_name_filters = image_name_filters)
    if count == 0:
        print('No image match filter "%s"' % image_names, file=sys.stderr)
        sys.exit(1)

@command
def publish_build_workflows(distro='*', branch='*', system='*', 
                            build_workflows_repository=default_build_workflow_repository, 
                            repository_server=default_repository_server, 
                            repository_server_directory=default_repository_server_directory,
                            login=default_repository_login, verbose=None):
    '''Upload a build workflow to sftp server (require lftp command to be installed).'''
    
    from subprocess import check_call
    from casa_distro import iter_build_workflow
    
    lftp_script = tempfile.NamedTemporaryFile()
    if login:
        remote = 'sftp://%s@%s' % (login, repository_server)
    else:
        remote = 'sftp://%s' % repository_server
    print('connect', remote, file=lftp_script)
    print('cd', repository_server_directory, file=lftp_script)
    for d, b, s, bwf_dir in iter_build_workflow(build_workflows_repository, distro=distro, branch=branch, system=system):
        relative_bwf_dir = bwf_dir[len(build_workflows_repository)+1:]
        
        cmd = ['mirror', '-R', '--delete', bwf_dir, relative_bwf_dir]
        if verbose:
            cmd.insert(2, '-v')
        print(*cmd, file=lftp_script)
    lftp_script.flush()
    cmd = ['lftp', '-f', lftp_script.name]
    if verbose:
        print('Running', *cmd, file=verbose)
        print('-' * 10, lftp_script.name, '-'*10, file=verbose)
        print(open(lftp_script.name).read(), file=verbose)
        print('-'*40, file=verbose)
    check_call(cmd)

