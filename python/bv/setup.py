# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

import os.path as osp
import sys

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

if __name__ == '__main__':
    setup_dir = '/casa/setup'
    builtin_metadata_file = '/casa/casa_distro.json'

    if not osp.exists(output):
        print('Directory {} does not exist.'.format(setup_dir), 
              file=sys.stderr)
        sys.exit(1)

    environment = json.load(open(builtin_metadata_file))

    if not osp.exists(osp.join(setup_dir, 'host', 'conf')):
        os.makedirs(osp.join(setup_dir, 'host', 'conf'))

    casa_distro_json = osp.join(setup_dir, 'host', 'conf', 'casa_distro.json')
    json.dump(environment, open(casa_distro_json, 'w'), indent=4)

    write_environment_homedir(osp.join(setup_dir, 'home'))
    