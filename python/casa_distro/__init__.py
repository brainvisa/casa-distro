from __future__ import absolute_import

import os
import os.path as osp
from glob import glob

from .info import NAME as project_name, version_major, version_minor
# Find location of the shared directory
share_directory = osp.join(os.environ.get('BRAINVISA_HOME', osp.dirname(osp.dirname(__file__))), 'share', '%s-%s.%s' % (project_name, version_minor, version_minor))
linux_os_ids = ['ubuntu-12.04', 'ubuntu-16.04']
casa_branches = ['latest_release', 'bug_fix']


def iter_build_workflow(build_workflows_repository, distro='*', branch='*',
                        system='*'):
    for i in glob(osp.join(build_workflows_repository, distro, '%s-%s' % (branch, system), 'conf')):
        d, branch_system = osp.split(osp.dirname(i))
        the_branch, the_system = branch_system.split('-', 1)
        d, the_distro  = osp.split(d)
        yield (the_distro, the_branch, the_system, osp.dirname(i))
