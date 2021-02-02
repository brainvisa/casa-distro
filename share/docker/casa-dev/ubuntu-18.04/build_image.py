# -*- coding: utf-8 -*-
import os.path as osp

from casa_distro.image_builder import ImageBuilder


builder = ImageBuilder('casa-run')


@builder.step
def copying_files(base_dir, builder):
    'Copying files'

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


@builder.step
def apt_dev_dependencies(base_dir, builder):
    'Install apt dependencies for developement'

    builder.run_root('/opt/install_apt_dev_dependencies.sh')


@builder.step
def pip_dev_dependencies(base_dir, builder):
    'Install pip dependencies for developement'
    builder.run_root('/opt/install_pip_dev_dependencies.sh')


@builder.step
def compiled_dev_dependencies(base_dir, builder):
    'Install compiled dependencies for developement'
    builder.run_root('/opt/install_compiled_dev_dependencies.sh')


@builder.step
def install_casa_distro(base_dir, builder):
    'Install casa_distro'
    builder.install_casa_distro('/casa/casa-distro')


@builder.step
def casa_dev_components(base_dir, builder):
    'Install casa components for developement'
    builder.run_root('/opt/install_casa_dev_components.sh')

    builder.copy_root(osp.join(base_dir, 'gitignore'), '/etc')
    builder.run_root('git config --system core.excludesfile /etc/gitignore')


@builder.step
def cleanup(base_dir, builder):
    'Cleanup installation files'
    builder.run_root('rm -f /opt/install_apt_dev_dependencies.sh '
                     '/opt/build_sip_pyqt.sh '
                     '/opt/install_pip_dev_dependencies.sh '
                     '/opt/install_compiled_dev_dependencies.sh '
                     '/opt/install_casa_dev_components.sh')
