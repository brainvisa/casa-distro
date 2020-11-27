# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

import json
import os
import os.path as osp
import platform
import shutil
import subprocess
import sys
import time

import casa_distro
from casa_distro.environment import (find_in_path,
                                     write_environment_homedir,
                                     copytree)


if __name__ == '__main__':
    setup_dir = '/casa/setup'

    distro = sys.argv[1]
    if len(sys.argv) > 1:
        branch = sys.argv[2]
    else:
        branch = os.environ['CASA_BRANCH']
    system = os.getenv('CASA_SYSTEM')

    if not system:
        system = \
            '-'.join(platform.linux_distribution()[:2]).lower()

    if not osp.exists(setup_dir):
        print('Directory {} does not exist.'.format(setup_dir),
              file=sys.stderr)
        sys.exit(1)

    all_subdirs = ('conf', 'src', 'build', 'install',)
    for subdir in all_subdirs:
        if not osp.exists(osp.join(setup_dir, 'host', subdir)):
            os.makedirs(osp.join(setup_dir, 'host', subdir))

    bin = osp.join(setup_dir, 'bin')
    if not osp.exists(bin):
        os.makedirs(bin)

    bv = find_in_path('bv')
    if bv:
        shutil.copy(bv, osp.join(bin, 'bv'))

    casa_distro_dir = osp.join(setup_dir, 'casa_distro')
    subprocess.check_call(['git', 'clone',
                           'https://github.com/brainvisa/casa-distro',
                           casa_distro_dir])

    distro_dir = osp.join(casa_distro_dir, 'share', 'distro', distro)
    if not osp.exists(osp.join(distro_dir, 'conf', 'casa_distro.json')):
        print('ERROR - invalid distro:', distro, file=sys.stderr)
        sys.exit(1)
    copytree(distro_dir, osp.join(setup_dir, 'host'))

    environment = {
        'casa_distro_compatibility': str(casa_distro.version_major),
        'distro': distro,
        'type': 'dev',
        'system': system,
        'branch': branch,
        'container_type': 'singularity',
    }
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

    svn_secret = osp.join(setup_dir, 'host', 'conf', 'svn.secret')
    print('\n------------------------------------------------------------')
    print('** WARNING: svn secret **')
    print('Before using "casa_distro bv_maker" you will have to '
          'setup svn to access the Biporoj server, which needs a login '
          'and a password.\n'
          'There are 2 methods for this, and 2 situations, which we could '
          'simplify as this:\n\n'
          '* opensource distro: if you are only using open-source '
          'projects, you can use the preconfigured "public" '
          'login/password: brainvisa / Soma2009.\n'
          'Credentials are stored in the followinf file:\n')
    print(svn_secret)
    print('\nYou may leave it as is or replace with your own login/password '
          'if you need to access restricted resources. Svn will be used '
          'non-interactively, it will not ask for password confirmation '
          '/ storage, but will reject any interactive input, including '
          'commit comments etc.')
    print('This file is a shell script that must set the variables '
          'SVN_USERNAME and SVN_PASSWORD. Do not forget to properly quote '
          'the values if they contains special characters.')
    print('For instance, the file could contain the two following lines '
          '(replacing "your_login" and "your_password" by appropriate '
          'values:\n')
    print("SVN_USERNAME='your_login'")
    print("SVN_PASSWORD='your_password'\n")
    print('If you need more interaction, then remove the svn.secret file, '
          'and let svn interactively ask you for login/password and store '
          'it appropriately, like in the following case.\n')
    print('* brainvisa and other non-totally opensource distros: they '
          'need a personal login and password. You can either use the '
          'above svn.secret method (create the file if it doesn\'t exist '
          'and fill in your information), or let svn interactively ask '
          'you a login and password, and let it store it the way it suits '
          'it. In this mode svn is used "directly", without interactive '
          'restrictions.\n\n')
    print('Remember also that you can edit and customize the projects to '
          'be built, by editing the following file:\n')
    print(osp.join(setup_dir, 'host', 'conf', 'bv_maker.cfg'))
    print('------------------------------------------------------------')
    print()
