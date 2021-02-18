# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

from glob import glob
import json
import os
import os.path as osp
import platform
import shutil
import stat
import sys
import time
import subprocess
import tempfile

import casa_distro
from casa_distro.environment import (prepare_environment_homedir, copytree, cp)
from casa_distro import downloader


def user_config_filename():
    """
    Get the user configuration file for casa-distro. This user config is
    outside of environments in order to allow configuration of read-only shared
    environments.
    """
    xdg_config_home = os.environ.get('XDG_CONFIG_HOME', '')
    if not xdg_config_home:
        host_home = os.environ['CASA_HOST_HOME']
        xdg_config_home = osp.join(host_home, '.config')
    user_config_file = osp.join(xdg_config_home,
                                'casa-distro', 'casa_distro_3.json')
    return user_config_file


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
        source_command = osp.join(source, command)
        try:
            if not os.stat(source_command).st_mode & stat.S_IXUSR:
                continue  # skip non-executable files (e.g. bv_env.sh)
        except OSError:
            # avoid skipping commands that do not have a binary (casa_distro
            # and casa_distro_admin)
            pass
        dest_link = osp.join(dest, command)
        if osp.exists(dest_link):
            os.remove(dest_link)
        os.symlink('bv', dest_link)


def download_install(install_dir, distro, version, url):
    system = os.environ['CASA_SYSTEM']
    image_version = ''
    if osp.exists('/casa/image_id'):
        with open('/casa/image_id') as f:
            image_id = json.load(f)
        image_version = image_id.get('image_version')
    if image_version is None:
        image_version = system
    distro_url = osp.join(url, version, distro, system, '%s-%s-%s.zip'
                          % (distro, version, image_version))
    print('download:', distro_url)
    local_zip = osp.join('/tmp', osp.basename(distro_url))
    json_url = '%s.json' % distro_url
    try:
        f = None
        try:
            f = downloader.urlopen(json_url)
            if f.getcode() == 404:
                return
            metadata = json.loads(f.read().decode('utf-8'))
        except Exception as e:
            print('%s could not be read:' % json_url, e)
            return
    finally:
        if f:
            f.close()
        del f

    downloader.download_file(distro_url, local_zip,
                             allow_continue=True,
                             use_tmp=True,
                             md5_check=metadata['md5'],
                             callback=downloader.stdout_progress)
    if not osp.exists(install_dir):
        os.makedirs(install_dir)
    try:
        subprocess.check_call(['unzip', local_zip], cwd=install_dir)
    finally:
        os.unlink(local_zip)


def is_writable(dir):
    try:
        x = tempfile.mkstemp(dir=dir)
    except Exception:
        return False
    os.close(x[0])
    os.unlink(x[1])
    return True


def setup_user(setup_dir='/casa/setup', rw_install=False, distro=None,
               version=None, url='https://brainvisa.info/download'):
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

    install_dir = '/casa/install'
    if distro is None and not osp.exists('/casa/install'):
        distro = 'brainvisa'
    if distro is not None:
        print('Downloading BrainVisa distro %s from the web site...' % distro)
        if not is_writable('/casa/install'):
            install_dir = osp.join(setup_dir, 'install')
        if version is None:
            version = os.environ['CASA_VERSION']
        download_install(install_dir, distro, version, url)
    elif rw_install:
        if is_writable('/casa_install'):
            print('The install directory is already writable. No need to copy '
                  'files.')
        else:
            print('copying BrainVisa installation into a writable '
                  'directory...')
            shutil.copytree('/casa/install', osp.join(setup_dir, 'install'))
            install_dir = osp.join(setup_dir, 'install')

    create_environment_bin_commands(osp.dirname(bv), bin)
    create_environment_bin_commands(osp.join(install_dir, 'bin'), bin)

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
    # test consistency: on Mac there is a problem here
    image = environment['image']
    sing_name = os.getenv('SINGULARITY_NAME')
    if image and osp.basename(image) != sing_name:
        # on mac/singularity 3 beta, we get:
        # SINGULARITY_CONTAINER=/dev/sda
        # SINGULARITY_NAME=brainvisa-5.0.0-test10.sif
        if 'SINGCWD' in os.environ:
            # hope the image was in the current directory, we cannot do better
            image = osp.join(os.getenv('SINGCWD'), sing_name)
            environment['image'] = image
        print(
            '** WARING **\n'
            'We could not determine automatically from the container '
            'where the container image is. Please edit the file '
            '/casa/host/conf/casa_distro.json (in the container) and '
            'fix the path to the image file on the host filesystem.')
    if not image:
        environment['image'] = '/unknown.sif'
    environment['name'] = osp.splitext(sing_name)[0]
    if not environment['name']:
        environment['name'] = '{}-{}'.format(environment['distro'],
                                             time.strftime('%Y%m%d'))

    # keep image ID in metadata
    if osp.exists('/casa/image_id'):
        with open('/casa/image_id') as f:
            image_id = json.load(f)
        environment['image_id'] = image_id['image_id']

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
              system=None, image_version=None, image=None, name=None):
    if not system:
        system = os.getenv('CASA_SYSTEM')
    if not system:
        system = \
            '-'.join(platform.linux_distribution()[:2]).lower()
    if not image_version:
        if osp.exists('/casa/image_id'):
            with open('/casa/image_id') as f:
                image_id = json.load(f)
            image_version = image_id.get('image_version')
    iver = image_version
    if not image_version:
        iver = system  # old nomenclature

    if name is None:
        name = '-'.join([distro, branch, iver])

    if not osp.exists(setup_dir):
        os.makedirs(setup_dir)

    all_subdirs = ['conf', 'src', 'build', 'install', 'bootstrap', 'bin']
    for subdir in all_subdirs:
        if not osp.exists(osp.join(setup_dir, subdir)):
            os.makedirs(osp.join(setup_dir, subdir))
    bin_dir = osp.join(setup_dir, 'bin')

    bv = osp.join(osp.dirname(osp.dirname(osp.dirname(__file__))),
                  'bin', 'bv')
    shutil.copy(bv, osp.join(bin_dir, 'bv'))

    with open(osp.join(setup_dir, 'bootstrap', 'README.txt'), 'w') as f:
        f.write('''\
You should never need to use the contents of this directory directly,
instead use bin/bv_maker that is at the top-level of your environment
directory to bootstrap your first BrainVISA compilation.

This directory contains a version of casa-distro and brainvisa-cmake
that can be used for doing the first compilation in an empty dev
environment. In fact, after a successful build this directory is never
used anymore, you may as well delete it if you wish.

- Whenever casa-distro sources are present in
  src/development/casa-distro, they will be used instead of the
  casa-distro that is in this directory (bin/bv takes charge of choosing
  the correct version).

- The brainvisa-cmake subdirectory is placed last on the PATH in the
  image, so the version that is compiled as part of a BrainVISA build
  tree will take precedence after the first successful build.
''')

    print('Bootstrapping brainvisa-cmake...')
    tmpdir = None
    try:
        tmpdir = tempfile.mkdtemp(prefix='brainvisa-cmake')
        retval = subprocess.call([
            'git', 'clone', '--depth=1',
            '--branch', branch,
            'https://github.com/brainvisa/brainvisa-cmake.git', tmpdir,
        ])
        if retval != 0:
            # If brainvisa-cmake does not have the requested branch, fall back
            # to the default branch (master).
            subprocess.check_call([
                'git', 'clone', '--depth=1',
                'https://github.com/brainvisa/brainvisa-cmake.git', tmpdir,
            ])
        subprocess.check_call([
            'cmake',
            '-DCMAKE_INSTALL_PREFIX=' + osp.join(
                setup_dir, 'bootstrap', 'brainvisa-cmake'),
            '.'],
            cwd=tmpdir)
        subprocess.check_call(['make', 'install'], cwd=tmpdir)
    except subprocess.CalledProcessError:
        print('WARNING: error while boostrapping brainvisa-cmake, '
              'your first compilation will use the older version '
              'that is included in the image (this is usually fine).',
              file=sys.stderr)
        create_environment_bin_commands(
            '/casa/bootstrap/brainvisa-cmake/bin', bin_dir)
    else:
        create_environment_bin_commands(
            osp.join(setup_dir, 'bootstrap', 'brainvisa-cmake', 'bin'),
            bin_dir)
        print('brainvisa-cmake bootstrapped successfully.')
    finally:
        if tmpdir:
            shutil.rmtree(tmpdir)
            tmpdir = None

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
        'image_version': image_version,
        'branch': branch,
        'container_type': 'singularity',
    })
    if image is None:
        image = os.getenv('SINGULARITY_CONTAINER')
        # test consistency: on Mac there is a problem here
        sing_name = os.getenv('SINGULARITY_NAME')
        if image and osp.basename(image) != sing_name:
            # on mac/singularity 3 beta, we get:
            # SINGULARITY_CONTAINER=/dev/sda
            # SINGULARITY_NAME=brainvisa-5.0.0-test10.sif
            if 'SINGCWD' in os.environ:
                # hope the image was in the current directory, we cannot
                # do better
                image = osp.join(os.getenv('SINGCWD'), sing_name)
            print(
                '** WARING **\n'
                'We could not determine automatically from the container '
                'where the container image is. Please edit the file '
                '/casa/host/conf/casa_distro.json (in the container) and '
                'fix the path to the image file on the host filesystem.')
        if not image:
            images = glob(osp.join(osp.expanduser(
                '~/casa_distro/casa-dev-*.sif')))
            if len(images) == 1:
                image = images[0]
            if not image:
                raise ValueError('No image found')
    environment['image'] = image
    environment['name'] = name
    # keep image ID in metadata
    if osp.exists('/casa/image_id'):
        with open('/casa/image_id') as f:
            image_id = json.load(f)
        environment['image_id'] = image_id['image_id']
        environment['image_version'] = image_id['image_version']

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
