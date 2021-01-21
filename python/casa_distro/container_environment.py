# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

from glob import glob
import json
import os
import os.path as osp
import platform
import shutil
import sys
import time

import casa_distro
from casa_distro.environment import (prepare_environment_homedir, copytree, cp)


def install_casa_distro(dest):
    source = osp.dirname(osp.dirname(osp.dirname(__file__)))
    for i in ('bin', 'cbin', 'python', 'etc', 'share'):
        dest_dir = osp.join(dest, i)
        if osp.exists(dest_dir):
            shutil.rmtree(dest_dir)
        copytree(osp.join(source, i), dest_dir,
                 symlinks=True,
                 ignore=lambda src, names, dst, dstnames:
                 {i for i in names if i in ('__pycache__',)
                  or i.endswith('.pyc') or i.endswith('~')})


exclude_from_bin = {
    'python', 'python2', 'python3', 'bv', 'bv_env', 'bv_env.sh', 'bv_env.bat',
    'bv_env.py', 'bv_env_host', 'bv_env_test', 'bv_unenv', 'bv_unenv.sh',
    'bv_unit_test', 'bv_wine_regedit', 'docker-deps',
}


def create_environment_bin_commands(source, dest):
    """
    Create, in dest, a symlink pointing to 'bv' for each file present in
    source except those in exclude_from_bin.
    """
    commands = {'casa_distro', 'casa_distro_admin'}
    commands.update(os.listdir(source))
    for command in commands:
        if command in exclude_from_bin:
            continue
        script = osp.join(dest, command)
        if osp.exists(script):
            os.remove(script)
        os.symlink('bv', script)


def setup_user(setup_dir='/casa/setup'):
    """
    Initialize a user environment directory.
    This function is supposed to be called from a user image.
    """
    if not osp.exists(setup_dir):
        os.makedirs(setup_dir)

    if not osp.exists(osp.join(setup_dir, 'conf')):
        os.makedirs(osp.join(setup_dir, 'conf'))
    bin = osp.join(setup_dir, 'bin')
    if not osp.exists(bin):
        os.makedirs(bin)

    bv = osp.join(osp.dirname(osp.dirname(osp.dirname(__file__))),
                  'bin', 'bv')
    dest = osp.join(bin, 'bv')
    shutil.copy(bv, dest)
    create_environment_bin_commands(osp.dirname(bv), bin)
    create_environment_bin_commands('/casa/install/bin', bin)

    casa_distro_dir = osp.join(setup_dir, 'casa-distro')
    install_casa_distro(casa_distro_dir)

    environment = {
        'casa_distro_compatibility': str(casa_distro.version_major),
        'type': 'user',
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
    if 'CASA_VERSION' in os.environ:
        environment['version'] = os.environ['CASA_VERSION']
    environment['image'] = os.getenv('SINGULARITY_CONTAINER')
    if not environment['image']:
        environment['image'] = '/unknown.sif'
    if environment['image'] != '/unknown.sif':
        environment['name'] = \
            osp.splitext(osp.basename(environment['image']))[00]
    else:
        environment['name'] = '{}-{}'.format(environment['distro'],
                                             time.strftime('%Y%m%d'))
    json.dump(environment,
              open(osp.join(setup_dir, 'conf',
                            'casa_distro.json'), 'w'),
              indent=4, separators=(',', ': '))

    prepare_environment_homedir(osp.join(setup_dir, 'home'))
    print('The software is now setup in a new user environment.')
    print('Now you can add in the PATH environment variable of your host '
          'system the bin/ subdirectory of the install directory. You may add '
          'it in your $HOME/.bashrc config file:\n')
    print('export PATH="<install_dir>/bin:$PATH"\n')
    print('(replacing "<install_dir> with the install directory). Then, after '
          'opening a new terminal, or sourcing the $HOME/.bashrc file, you '
          'can run programs like "bv", "anatomist", "brainvisa" etc.')
    print('The "bv" program without arguments runs a configuration interface '
          'that allows to customize the installation settings, environment '
          'variables, mount points in the virtual image, etc.')


def setup_dev(setup_dir='/casa/setup', distro='opensource', branch='master',
              system=None, image=None, name=None):
    if not system:
        system = os.getenv('CASA_SYSTEM')
    if not system:
        system = \
            '-'.join(platform.linux_distribution()[:2]).lower()

    if name is None:
        name = '-'.join([distro, branch, system])

    if not osp.exists(setup_dir):
        os.makedirs(setup_dir)

    all_subdirs = ('conf', 'src', 'build', 'install',)
    for subdir in all_subdirs:
        if not osp.exists(osp.join(setup_dir, subdir)):
            os.makedirs(osp.join(setup_dir, subdir))

    bin = osp.join(setup_dir, 'bin')
    if not osp.exists(bin):
        os.makedirs(bin)

    bv = osp.join(osp.dirname(osp.dirname(osp.dirname(__file__))),
                  'bin', 'bv')
    shutil.copy(bv, osp.join(bin, 'bv'))

    casa_distro_dir = osp.join(setup_dir, 'casa-distro')
    install_casa_distro(casa_distro_dir)

    distro_dir = osp.join(casa_distro_dir, 'share', 'distro', distro)
    casa_distro_json = osp.join(distro_dir, 'casa_distro.json')
    if not osp.exists(casa_distro_json):
        print('ERROR - invalid distro:', distro, file=sys.stderr)
        sys.exit(1)
    for i in os.listdir(distro_dir):
        if i == 'casa_distro.json':
            continue
        fp = osp.join(distro_dir, i)
        if osp.isdir(fp):
            copytree(fp, osp.join(setup_dir, i))
        else:
            cp(fp, osp.join(setup_dir, i))

    environment = json.load(open(casa_distro_json))
    environment.pop('description', None)
    environment.update({
        'casa_distro_compatibility': str(casa_distro.version_major),
        'distro': distro,
        'type': 'dev',
        'system': system,
        'branch': branch,
        'container_type': 'singularity',
    })
    if image is None:
        image = os.getenv('SINGULARITY_CONTAINER')
        if not image:
            images = glob(osp.join(osp.expanduser(
                '~/casa_distro/casa-dev-*.sif')))
            if len(images) == 1:
                image = images[0]
            if not image:
                raise ValueError('No image found')
    environment['image'] = image
    environment['name'] = name
    json.dump(environment,
              open(osp.join(setup_dir, 'conf',
                            'casa_distro.json'), 'w'),
              indent=4, separators=(',', ': '))

    prepare_environment_homedir(osp.join(setup_dir, 'home'))

    svn_secret = osp.join(setup_dir, 'conf', 'svn.secret')
    with open(svn_secret, 'w') as f:
        f.write('''\
# This is a shell script that must set the variables SVN_USERNAME
# and SVN_PASSWORD. Do not forget to properly quote the variable
# especially if values contains special characters.

SVN_USERNAME='brainvisa'
SVN_PASSWORD='Soma2009'
''')
    os.chmod(svn_secret, 0o600)  # hide password from other users

    print('''
------------------------------------------------------------------------
** WARNING: svn secret **

Before using "casa_distro bv_maker" you will have to set up svn to
access the BioProj server (https://bioproj.extra.cea.fr/), which needs a
login and a password.

There are two situations, which we could simplify as this:

* opensource distro: if you are only using open-source projects, you can
  use the public credentials:

    Username: brainvisa
    Password: Soma2009

* brainvisa and other non-totally opensource distros: they need a
  personal login and password.


Credentials can be handled in two ways, at your choice:

* The svn.secret method (default):

  Credentials are, by default, stored in a file named conf/svn.secret.

  This file is a shell script that must set the variables SVN_USERNAME
  and SVN_PASSWORD. Do not forget to properly quote the values if they
  contains special characters For instance, the file could contain the
  two following lines (replacing "your_login" and "your_password" by
  appropriate values):

  SVN_USERNAME='your_login'
  SVN_PASSWORD='your_password'

  CAVEAT: If the svn.secret file exists, SVN will be forced to use
  non-interactive mode: it will never ask for password confirmation /
  storage, and it will reject any interactive input, including commit
  comments, etc.

* If you need more interaction, then remove the svn.secret file and let
  svn interactively ask you for login/password and store it
  appropriately.
------------------------------------------------------------------------
Remember also that you can edit and customize the projects to
be built, by editing the following file:

    conf/bv_maker.cfg
------------------------------------------------------------------------
''')
