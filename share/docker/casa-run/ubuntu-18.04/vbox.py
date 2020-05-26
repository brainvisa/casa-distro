import six
import os.path as osp

def install(base_dir, vbox, verbose):
    if verbose:
        six.print_('Creating /casa and', vbox.tmp_dir, 'in', vbox.vm,
                file=verbose, flush=True)
    vbox.run_root('if [ ! -e "{0}" ]; then mkdir "{0}"; fi'.format(vbox.tmp_dir))
    vbox.run_root('if [ ! -e /casa ]; then mkdir /casa && /bin/chown {0}:{0} /casa; fi'.format(vbox.user))

    if verbose:
        six.print_('Copying files in', vbox.vm,
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
        vbox.copy_root(osp.join(base_dir, f), '/tmp')
    vbox.run_root('chmod +x /tmp/*.sh')

    if verbose:
        six.print_('Copying entrypoint in', vbox.vm,
                file=verbose, flush=True)
    vbox.copy_root(osp.join(base_dir, 'entrypoint'),
                            '/usr/local/bin/')
    vbox.run_root('chmod a+rx /usr/local/bin/entrypoint')

    if verbose:
        six.print_('Running install_apt_dependencies.sh',
                file=verbose, flush=True)
    vbox.run_root('/tmp/install_apt_dependencies.sh')
    if verbose:
        six.print_('Running install_pip_dependencies.sh',
                file=verbose, flush=True)
    vbox.run_root('/tmp/install_pip_dependencies.sh')
    if verbose:
        six.print_('Running install_compiled_dependencies.sh',
                file=verbose, flush=True)
    vbox.run_root('/tmp/install_compiled_dependencies.sh')

    if verbose:
        six.print_('Running cleanup_build_dependencies.sh',
                file=verbose, flush=True)
    vbox.run_root('/tmp/cleanup_build_dependencies.sh')


    if verbose:
        six.print_('Cleanup files in', vbox.vm,
                file=verbose, flush=True)
    vbox.run_root('rm -f /tmp/neurodebian-key.gpg '
                    '/tmp/neurodebian.sources.list '
                    '/tmp/install_apt_dependencies.sh '
                    '/tmp/build_dependencies.sh '
                    '/tmp/install_pip_dependencies.sh '
                    '/tmp/install_compiled_dependencies.sh '
                    '/tmp/build_netcdf.sh '
                    '/tmp/build_sip_pyqt.sh '
                    '/tmp/cleanup_build_dependencies.sh')
