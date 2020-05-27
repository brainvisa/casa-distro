# -*- coding: utf-8 -*-
import six
import os.path as osp

def install(base_dir, builder, verbose):
    if verbose:
        six.print_('Creating /casa and other directories in', builder.name,
                file=verbose, flush=True)
    if builder.tmpdir:
        builder.run_root('if [ ! -e "{0}" ]; then mkdir "{0}"; fi'.format(builder.tmp_dir))
    builder.run_root('if [ ! -e /casa ]; then mkdir /casa; fi')
    builder.run_root('if [ ! -e /casa/host ]; then mkdir /casa/host; fi')
    if builder.user:
        builder.run_root('/bin/chown {0}:{0} /casa'.format(builder.user))
        builder.run_root('/bin/chown {0}:{0} /casa/host'.format(builder.user))

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
        builder.copy_root(osp.join(base_dir, f), '/tmp')
    builder.run_root('chmod +x /tmp/*.sh')

    if verbose:
        six.print_('Copying entrypoint in', builder.name,
                file=verbose, flush=True)
    builder.copy_root(osp.join(base_dir, 'entrypoint'),
                            '/usr/local/bin/')
    builder.run_root('chmod a+rx /usr/local/bin/entrypoint')

    if verbose:
        six.print_('Running install_apt_dependencies.sh',
                file=verbose, flush=True)
    builder.run_root('/tmp/install_apt_dependencies.sh')
    if verbose:
        six.print_('Running install_pip_dependencies.sh',
                file=verbose, flush=True)
    builder.run_root('/tmp/install_pip_dependencies.sh')
    if verbose:
        six.print_('Running install_compiled_dependencies.sh',
                file=verbose, flush=True)
    builder.run_root('/tmp/install_compiled_dependencies.sh')

    if verbose:
        six.print_('Running cleanup_build_dependencies.sh',
                file=verbose, flush=True)
    builder.run_root('/tmp/cleanup_build_dependencies.sh')


    if verbose:
        six.print_('Cleanup files in', builder.name,
                file=verbose, flush=True)
    builder.run_root('rm -f /tmp/neurodebian-key.gpg '
                    '/tmp/neurodebian.sources.list '
                    '/tmp/install_apt_dependencies.sh '
                    '/tmp/build_dependencies.sh '
                    '/tmp/install_pip_dependencies.sh '
                    '/tmp/install_compiled_dependencies.sh '
                    '/tmp/build_netcdf.sh '
                    '/tmp/build_sip_pyqt.sh '
                    '/tmp/cleanup_build_dependencies.sh')
