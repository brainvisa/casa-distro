# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

import os
import os.path as osp

from .info import NAME as project_name, version_major, version_minor

# Find location of the buiiltin share directory
share_directory = osp.join(osp.dirname(__file__), 'share')
if not osp.exists(share_directory):
    share_directory = osp.join(osp.dirname(osp.dirname(__file__)), 'share')
    if not osp.exists(share_directory):
        share_directory = osp.join(
            osp.dirname(osp.dirname(osp.dirname(__file__))), 'share')
        if not osp.exists(share_directory):
            brainvisa_home = os.environ.get('BRAINVISA_HOME')
            if brainvisa_home:
                share_directory = osp.join(
                    brainvisa_home, 'share',
                    '%s-%s.%s' % (project_name, version_major, version_minor)
                )
            del brainvisa_home
casa_branches = ['latest_release', 'master', 'integration']


def share_directories():
    """
    Get a list of "share" directories, including personal paths
    ($CASA_DISTRO/share, $HOME/.config/casa_distro) and the
    builtin casa-distro share directory, when they exist.
    """

    share_directories = []
    from casa_distro.defaults import default_base_directory
    if default_base_directory is not None:
        share_directories.append(osp.join(default_base_directory,
                                          'share'))
    share_directories += [osp.join(osp.expanduser('~'), '.local', 'share',
                                   'casa-distro')]
    share_directories = [d for d in share_directories if os.path.isdir(d)] \
        + [share_directory]
    return share_directories
