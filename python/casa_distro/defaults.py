# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

import os
import os.path as osp

default_base_directory = os.environ.get('CASA_BASE_DIRECTORY')
if not default_base_directory:
    default_base_directory = osp.expanduser('~/casa_distro')
default_repository_server = 'brainvisa.info'
default_repository_server_directory = 'prod/www/casa-distro'
default_download_url = 'http://%s/casa-distro' % default_repository_server
default_repository_login = 'brainvisa'
default_environment_type = 'run'
default_distro = 'opensource'
default_branch = 'latest_release'
default_system = 'ubuntu-18.04'
