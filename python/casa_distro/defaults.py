import os
import os.path as osp

default_build_workflow_repository = os.environ.get('CASA_DEFAULT_REPOSITORY')
if not default_build_workflow_repository:
    default_build_workflow_repository = osp.expanduser('~/casa_distro')
default_repository_server = 'brainvisa.info'
default_repository_server_directory = 'prod/www/casa-distro'
default_download_url = 'http://%s/casa-distro'  % default_repository_server
default_repository_login = 'brainvisa'
default_distro = 'opensource'
default_branch = 'latest_release'
default_system = 'ubuntu-12.04'
