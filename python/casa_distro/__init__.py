from __future__ import absolute_import

import os
import os.path as osp
from glob import glob

from .info import NAME as project_name, version_major, version_minor
# Find location of the shared directory
share_directory = osp.join(os.environ.get('BRAINVISA_HOME', osp.dirname(osp.dirname(__file__))), 'share', '%s-%s.%s' % (project_name, version_major, version_minor))
linux_os_ids = ['ubuntu-12.04', 'ubuntu-14.04', 'ubuntu-16.04', 'ubuntu-18.04']
casa_branches = ['latest_release', 'bug_fix', 'trunk']
