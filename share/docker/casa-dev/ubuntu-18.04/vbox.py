import six
import os.path as osp

def install(base_dir, vbox, verbose):
    vbox.run_root('if [ ! -e "{0}" ]; then mkdir "{0}"; fi'.format(vbox.tmp_dir))

    if verbose:
        six.print_('Copying files in', vbox.vm,
                    file=verbose, flush=True)
    for f in ('install_apt_dev_dependencies.sh',
                'install_pip_dev_dependencies.sh',
                'install_compiled_dev_dependencies.sh',
                'build_sip_pyqt.sh',
                'install_casa_dev_components.sh'):
        vbox.copy_root(osp.realpath(osp.join(base_dir, f)), '/tmp')
    vbox.run_root('chmod +x /tmp/*.sh')

    vbox.copy_user(osp.join(base_dir, 'environment.sh'),
                    '/casa')
    vbox.run_user('chmod a+rx /casa/environment.sh')

    vbox.copy_user(osp.realpath(osp.join(base_dir, 'svn.secret')),
                    '/casa/conf')
    vbox.copy_root(osp.realpath(osp.join(base_dir, 'svn')),
                    '/usr/local/bin')
    vbox.run_root('chmod a+rx /usr/local/bin/svn')
    vbox.copy_root(osp.realpath(osp.join(base_dir, 'askpass-bioproj.sh')),
                    '/usr/local/bin')
    vbox.run_root('chmod a+rx /usr/local/bin/askpass-bioproj.sh')

    vbox.copy_user(osp.realpath(osp.join(base_dir, 'list-shared-libs-paths.sh')),
                    '/casa/')
    vbox.run_user('chmod a+rx /casa/list-shared-libs-paths.sh')

    if verbose:
        six.print_('Running install_apt_dev_dependencies.sh',
                file=verbose, flush=True)
    vbox.run_root('/tmp/install_apt_dev_dependencies.sh')
    if verbose:
        six.print_('Running install_pip_dev_dependencies.sh',
                file=verbose, flush=True)
    vbox.run_root('/tmp/install_pip_dev_dependencies.sh')
    if verbose:
        six.print_('Running install_compiled_dev_dependencies.sh',
                file=verbose, flush=True)
    vbox.run_root('/tmp/install_compiled_dev_dependencies.sh')

    if verbose:
        six.print_('Running install_casa_dev_components.sh',
                file=verbose, flush=True)
    vbox.run_root('/tmp/install_casa_dev_components.sh')


    if verbose:
        six.print_('Cleanup files in', vbox.vm,
                file=verbose, flush=True)
    vbox.run_root('rm -f /casa/install_apt_dev_dependencies.sh '
                    '/casa/build_sip_pyqt.sh '
                    '/casa/install_pip_dev_dependencies.sh '
                    '/casa/install_compiled_dev_dependencies.sh '
                    '/casa/install_casa_dev_components.sh')
