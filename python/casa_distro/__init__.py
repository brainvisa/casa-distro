from __future__ import absolute_import

import os
import os.path as osp
from glob import glob

from .info import NAME as project_name, version_major, version_minor

# Find location of the shared directory

share_directory = osp.join(osp.dirname(__file__), 'share')
if not osp.exists(share_directory):
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

def share_directories():
    ''' Get a list of "share" directories, including personal paths
    ($CASA_DISTRO/share, $HOME/.config/casa_distro, $HOME/.casa_distro) and the
    builtin casa-distro share directory, when they exist.
    '''
    # use other personal locations for share directories

    share_directories = []
    from casa_distro.defaults import default_build_workflow_repository
    if default_build_workflow_repository is not None:
        share_directories.append(osp.join(default_build_workflow_repository,
                                          'share'))
    share_directories += [osp.join(osp.expanduser('~'), '.casa-distro'),
                          osp.join(osp.expanduser('~'), '.config',
                                  'casa-distro')]
    share_directories = [d for d in share_directories if os.path.isdir(d)] \
        + [share_directory]
    return share_directories

