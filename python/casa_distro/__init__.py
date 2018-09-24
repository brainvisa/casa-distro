from __future__ import absolute_import

import os
import os.path as osp
from glob import glob

from .info import NAME as project_name, version_major, version_minor

# Find location of the shared directory

share_directory = osp.join(osp.dirname(osp.dirname(__file__)), 'share')
if not osp.exists(share_directory):
    share_directory = osp.join(osp.dirname(osp.dirname(osp.dirname(__file__))), 'share')
    if not osp.exists(share_directory):
        brainvisa_home = os.environ.get('BRAINVISA_HOME')
        if brainvisa_home:
            share_directory = osp.join(brainvisa_home, 'share', '%s-%s.%s' % (project_name, version_major, version_minor))
        del brainvisa_home
linux_os_ids = ['ubuntu-12.04', 'ubuntu-14.04', 'ubuntu-16.04', 'ubuntu-18.04']
casa_branches = ['latest_release', 'bug_fix', 'trunk']
