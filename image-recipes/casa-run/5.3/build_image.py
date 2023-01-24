# -*- coding: utf-8 -*-
#
# This file is used for building the image for Singularity and VirtualBox.

import os.path

from casa_distro.image_builder import ImageBuilder


builder = ImageBuilder('casa-run', base='casa-system-ubuntu-22.04.{extension}')


BUILD_FILES = [
    'install_apt_dependencies.sh',
    'build_dependencies.sh',
    'neurodebian.sources.list',
    'neurodebian-key.gpg',
    'pip_constraints.txt',
    'install_pip_dependencies.sh',
    'install_compiled_dependencies.sh',
    'cleanup_build_dependencies.sh',
    'build_sip_pyqt.sh',
]
"""List of files that are copied into /build and removed when done."""


@builder.step
def mount_points(base_dir, builder):
    """Create /casa and other mount points."""
    # Mount points must exist in the image for Singularity to be able to use
    # them when the --writable option is used (e.g. with a sandbox image).
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
def copy_build_files(base_dir, builder):
    """Copy files that are necessary for building the image."""
    builder.run_root('if [ ! -e /build ]; then mkdir /build; fi')
    for f in BUILD_FILES:
        # /build is used instead of /tmp here because /tmp can be bind-mounted
        # during build on Singularity (and the copied files are hidden by this
        # mount).
        builder.copy_root(os.path.join(base_dir, f), '/build')
    builder.run_root('chmod +x /build/*.sh')

    builder.copy_user(os.path.join(base_dir, 'environment.sh'),
                      '/casa')
    builder.run_user('chmod a+rx /casa/environment.sh')
    builder.run_user('echo "{\\"image_id\\": \\"%s\\", '
                     '\\"image_version\\": \\"%s\\"}"'
                     ' > /casa/image_id' % (builder.image_id,
                                            builder.image_version))

    builder.copy_user(os.path.join(base_dir, 'bashrc'),
                      '/casa')
    builder.copy_root(os.path.join(base_dir, 'entrypoint'),
                      '/usr/local/bin/')
    builder.run_root('chmod a+rx /usr/local/bin/entrypoint')


@builder.step
def apt_dependencies(base_dir, builder):
    """Run install_apt_dependencies.sh."""
    builder.run_root('/build/install_apt_dependencies.sh')


@builder.step
def pip_dependencies(base_dir, builder):
    """Run install_pip_dependencies.sh."""
    builder.run_root('/build/install_pip_dependencies.sh')


@builder.step
def compiled_dependencies(base_dir, builder):
    """Run install_compiled_dependencies.sh."""
    builder.run_root('/build/install_compiled_dependencies.sh')


@builder.step
def cleanup_build_dependencies(base_dir, builder):
    """Run cleanup_build_dependencies.sh."""
    builder.run_root('/build/cleanup_build_dependencies.sh')


@builder.step
def cleanup_files(base_dir, builder):
    """Clean up build files."""
    builder.run_root('rm -rf /build')
