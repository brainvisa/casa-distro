# -*- coding: utf-8 -*-
#
# This file is used for building the image for Singularity and VirtualBox. At
# the moment a separate Dockerfile is used to support Docker, *please* keep
# these files synchronized so that they perform exactly the same installation
# steps.

import os.path as osp

from casa_distro import six


def install(base_dir, builder, verbose):
    if verbose:
        six.print_('Creating /casa and other directories in', builder.name,
                   file=verbose, flush=True)
    builder.run_root('if [ ! -e /casa ]; then mkdir /casa; fi')
    builder.run_root('if [ ! -e /casa/host ]; then mkdir /casa/host; fi')
    if builder.user:
        builder.run_root('/bin/chown {0}:{0} /casa'.format(builder.user))
        builder.run_root('/bin/chown {0}:{0} /casa/host'.format(builder.user))

    # Use a minimal UTF-8-aware locale.
    #
    # TODO: implement builder.set_env (see
    # https://github.com/brainvisa/casa-distro/issues/114) and uncomment the
    # following line
    #
    # builder.set_env('LANG', 'C.UTF-8')

    if verbose:
        six.print_('Copying files in', builder.name,
                   file=verbose, flush=True)
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

    if verbose:
        six.print_('Copying entrypoint in', builder.name,
                   file=verbose, flush=True)
    builder.copy_root(osp.join(base_dir, 'entrypoint'),
                      '/usr/local/bin/')
    builder.run_root('chmod a+rx /usr/local/bin/entrypoint')

    # copy a software-only mesa libGL in /usr/local/lib
    builder.copy_root(osp.join(base_dir, 'mesa'), '/usr/local/lib/')

    if verbose:
        six.print_('Running install_apt_dependencies.sh',
                   file=verbose, flush=True)
    builder.run_root('/opt/install_apt_dependencies.sh')
    if verbose:
        six.print_('Running install_pip_dependencies.sh',
                   file=verbose, flush=True)
    builder.run_root('/opt/install_pip_dependencies.sh')
    if verbose:
        six.print_('Running install_compiled_dependencies.sh',
                   file=verbose, flush=True)
    builder.run_root('/opt/install_compiled_dependencies.sh')

    if verbose:
        six.print_('Running cleanup_build_dependencies.sh',
                   file=verbose, flush=True)
    builder.run_root('/opt/cleanup_build_dependencies.sh')

    if verbose:
        six.print_('Cleanup files in', builder.name,
                   file=verbose, flush=True)
    builder.run_root('rm -f /opt/neurodebian-key.gpg '
                     '/opt/neurodebian.sources.list '
                     '/opt/install_apt_dependencies.sh '
                     '/opt/build_dependencies.sh '
                     '/opt/install_pip_dependencies.sh '
                     '/opt/install_compiled_dependencies.sh '
                     '/opt/build_netcdf.sh '
                     '/opt/build_sip_pyqt.sh '
                     '/opt/cleanup_build_dependencies.sh')
