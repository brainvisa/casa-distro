===========
Casa-Distro
===========

I - Overview
============

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


II - Background: distributions, versions and build workflows.
=============================================================

Casa-distro is composed of many versioned software components (more than
50 at the time of this writing). Each one has its own time line for
development and release. Casa team is not big enough to follow the
release of all projects and make sure that good practices are followed
(for instance make sure that the project version is increased whenever
the project source are changed between releases). It was therefore
decided to schedule casa-distro versions at a frequency that is
independent of project versions. This **distribution frequency** is a
fundamental element of casa-distro; every first monday of each month, a
**distribution** is created. The creation of a distribution is a series
of steps that leads to the creation of **build workflows** and
**packages**. Build workflows are all the directories used by developers
who need to create or modify software. Packages are single file archives 
used to distribute all the component of a distro to end users.

Distributions
-------------

A distribution (or distro) is a selection of software components that
can be shared with collaborators. All the distro are compiled, tested
and packaged the same way and at the same time. But each distro have its 
own software content, targeted audience and license agreement. At the 
time of this writing, the following distros are planned to be technically 
managed by CASA :

-  **brainvisa**: the historical BrainVISA distribution. It combines
   open source and close source software. It can be downloaded by anyone
   and used freely for non profit research.
-  **cati**: this distro contains the sowtware necessary to operate CATI
   platform. It is managed by CATI and distributed only to CATI members.
-  **cea**: this distribution is based on the BrainVISA distribution but
   contains also some toolboxes that are not distributed to the whole
   community. It is installed in several CEA labs : Neurospin, MIRCen
   and SHFJ.

Distribution frequency
----------------------

A distribution is created every first monday of each month. Normally,
any modification done after a distribution must wait for the next
distribution to be released. However, in case of emergency, it is
possible to add exceptional distributions.

Distribution versioning
-----------------------

It has been chosen to use a classical version numbering convention :
``<major>.<minor>.<patch>`` where :

-  **<major>:** is a number that is increased whenever a major
   modification is done on significant components inducing an
   incompatibility with latest distribution.
-  **<minor>:** is a number that is increased whenever important
   features or modifications are done but without introducing
   incompatibilities.
-  **<patch>:** is a number that is increased whenever routine
   modifications are done.

Distribution creation
---------------------

The creation of a distribution is a three steps process :

#. **Create release plan:** selection of the software components that
   are going to be upgraded in the next release of the distribution.
#. **Apply release plan:** update the version of generic branches
   (*latest\_release*, *bug\_fix* and *trunk*) in the source code of all
   projects according to the release plan.
#. **Compilation, testing and packaging:** creation of build workflows,
   tests execution and packages creation for the new distribution.
#. **Distribution deployment:** make build workflows and packages
   available for users.

All these steps are done by CASA admin team using ``casa_distro`` command. The
release plan is discussed with distros managers and eventually modified before being applied. The current status of the release plan can be found on a `BioProj wiki page <https://bioproj.extra.cea.fr/redmine/projects/catidev/wiki/Release_plan>`_. 

Build workflow
--------------

A build workflow represent all what is necessary to work on a distro at
a given version for a given operating system. In ``casa_distro``, a
build workflow is identified by three variables:

| - **distro:** the identifier of the distro (*e.g.* ``brainvisa``,
  ``cati`` or ``cea``)
| - **branch:** the name of the virtual branch used to select sofware
  component sources (``latest_release``, ``bug_fix`` or ``trunk``).
| - **system:** the operating system the distro is build for (*e.g.*
  ``ubuntu-12.04``, ``ubuntu-16.04``, ``win32`` or ``win64``).

The hardware representation of a build workflow is a set of directories
:

| - **conf:** configuration of the build workflow (BioProj passwords,
  bv\_maker.cfg, etc.). The content of this directory is the input of
  the compilation, packaging and testing steps. There are some
  predefined content for ``conf`` that can be generated with command
  ``casa_distro create_build_workflow`` but the whole build workflow can
  be customized by editing files in this directory.
| - **src:** source of selected components for the workflow. The content
  of this directory is first created by ``bv_maker`` from within a
  Docker container running the targeted operting system. Simply call
  ``casa_distro bv_maker`` for this. The same command can be used to
  update sources to latest revision or to recompile when source code has
  been modified.
| - **build:** build directory used for compilation. Like the ``src``
  directory, the content of this directory is created by commands such
  as ``casa_distro bv_maker``.
| - **pack:** directory containing distribution packages. Packages that
  are created by bv\_maker are stored in that directory.
| - **test:** directory used during testing. Typically reference data
  will be downloaded in this directory and compared to test data
  generated, in this directory, by test commands.


III - casa_distro installation and setup
========================================

Requirements
------------

To use Casa-Distro, a user (or rather a developer) must have a system with the following characteristics:

* A system which supports Docker: `Docker <https://www.docker.com>`_ only runs on reasonably recent Linux systems, recent Mac systems, and Windows.
* Administrator permissions on the machine: Docker can only be used by users with advanced permissions, as it allows to change user and write files on the host system with any user identity.
* `Docker <https://www.docker.com>`_ muste be installed and setup for the user on the host system.
* Python >= 2.7 to run the ``casa_distro`` command on the host system.

The rest takes place inside Docker containers, so are normally not restricted by the host system, (as long as it has enough memory and disk space).

* To run graphical software, a X server and OpenGL have to be running on the host system (unless a virtual X/VNC solution is used)

On Debian based Linux systems (such as Ubuntu), the following packages must be installed :

.. code-block:: bash

  sudo apt-get install python docker.io

On these systems, after ``docker.io`` installation, it is necessary for a user to be in the ``docker`` system group to be able to use Docker. For administrators who need to use release plan files, the package ``python-yaml`` must also be installed.

Install latest release
----------------------

This is the simplest and the only recommended way to use casa_distro. Simply download the latest release with the following link : `http://brainvisa.info/casa_distro/casa_distro.zip <http://brainvisa.info/casa_distro/casa_distro.zip>`_.

Then, provided that Python is installed on your system, you can use casa_distro.zip directly. For instance, to get the help of the command, do:

.. code-block:: bash

  python casa_distro.zip --help

Install from sources
--------------------

This advanced method can be used by people that are familiar with the use of :bv-cmake:`BrainVisa-Cmake <index.html>`. Casa-distro belong to the standard projects of brainvisa-cmake so in most case, there is no specific modification to do on ``bv_maker.cfg``. casa_distro can be downloaded, configured and build like any other brainvisa-cmake components. Once build, it can be used as other commands compiled by ``bv_maker``. For instance :

.. code-block:: bash

  <path_to_build_dir>/bin/bv_env_host casa_distro --help


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


:doc:`casa_distro_command`
==========================

.. toctree::

    casa_distro_command


