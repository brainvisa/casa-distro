from __future__ import print_function

from getpass import getpass
import sys
import tempfile
import os.path as osp
import glob

from casa_distro.info import __version__ as casa_distro_version
from casa_distro.info import version_major, version_minor

from casa_distro import log, six
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
    
    dirs = {
        osp.dirname(casa_distro.__file__): ('casa_distro', '*.py'),
        osp.dirname(brainvisa.maker.__file__): ('brainvisa/maker', '*.py'),
        osp.join(casa_distro.share_directory, 'distro'): ('share/distro', None),
    }
    tmp = tempfile.mkdtemp()
    try:
        # Copy files in temporary directory
        os.mkdir(osp.join(tmp,'brainvisa'))
        open(osp.join(tmp, 'brainvisa', '__init__.py'), 'w')
        shutil.copy(osp.join(osp.dirname(osp.dirname(osp.dirname(__file__))), 'bin','casa_distro'), osp.join(tmp, '__main__.py'))
        for srcdir, dstdir_filter in dirs.items():
            dstdir, filter = dstdir_filter
            os.makedirs(osp.join(tmp, dstdir))
            len_srcdir = len(srcdir) + 1
            for dirpath, dirnames, filenames in os.walk(srcdir):
                zipdir = osp.join(dstdir, dirpath[len_srcdir:])
                for i in dirnames:
                    os.mkdir(osp.join(tmp, zipdir, i))
                for i in filenames:
                    if not filter or fnmatch(i, filter):
                        shutil.copy(osp.join(dirpath, i), osp.join(tmp, zipdir, i))
        
        # Replace import six in brainvisa_projects.py
        brainvisa_projects = osp.join(tmp, 'brainvisa', 'maker', 'brainvisa_projects.py')
        content = open(brainvisa_projects).read().replace('import six', 'from casa_distro import six')
        open(brainvisa_projects, 'w').write(content)
        
        # Create zip archive of temporary directory
        with zipfile.ZipFile(osp.join(build_workflows_repository, 'casa-distro-%s.zip' % casa_distro_version), mode='w') as zip:
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
    
    verbose = log.getLogFile(verbose)
    
    lftp_script = tempfile.NamedTemporaryFile()
    if login:
        remote = 'sftp://%s@%s' % (login, repository_server)
    else:
        remote = 'sftp://%s' % repository_server
    print('connect', remote, file=lftp_script)
    print('cd', repository_server_directory, file=lftp_script)
            
    print('put %s/casa-distro-%s.zip' % (build_workflows_repository, casa_distro_version), file=lftp_script)
    print('rm -f casa-distro.zip', file=lftp_script)
    print('ln -s casa-distro-%s.zip casa-distro.zip' % casa_distro_version, file=lftp_script)
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
    from subprocess import check_call
    verbose = log.getLogFile(verbose)
    
    image_name_filters = [i.replace('/', '_').replace(':', '_') for i in image_names.split(',')]
    image_files = []
    for filter in image_name_filters:
        image_files += glob.glob(osp.join(build_workflows_repository, filter + '.sqsh'))
    if not image_files:
        print('No image match filter "%s"' % image_names, file=sys.stderr)
        return 1
                  
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
    lftp_script.flush()
    cmd = ['lftp', '-f', lftp_script.name]
    if verbose:
        print('Running', *cmd, file=verbose)
        print('-' * 10, lftp_script.name, '-'*10, file=verbose)
        print(open(lftp_script.name).read(), file=verbose)
        print('-'*40, file=verbose)
    check_call(cmd)

@command
def publish_build_workflows(distro='*', branch='*', system='*', 
                            build_workflows_repository=default_build_workflow_repository, 
                            repository_server=default_repository_server, 
                            repository_server_directory=default_repository_server_directory,
                            login=default_repository_login, verbose=None):
    '''Upload a build workflow to sftp server (require lftp command to be installed).'''
    
    from subprocess import check_call
    from casa_distro import iter_build_workflow
    
    verbose = log.getLogFile(verbose)
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

