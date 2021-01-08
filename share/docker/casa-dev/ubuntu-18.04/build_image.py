# -*- coding: utf-8 -*-
import os.path as osp

from casa_distro import six


def install(base_dir, builder, verbose):
    if verbose:
        six.print_('Copying files in', builder.name,
                   file=verbose, flush=True)
    for f in ('install_apt_dev_dependencies.sh',
              'install_pip_dev_dependencies.sh',
              'install_compiled_dev_dependencies.sh',
              'build_sip_pyqt.sh',
              'install_casa_dev_components.sh'):
        # /opt is used instead of /tmp here because /tmp can be bind mount
        # during build on Singularity (and the copied files are hidden by this
        # mount).
        builder.copy_root(osp.realpath(osp.join(base_dir, f)), '/opt')
    builder.run_root('chmod +x /opt/*.sh')

    builder.copy_user(osp.join(base_dir, 'dev-environment.sh'),
                      '/casa')
    builder.run_user('chmod a+rx /casa/dev-environment.sh')

    builder.copy_user(osp.realpath(osp.join(base_dir, 'svn.secret')),
                      '/casa/host/conf')
    builder.copy_root(osp.realpath(osp.join(base_dir, 'svn')),
                      '/usr/local/bin')
    builder.run_root('chmod a+rx /usr/local/bin/svn')
    builder.copy_root(osp.realpath(osp.join(base_dir, 'askpass-bioproj.sh')),
                      '/usr/local/bin')
    builder.run_root('chmod a+rx /usr/local/bin/askpass-bioproj.sh')

    builder.copy_user(osp.realpath(osp.join(base_dir,
                                            'list-shared-libs-paths.sh')),
                      '/casa/')
    builder.run_user('chmod a+rx /casa/list-shared-libs-paths.sh')

    if verbose:
        six.print_('Running install_apt_dev_dependencies.sh',
                   file=verbose, flush=True)
    builder.run_root('/opt/install_apt_dev_dependencies.sh')
    if verbose:
        six.print_('Running install_pip_dev_dependencies.sh',
                   file=verbose, flush=True)
    builder.run_root('/opt/install_pip_dev_dependencies.sh')
    if verbose:
        six.print_('Running install_compiled_dev_dependencies.sh',
                   file=verbose, flush=True)
    builder.run_root('/opt/install_compiled_dev_dependencies.sh')

    if verbose:
        six.print_('Running install_casa_dev_components.sh',
                   file=verbose, flush=True)
    builder.run_root('/opt/install_casa_dev_components.sh')

    builder.copy_root(osp.join(base_dir, 'gitignore'), '/etc')
    builder.run_root('git config --system core.excludesfile /etc/gitignore')

    if verbose:
        six.print_('Cleanup files in', builder.name,
                   file=verbose, flush=True)
    builder.run_root('rm -f /opt/install_apt_dev_dependencies.sh '
                     '/opt/build_sip_pyqt.sh '
                     '/opt/install_pip_dev_dependencies.sh '
                     '/opt/install_compiled_dev_dependencies.sh '
                     '/opt/install_casa_dev_components.sh')
