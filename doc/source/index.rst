===========
Casa-Distro
===========

Overview
========

What is CASA ?
--------------

CASA = `CATI <http://cati-neuroimaging.com>`_ + `BrainVISA <http://brainvisa.info>`_

What is Casa-Distro ?
---------------------

It's a development environment which helps to provide developers with a working development environment for BrainVisa and CATI tools.

It provides `Docker images <https://www.docker.com>`_ images compatible with BrainVisa distributions with all needed setup to build custom toolboxes, package them, and distribute them, in the same environment.

Casa-distro is the metronome and swiss knife for the management of compilation and publication of CASA software distributions. It is a metronome because the distribution procedures, and especially the distribution frequency, is defined in casa-distro documentation (`bioproj wiki <https://bioproj.extra.cea.fr/redmine/projects/catidev/wiki/Casa-distro>`_). It is a swiss knife because it provides a tool for the management of the whole distro creation pipeline (configuration source retrieval, compilation, packaging, publication, etc.).

Use cases
---------

* I develop toolboxes, I need to build and release them as binary compatible with the official BrainVisa distrtibutions
* I am a contributor of Cati/BrainVisa environment, and need to get started quickly
* I am release maintainer of BrainVisa and need to produce a new release yesterday


What Casa-Distro is **not**
---------------------------

* Casa-Distro is not a build sytem: this is the job of :bv-cmake:`BrainVisa-Cmake <index.html>`. Casa-distro brings a wrapper for the build system: it provides Docker images of Linux systems which contain :bv-cmake:`BrainVisa-Cmake <index.html>` and many other thirdparty development tools and libraries, which are already setup for development and distribution of tools.

  The user will be able to use the build system (:bv-cmake:`bv_maker <bv_maker.html>`), inside Docker, in a way that ensures to build, run, and ship software that is compatible with public distributions of BrainVisa.

* Casa-Distro is not a binary distribution of BrainVisa. Even if it could be used that way. Binary distributions provide binaries that try to work on the wider possible variety of systems. Casa-distro is one (or a small set) of these systems with developemnt, distribution, and run environment.


Install and setup
=================

Requirements
------------

To use Casa-Distro, a user (or rather a developer) must have a system with the following characteristics:

* A system which supports Docker: `Docker <https://www.docker.com>`_ only runs on reasonably recent Linux systems, recent Mac systems, and Windows.
* Administrator permissions on the machine: Docker can only be used by users with advanced permissions, as it allows to change user and write files on the host system with any user identity.
* `Docker <https://www.docker.com>`_ muste be installed and setup for the user on the host system.
* Python >= 2.7 to run the ``casa_distro`` command on the host system.

The rest takes place inside Docker containers, so are normally not restricted by the host system, (as long as it has enough memory and disk space).

* To run graphical software, a X server and OpenGL have to be running on the host system (unless a virtual X/VNC solution is used)


Install
-------

* get casa_distro.zip
* run casa_distro or casa_distro.zip


Management of source code, branches, build directories and packages
===================================================================

Working with docker
===================

Next release
============

Using Casa-Distro as a runtime environment to run BrainVisa-related software
============================================================================

It's possible to do so:

.. code-block:: bash

    casa_distro -r /home/me/casa run branch=bug_fix X=1 brainvisa

``brainvisa`` could be replaced by any other command (``anatomist``, ``AimsSomething``, ``morphologist``) with parameters.

Note that graphical software need to run Docker containers with a graphical "bridge": a X server has to be running on the host system, and OpenGL may or may not work. The option ``X=1`` of casa_distro tries to handle common cases (at least on Linux hosts), possibly using Nvidia proprietary OpenGL implementation and drivers from the host system.

.. warning:: BUT...

    But soma-workflow distributed execution will not spawn Docker (or casa_distro run) in remote processing. Modifications could be done to handle it.

Remember that software run that way live in a Docker container, which is more or less isolated from the host system. To access data, it casa_distro will likeky need additional directories mount options. It can be specified on ``casa_distro`` commandline, or in the DOCKER_OPTIONS variable of the script ``docker_options`` found in ``<casa_distro_build_workflow>/conf/docker_options``.

