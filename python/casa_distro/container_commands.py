# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

import os
# from casa_distro import six
from casa_distro.command import command, check_boolean
from casa_distro.container_environment import (setup_user as env_setup_user,
                                               setup_dev as env_setup_dev)


@command
def setup_user(dir='/casa/setup', rw_install=False,
               shared_install=False, distro=None,
               version=os.environ.get('CASA_VERSION'),
               url='https://brainvisa.info/download'):
    """
    Create all necessary directories and files to setup a user environment.

    This command is not supposed to be called directly but using a user image::

        mkdir ~/brainvisa
        cd ~/brainvisa
        singularity run -c --bind .:/casa/setup brainvisa-5.0.sif

    Parameters
    ----------

    dir
        dir={dir_default}
        Target environment directory

    rw_install
        {rw_install_default}
        if true, install in a read-write directory /casa/host/install in the
        container but on the host filesystem. This install allows to add
        external toolboxes on top of the standard BrainVisa install

    shared_install
        {shared_install_default}
        if true, the creation of /casa/host/home will be skipped. This is
        appropriate for an install shared among multiple users, who will then
        each have their own home directory stored under
        ~/.local/share/casa-distro

    distro
        {distro_default}
        if specified, the install will download the BrainVisa distro from the
        web site, and install it in a writable directory /casa/host/install in
        the container, like with the rw_install mode above.

    version
        {version_default}
        version of the Brainvisa distribution to be downloaded (for use with
        the distro option).

    url
        {url_default}
        download URL for use with the distro option.
    """
    rw_install = check_boolean('rw_install', rw_install)
    env_setup_user(dir, rw_install=rw_install,
                   create_homedir=not shared_install,
                   distro=distro, version=version,
                   url=url)


@command
def setup_dev(distro, branch='master', system=None, image_version=None,
              dir='/casa/setup', name=None):
    """
    Create all necessary directories and files to setup a developer
    environment.

    This command is not supposed to be called directly but using a casa-dev
    image::

        mkdir -p ~/casa_distro/brainvisa-master
        cd ~/casa_distro
        singularity run -c -B \\
            ./brainvisa-master:/casa/setup casa-dev-ubuntu-18.04.sif \\
            brainvisa master

    Parameters
    ----------

    {distro}
    {branch}
    {system}
    {image_version}
    dir
        dir={dir_default}
        Target environment directory
    {name}
    """
    env_setup_dev(dir, distro=distro, branch=branch, system=system,
                  image_version=image_version, name=name)


@command
def config_gui():
    """
    """
    from casa_distro import configuration_gui

    configuration_gui.main_gui()
