===========
Casa-Distro
===========

If you want to install simply casa-distro as a user, you can directly see the :bv:`BrainVisa download / install section <download.html>`.


Overview
========

What is CASA ?
--------------

CASA = `CATI <http://cati-neuroimaging.com>`_ + `BrainVISA <http://brainvisa.info>`_

When these two projects decided to use the same development and software delivery environment, the name CASA was chosen to name this environment.

What is Casa-Distro ?
---------------------

**Short answer:** it's the way to **run or develop BrainVISA software** in a containerized environment or a virtual machine.

**Longer answer:**

It's a cross-platform environment which is used by users to install/use BrainVisa and CATI environments, and by developers to provide a common working development environment for BrainVISA and CATI tools. It avoids the manual installation of required development software and libraries, which can cause the use of different versions on different systems.
It was not unusual to discover differences of behaviour in software that was only due to diferrences between developpement environments. The more developpers were involved in the projects, the more difficulties were encoutered. It was become too difficult to maintain good quality software without a unified development environment.

Therefore, it was decided to create casa-distro to provide a complete development environment using a virtual applicance to host the compilation system. casa_distro will support two container technologies, `Singularity <https://www.sylabs.io/>`_ and `Docker <https://www.docker.com>`_ (soon) and one virtual machine technology : `VirtualBox <https://www.virtualbox.org/>`_.

**Note**: in version 3.0 the support for Docker has been temporarily dropped (but should come back as soon as possible).

.. role:: grey

+----------+-------------------------------------------+---------------+-----------------------------------------+
|          | Singularity (version 3.x)                 | Docker        | VirtualBox                              |
+----------+-------------------------------------------+---------------+-----------------------------------------+
| Linux    | ✓                                         | :grey:`X`     | ✓                                       |
+----------+-------------------------------------------+---------------+-----------------------------------------+
| Windows  | (✓ :ref:`(1) <win_sing_troubleshooting>`) | :grey:`\(X\)` | ✓                                       |
+----------+-------------------------------------------+---------------+-----------------------------------------+
| Mac OS   | ✓ :ref:`(2) <mac_sing_troubleshooting>`   | :grey:`\(X\)` | ✓ :ref:`(3) <mac_vbox_troubleshooting>` |
+----------+-------------------------------------------+---------------+-----------------------------------------+


Casa-Distro for users
=====================

Users will use Casa-Distro to install and run `BrainVISA <http://brainvisa.info>`_ software.

See the :bv:`BrainVisa download / install section <download.html>` explains how to install it.

The containerization allows to have a single binary distribution for all host operating systems and versions.


Casa-Distro for developers
==========================

What Casa-Distro is **not**
---------------------------

Casa-Distro is not a build sytem: this is the job of :bv-cmake:`BrainVisa-Cmake <index.html>`. Casa-distro brings a wrapper for the build system: it provides Docker images of Linux systems which contain :bv-cmake:`BrainVisa-Cmake <index.html>` and many other thirdparty development tools and libraries, which are already setup for development and distribution of tools.

The user will be able to use the build system (:bv-cmake:`bv_maker <bv_maker.html>`), inside Singularity, Docker, or VirtualBox, in a way that ensures to build, run, and ship software that is compatible with public distributions of BrainVisa.

See the :doc:`developer` documentation.

.. _install:

Installation and setup
======================

Follow roughly the same procedure as for user setup, as axplained in: :bv:`BrainVisa download / install section <download.html#developers-install>`.


3 main commands
===============

:doc:`bv_command`
-----------------

:doc:`bv_command` is the lightest, user-oriented command in casa-distro. It supports a single :ref:`environment` and allows the minimum required to configure and run commands (or open a shell) in an installed environment container.

:doc:`casa_distro_command`
--------------------------

:doc:`casa_distro_command` supports multiple :ref:`environments <environment>` using selection parameters (see :doc:`concepts`) and allows also to run commands insde containers, but also to setup / install, manage, delete :ref:`environments <environment>` and :ref:`container images <image>`.

:doc:`casa_distro_admin_command`
--------------------------------

:doc:`casa_distro_admin_command` is used to create new container images and publish them on a web server for other users.


Contents
========

.. toctree::

    concepts
    technical
    developer
    bv_command
    casa_distro_command
    casa_distro_admin_command
    bbi_daily
