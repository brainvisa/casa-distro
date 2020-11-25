# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

import json
import os
import os.path as osp
import platform
import shutil
import sys
import time

import casa_distro


def write_environment_homedir(casa_home_host_path):
    """Create a new home directory for an environment."""
    if not osp.exists(casa_home_host_path):
        os.makedirs(casa_home_host_path)
    bashrc = osp.join(casa_home_host_path, '.bashrc')
    if not osp.exists(bashrc):
        with open(bashrc, 'w') as f:
            print(r'''
if [ -f /etc/profile ]; then
    . /etc/profile
fi

# source any bash_completion scripts
if [ -n "$CASA_BUILD" -a -d "$CASA_BUILD/etc/bash_completion.d" ]; then
    # from a build directory
    for d in "$CASA_BUILD/etc/bash_completion.d/"*; do
        if [ -f "$d" ]; then
            . "$d"
        fi
    done
elif [ -d "/casa/install/etc/bash_completion.d" ]; then
    # else from an install directory
    for d in "/casa/install/etc/bash_completion.d/"*; do
        if [ -f "$d" ]; then
            . "$d"
        fi
    done
fi

export PS1="\[\033[33m\]\u@\h \$\[\033[0m\] "

''', file=f)


def find_in_path(command):
    path = os.environ.get('PATH', os.defpath)
    if not path:
        return None
    path = path.split(os.pathsep)

    seen = set()
    for dir in path:
        normdir = os.path.normcase(dir)
        if normdir not in seen:
            seen.add(normdir)
            name = os.path.join(dir, command)
            if (osp.exists(name)
                    and os.access(name, os.F_OK | os.X_OK)
                    and not osp.isdir(name)):
                return name
    return None


if __name__ == '__main__':
    setup_dir = '/casa/setup'

    if not osp.exists(setup_dir):
        print('Directory {} does not exist.'.format(setup_dir),
              file=sys.stderr)
        sys.exit(1)

    if not osp.exists(osp.join(setup_dir, 'host', 'conf')):
        os.makedirs(osp.join(setup_dir, 'host', 'conf'))
    bin = osp.join(setup_dir, 'bin')
    if not osp.exists(bin):
        os.makedirs(bin)

    bv = find_in_path('bv')
    if bv:
        shutil.copy(bv, osp.join(bin, 'bv'))

    casa_distro_dir = osp.join(setup_dir, 'casa_distro')
    casa_distro_bin = osp.join(casa_distro_dir, 'bin')
    if not osp.exists(casa_distro_bin):
        os.makedirs(casa_distro_bin)
    casa_distro_python = osp.join(casa_distro_dir, 'python')
    if not osp.exists(casa_distro_python):
        os.makedirs(casa_distro_python)
    for command in ('casa_distro', 'casa_distro_admin'):
        source = find_in_path(command)
        if source:
            shutil.copy(source, osp.join(casa_distro_bin, command))
            casa_distro_source = osp.dirname(casa_distro.__file__)
    casa_distro_dest = osp.join(casa_distro_python,
                                osp.basename(casa_distro_source))
    if osp.exists(casa_distro_dest):
        shutil.rmtree(casa_distro_dest)
    shutil.copytree(casa_distro_source,
                    casa_distro_dest)

    environment = {
        'casa_distro_compatibility': str(casa_distro.version_major),
        'type': 'run',
        'container_type': 'singularity',
    }
    environment['distro'] = os.getenv('CASA_DISTRO')
    if not environment['distro']:
        environment['distro'] = 'unkown_distro'
    environment['system'] = os.getenv('CASA_SYSTEM')
    if not environment['system']:
        environment['system'] = \
            '-'.join(platform.linux_distribution()[:2]).lower()
    if 'CASA_BRANCH' in os.environ:
        environment['branch'] = os.environ['CASA_BRANCH']
    environment['image'] = os.getenv('SINGULARITY_CONTAINER')
    if not environment['image']:
        environment['image'] = '/unknown.sif'
    if environment['image'] != '/unknown.sif':
        environment['name'] = \
            osp.splitext(osp.basename(environment['image']))[0]
    else:
        environment['name'] = '{}-{}'.format(environment['distro'],
                                             time.strftime('%Y%m%d'))
    json.dump(environment,
              open(osp.join(setup_dir, 'host', 'conf',
                            'casa_distro.json'), 'w'),
              indent=4)

    write_environment_homedir(osp.join(setup_dir, 'home'))
