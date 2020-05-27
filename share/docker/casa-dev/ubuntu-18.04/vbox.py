# -*- coding: utf-8 -*-
import six
import os.path as osp

def install(base_dir, builder, verbose):
    builder.run_root('if [ ! -e "{0}" ]; then mkdir "{0}"; fi'.format(builder.tmp_dir))

    if verbose:
        six.print_('Copying files in', builder.vm,
                    file=verbose, flush=True)
    for f in ('install_apt_dev_dependencies.sh',
                'install_pip_dev_dependencies.sh',
                'install_compiled_dev_dependencies.sh',
                'build_sip_pyqt.sh',
                'install_casa_dev_components.sh'):
        builder.copy_root(osp.realpath(osp.join(base_dir, f)), '/tmp')
    builder.run_root('chmod +x /tmp/*.sh')

    builder.copy_user(osp.join(base_dir, 'environment.sh'),
                    '/casa')
    builder.run_user('chmod a+rx /casa/environment.sh')

    builder.copy_user(osp.realpath(osp.join(base_dir, 'svn.secret')),
                    '/casa/host/conf')
    builder.copy_root(osp.realpath(osp.join(base_dir, 'svn')),
                    '/usr/local/bin')
    builder.run_root('chmod a+rx /usr/local/bin/svn')
    builder.copy_root(osp.realpath(osp.join(base_dir, 'askpass-bioproj.sh')),
                    '/usr/local/bin')
    builder.run_root('chmod a+rx /usr/local/bin/askpass-bioproj.sh')

    builder.copy_user(osp.realpath(osp.join(base_dir, 'list-shared-libs-paths.sh')),
                    '/casa/')
    builder.run_user('chmod a+rx /casa/list-shared-libs-paths.sh')

    if verbose:
        six.print_('Running install_apt_dev_dependencies.sh',
                file=verbose, flush=True)
    builder.run_root('/tmp/install_apt_dev_dependencies.sh')
    if verbose:
        six.print_('Running install_pip_dev_dependencies.sh',
                file=verbose, flush=True)
    builder.run_root('/tmp/install_pip_dev_dependencies.sh')
    if verbose:
        six.print_('Running install_compiled_dev_dependencies.sh',
                file=verbose, flush=True)
    builder.run_root('/tmp/install_compiled_dev_dependencies.sh')

    if verbose:
        six.print_('Running install_casa_dev_components.sh',
                file=verbose, flush=True)
    builder.run_root('/tmp/install_casa_dev_components.sh')


    if verbose:
        six.print_('Cleanup files in', builder.vm,
                file=verbose, flush=True)
    builder.run_root('rm -f /casa/install_apt_dev_dependencies.sh '
                    '/casa/build_sip_pyqt.sh '
                    '/casa/install_pip_dev_dependencies.sh '
                    '/casa/install_compiled_dev_dependencies.sh '
                    '/casa/install_casa_dev_components.sh')
