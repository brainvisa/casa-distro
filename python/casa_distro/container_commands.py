# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

# from casa_distro import six
from casa_distro.command import command
from casa_distro.environment import (setup_user as env_setup_user,
                                     setup_dev as env_setup_dev)


@command
def setup_user(dir='/casa/setup'):
    """
    Create all necessary directories and files to setup a user environement.

    This command is not supposed to be called directly but using a user image::

        mkdir ~/brainvisa
        cd ~/brainvisa
        singularity run --bind .:/casa/setup brainvisa-5.0.sif

    Parameters
    ----------

    dir
        dir={dir_default}
        Target environment directory
    """
    env_setup_user(dir)


@command
def setup_dev(distro, branch='master', system=None, dir='/casa/setup',
              name=None):
    """
    Create all necessary directories and files to setup a developer
    environment.

    This command is not supposed to be called directly but using a casa-dev
    image::

        mkdir -p ~/casa_distro/brainvisa-master
        cd ~/casa_distro
        singularity run -B \\
            ./brainvisa-master:/casa/setup casa-dev-ubuntu-18.04.sif \\
            brainvisa master

    Parameters
    ----------

    {distro}
    {branch}
    {system}
    dir
        dir={dir_default}
        Target environment directory
    {name}
    """
    env_setup_dev(dir, distro, branch, system, name=name)


@command
def config_gui():
    """
    """
    from casa_distro import configuration_gui

    configuration_gui.main_gui()
