# -*- coding: utf-8 -*-
#
# This file is used for building the image for Singularity and VirtualBox.

import os.path

from casa_distro.image_builder import ImageBuilder


builder = ImageBuilder('casa-run', base='casa-run-5.4.{extension}')


BUILD_FILES = [
    'install_apt_dev_dependencies.sh',
    'install_pip_dev_dependencies.sh',
    'install_casa_dev_components.sh',
]
"""List of files that are copied into /build and removed when done."""


@builder.step
def copy_build_files(base_dir, builder):
    """Copy files that are necessary for building the image."""
    for f in BUILD_FILES:
        # /build is used instead of /tmp here because /tmp can be bind-mounted
        # during build on Singularity (and the copied files are hidden by this
        # mount).
        builder.copy_root(os.path.realpath(os.path.join(base_dir, f)),
                          '/build')
    builder.run_root('chmod +x /build/*.sh')

    builder.copy_user(os.path.join(base_dir, 'dev-environment.sh'),
                      '/casa')
    builder.run_user('chmod a+rx /casa/dev-environment.sh')
    builder.run_user('echo "{\\"image_id\\": \\"%s\\", '
                     '\\"image_version\\": \\"%s\\"}"'
                     ' > /casa/image_id' % (builder.image_id,
                                            builder.image_version))

    builder.copy_root(os.path.realpath(os.path.join(base_dir, 'svn')),
                      '/usr/local/bin')
    builder.copy_root(os.path.realpath(os.path.join(base_dir,
                                                    'askpass-bioproj.sh')),
                      '/usr/local/bin')


@builder.step
def apt_dev_dependencies(base_dir, builder):
    """Run install_apt_dev_dependencies.sh."""
    builder.run_root('/build/install_apt_dev_dependencies.sh')


@builder.step
def pip_dev_dependencies(base_dir, builder):
    """Run install_pip_dev_dependencies.sh."""
    builder.run_root('/build/install_pip_dev_dependencies.sh')


@builder.step
def fix_wsl2(base_dir, builder):
    """Fix image to be compatible with Windows/WSL2.

    After apt_dev_dependencies, /run/shm is a symlink to /dev/shm
    But, on Winows/WSL2, /dev/shm is a symlink to /run/shm. Therefore
    The /run/shm is removed from the image and will be mounted by
    casa_distro according to the host system.
    """
    builder.run_root('if [ -L /run/shm ]; then rm /run/shm; fi')


@builder.step
def install_casa_distro(base_dir, builder):
    """Install casa_distro."""
    builder.install_casa_distro('/casa/casa-distro')


@builder.step
def casa_dev_components(base_dir, builder):
    """Install casa components for development."""
    builder.run_root('/build/install_casa_dev_components.sh')

    builder.copy_root(os.path.join(base_dir, 'gitignore'), '/etc')
    builder.run_root('git config --system core.excludesfile /etc/gitignore')


@builder.step
def cleanup(base_dir, builder):
    """Clean up build files."""
    builder.run_root('rm -rf /build')
