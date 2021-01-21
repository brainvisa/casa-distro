# -*- coding: utf-8 -*-
#
# This file is used for building the image for Singularity and VirtualBox. At
# the moment a separate Dockerfile is used to support Docker, *please* keep
# these files synchronized so that they perform exactly the same installation
# steps.

import os.path as osp

from casa_distro.builder import ImageBuilder


builder = ImageBuilder('casa-run')


@builder.step
def casa_dir(base_dir, builder):
    'Creating /casa and other directories'

    builder.run_root('if [ ! -e /casa ]; then mkdir /casa; fi')
    builder.run_root('if [ ! -e /casa/host ]; then mkdir /casa/host; fi')
    builder.run_root('if [ ! -e /casa/home ]; then mkdir /casa/home; fi')
    if builder.user:
        builder.run_root('/bin/chown {0}:{0} /casa'.format(builder.user))
        builder.run_root('/bin/chown {0}:{0} /casa/host'.format(builder.user))
        builder.run_root('/bin/chown {0}:{0} /casa/home'.format(builder.user))

    # Used in Singularity only
    builder.run_root('if [ ! -e /host ]; then mkdir /host; fi')


@builder.step
def copy_files(base_dir, builder):
    'Copying files'

    for f in ('install_apt_dependencies.sh',
              'build_dependencies.sh',
              'neurodebian.sources.list',
              'neurodebian-key.gpg',
              'install_pip_dependencies.sh',
              'install_compiled_dependencies.sh',
              'build_netcdf.sh',
              'build_sip_pyqt.sh',
              'cleanup_build_dependencies.sh'):
        # /opt is used instead of /tmp here because /tmp can be bind mount
        # during build on Singularity (and the copied files are hidden by this
        # mount).
        builder.copy_root(osp.join(base_dir, f), '/opt')
    builder.run_root('chmod +x /opt/*.sh')

    builder.copy_user(osp.join(base_dir, 'environment.sh'),
                      '/casa')
    builder.run_user('chmod a+rx /casa/environment.sh')

    builder.copy_user(osp.join(base_dir, 'bashrc'),
                      '/casa')
    builder.copy_root(osp.join(base_dir, 'entrypoint'),
                      '/usr/local/bin/')
    builder.run_root('chmod a+rx /usr/local/bin/entrypoint')

    # copy a software-only mesa libGL in /usr/local/lib
    builder.copy_root(osp.join(base_dir, 'mesa'), '/usr/local/lib/')


@builder.step
def apt_dependencies(base_dir, builder):
    'Running install_apt_dependencies.sh'

    builder.run_root('/opt/install_apt_dependencies.sh')


@builder.step
def pip_dependencies(base_dir, builder):
    'Running install_pip_dependencies.sh'

    builder.run_root('/opt/install_pip_dependencies.sh')


@builder.step
def compiled_dependencies(base_dir, builder):
    'Running install_compiled_dependencies.sh'

    builder.run_root('/opt/install_compiled_dependencies.sh')


@builder.step
def cleanup_build_dependencies(base_dir, builder):
    'Running cleanup_build_dependencies.sh'

    builder.run_root('/opt/cleanup_build_dependencies.sh')


@builder.step
def cleanup_files(base_dir, builder):
    'Cleanup files'

    builder.run_root('rm -f /opt/neurodebian-key.gpg '
                     '/opt/neurodebian.sources.list '
                     '/opt/install_apt_dependencies.sh '
                     '/opt/build_dependencies.sh '
                     '/opt/install_pip_dependencies.sh '
                     '/opt/install_compiled_dependencies.sh '
                     '/opt/build_netcdf.sh '
                     '/opt/build_sip_pyqt.sh '
                     '/opt/cleanup_build_dependencies.sh')
