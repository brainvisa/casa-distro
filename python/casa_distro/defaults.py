# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

import os
import os.path as osp

default_base_directory = os.environ.get('CASA_BASE_DIRECTORY')
if not default_base_directory:
    default_base_directory = osp.join(osp.expanduser('~'), 'casa_distro')

publish_server = os.environ.get('BRAINVISA_PUBLISH_SERVER', 'brainvisa.info')
publish_login = os.environ.get('BRAINVISA_PUBLISH_LOGIN', 'brainvisa')
publish_dir = os.environ.get('BRAINVISA_PUBLISH_DIR',
                             '/var/www/html/brainvisa.info_download')
publish_url = f'{publish_login}@{publish_server}:{publish_dir}/'
default_download_url = f'https://{publish_server}/download'
