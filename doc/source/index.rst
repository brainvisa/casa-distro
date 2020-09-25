===========
Casa-Distro
===========

This page contains mainly informations for developpers.

If you want to install simply casa-distro as a user, you can see :doc:`Quickstart page <quickstart>`


Overview
========

What is CASA ?
--------------

CASA = `CATI <http://cati-neuroimaging.com>`_ + `BrainVISA <http://brainvisa.info>`_

When these two projects decided to use the same development and software delivery environment, the name CASA was chosen to name this environment.

What is Casa-Distro ?
---------------------

**Short answer:** it's the way to run or develop BrainVISA software in a containerized environment or a virtual machine.

**Longer answer:**

It's a cross-platform environment which is used by users to install/use BrainVisa and CATI environments, and by developers to provide a common working development environment for BrainVISA and CATI tools. It avoids the manual installation of required development software and libraries, which can cause the use of different versions on different systems.
It was not unusual to discover differences of behaviour in software that was only due to diferrences between developpement environments. The more developpers were involved in the projects, the more difficulties were encoutered. It was become too difficult to maintain good quality software without a unified development environment.

Therefore, it was decided to create casa-distro to provide a complete development environment using a virtual applicance to host the compilation system. casa_distro supports two container technologies, `Singularity <https://www.sylabs.io/>`_ and `Docker <https://www.docker.com>`_ and one virtual machine technology : `VirtualBox <https://www.virtualbox.org/>`_.

**Note**: in version 3.0 the support for Docker has been temporarily dropped (but should come back as soon as possible).

.. role:: grey

+----------+-------------------------------------------+---------------+-----------------------------------------+
|          | Singularity                               | Docker        | VirtualBox                              |
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

See the :doc:`Quickstart page <quickstart>` for installation instructions.

The containerization allows to have a single binary distribution for all host operating systems and versions.

Once installed, a user can add to his account configuration ``PATH`` environment variable the ``host_bin`` directory of the installed *envrironment*.

Unix bash shells (in ``$HOME/.bashrc`` for instance):

.. code-block:: bash

    export PATH="/home/user/casa_distro/brainvisa-5.0/host/host_bin:$PATH"

This makes the ``bv`` command, and "shortcuts" to all executable commands of the BrainVISA distribution, available. ``bv`` allows to run the container and programs in the container, and handles all needed configuration.

As programs are actually running in a container or a virtual machine (transparently), the user may have to configure additional mount points to actually see his data and working directories from his host machine in the container. This is done graphically, simply using:

.. code-block:: bash

    bv

``bv`` can also be used to run all programs in the container:

.. code-block:: bash

    bv AimsFileInfo -h
    bv anatomist
    bv brainvisa

or to open an interactive shell in the container:

.. code-block:: bash

    bv shell

More options may be used. :doc:`See the complete documentation of the bv command <bv_command>`.


Casa-Distro for developers
==========================

.. Casa-distro project is the metronome and swiss knife for the management of compilation and publication of CASA software distributions. It contains all tools to create and publish the virtual images as well as tools for the management of the whole distro creation pipeline (configuration source retrieval, compilation, packaging, publication, etc.).

.. Use cases
.. ---------

..   * I develop toolboxes, I need to build and release them as binary compatible with the official BrainVisa distrtibutions
..   * I am a contributor of Cati/BrainVisa environment, and need to get started quickly
..   * I am release maintainer of BrainVisa and need to produce a new release yesterday


What Casa-Distro is **not**
---------------------------

* Casa-Distro is not a build sytem: this is the job of :bv-cmake:`BrainVisa-Cmake <index.html>`. Casa-distro brings a wrapper for the build system: it provides Docker images of Linux systems which contain :bv-cmake:`BrainVisa-Cmake <index.html>` and many other thirdparty development tools and libraries, which are already setup for development and distribution of tools.

  The user will be able to use the build system (:bv-cmake:`bv_maker <bv_maker.html>`), inside Docker, in a way that ensures to build, run, and ship software that is compatible with public distributions of BrainVisa.


II - Background: distributions, versions and environments
=========================================================

Software distributions managed by casa-distro are composed of many versioned software components
(more than 50 at the time of this writing). Each one has its own time line for
development and release. BrainVISA team is not big enough to follow the
release of all projects and make sure that good practices are followed
(for instance make sure that the project version is increased whenever
the project source are changed between releases).

Distributions
-------------

casa-distro distributions
+++++++++++++++++++++++++

The casa-distro development :ref:`environment` is composed of two virtual images:

- **run image:** this image is used by end users to execute softwares distributed by BrainVISA and CATI. It is a Linux distribution where all the required system dependencies are already installed. This image is ready to be used with one of the casa-distro software distribution (see below).
- **dev image:** this image is used by developers to build softwares distributed by BrainVISA and CATI. It is based on the run image and adds all dependencies required for building all projects.

These two images are distributed using three technologies:

- [**Docker:** the images are on `Docker Hub <https://hub.docker.com/>`_. They are named `cati/casa-run` and `cati/casa-dev` for the latest release. They are also accessible with their release number. For `instance cati/casa-run:2020.03.06.1`.]
- **Singularity:** the images are on the BrainVISA web site on the following URLs : `<http://brainvisa.info/casa-distro/singularity/>`_.
- **VirtualBox:** the images are on the BrainVISA web site on the following URLs : `<http://brainvisa.info/casa-distro/vbox/>`_.


.. For the image version number it has been chosen to use the date of the begining of the image creation process with the pattern ``<year>.<month>.<day>.<count>`` where :
..
.. -  **<year>:** is the year as four digits number.
.. -  **<month>:** is the month as a two digits number.
.. -  **<day>:** is the day as a two digits number.
.. -  **<count>:** is a number starting at 1 and incremented whenever
..              it is necessary to publish two releases on the same day.


What is a distribution
++++++++++++++++++++++

A distribution (or distro) is a selection of software components that
can be shared with collaborators. All the distro are compiled, tested
and packaged the same way and at the same time. But each distro have its
own software content, targeted audience and license agreement. At the
time of this writing, the following distros are planned to be technically
managed by CASA :

-  **brainvisa**: the historical BrainVISA distribution. It combines
   open source and close source software. It can be downloaded by anyone
   and used freely for non profit research.
-  **cati_platform**: this distro contains the software necessary to
   operate CATI platform. It is managed by CATI and distributed only to
   CATI members.
-  **cea**: this distribution is based on the BrainVISA distribution but
   contains also some toolboxes that are not distributed to the whole
   community. It is installed in several CEA labs : Neurospin, MIRCen
   and SHFJ.



Distribution versioning
+++++++++++++++++++++++

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

.. Distribution creation
.. +++++++++++++++++++++
..
.. The creation of a distribution is a four steps process :
..
.. #. **Create release plan:** selection of the software components that
..    are going to be upgraded in the next release of the distribution.
.. #. **Apply release plan:** update the version of generic branches
..    (*latest\_release*, *bug\_fix* and *trunk*) in the source code of all
..    projects according to the release plan.
.. #. **Compilation, testing and packaging:** creation of environments,
..    tests execution and packages creation for the new distribution.
.. #. **Distribution deployment:** make distributions and packages
..    available for users.
..
.. All these steps are done by CASA admin team using ``casa_distro`` command. The
.. release plan is discussed with distros managers and eventually modified before
.. being applied. The current status of the release plan can be found on a
.. `BioProj wiki page <https://bioproj.extra.cea.fr/redmine/projects/catidev/wiki/Release_plan>`_.

Environment
-----------

An environment represents all what is necessary to work on a distro at
a given version for a given operating system. In ``casa_distro``, an
environment is identified by three variables:

| - **distro:** the identifier of the distro (*e.g.* ``opensource``,
  ``brainvisa``, ``cati`` or ``cea``)
| - **branch:** the name of the virtual branch used to select software
  component sources (``latest_release``, ``master`` or ``integration``).
| - **system:** the operating system the distro is build for (*e.g.*
  ``ubuntu-16.04``, ``ubuntu-18.04``, ``win32`` or ``win64``).

Note that in casa-distro 2, we used to call this environment "build workflow". We changed the name after extending it to user "run" environments which are not designed to build the software but just to use it.

The hardware representation of an environment is a set of directories:

| - **host/conf:** configuration of the environment (config file, BioProj passwords,
  bv\_maker.cfg, etc.). The content of this directory is the input of
  the compilation, packaging and testing steps. There are some
  predefined content for ``conf`` that can be generated with the command
  ``casa_distro setup`` or ``casa_distro setup_dev`` but the whole environment can be customized by editing files in this directory.
| - **host/src:** source of selected components for the workflow. The content
  of this directory is first created by ``bv_maker`` from within a
  Docker container running the targeted operting system. Simply call
  ``casa_distro bv_maker`` for this. The same command can be used to
  update sources to latest revision or to recompile when source code has
  been modified.
| - **host/build:** build directory used for compilation. Like the ``src``
  directory, the content of this directory is created by commands such
  as ``casa_distro bv_maker``.
| - **host/install:** directory containing distribution packages. Packages that
  are created by bv\_maker are stored in that directory.
| - **test:** directory used during testing. Typically reference data
  will be downloaded in this directory and compared to test data
  generated, in this directory, by test commands.


.. _install:

III - Installation and setup
========================================

.. Requirements
.. ------------
..
.. To use Casa-Distro, a user (or rather a developer) must have a system with
.. the following characteristics:
..
.. * Either `Singularity <https://www.sylabs.io/>`_ or
..   `Docker <https://www.docker.com>`_ must be installed and setup for the user
..   on the building system. These container technologies only runs
..   on reasonably recent Linux systems, recent Mac systems, and Windows.
.. * Python >= 2.7 is necessary  run the ``casa_distro`` command.
.. * Git may be used to download casa-distro *the first time you use it* (see later, `Install latest release`_), but generally Python and its ``pip`` command are enough.
..
.. The rest takes place inside containers, so are normally not restructed by the building system, (as long as it has enough memory and disk space).
..
.. Since Casa-Distro 3.0, Singularity >= 3.0 is needed.
.. Singularity v3 is not available as an apt package on Ubuntu, it is necessary to download
.. sources and to compile it.
..
.. It requires Go to be installed.
.. You can follow `Singularity installation instructions <https://sylabs.io/guides/3.6/admin-guide/installation.html#install-from-source>`_
..
.. For more details about installation, setup, and troubleshooting, see

see: :doc:`install_setup`


Install with python
-------------------

Casa_distro is available in the official python package repository `PyPi <https://pypi.org/project/casa-distro/>`_. If python is installed, you can use this command to install casa_distro :

.. code-block:: bash

    pip install casa_distro

Once installed, you can use the casa_distro command in your terminal :

.. code-block:: bash

    casa_distro setup [options]

Install latest release
----------------------

To get the lastest realease you can simply download it from https://github.com/brainvisa/casa-distro, or using git:

.. code-block:: bash

    git clone https://github.com/brainvisa/casa-distro.git /tmp/casa-distro

or by downloading a .zip from the github site using the download button or `clicking this link <https://github.com/brainvisa/casa-distro/archive/master.zip>`_.

Once downloaded, no "install step" is required, you can use the casa_distro command directly:

.. code-block:: bash

    /tmp/casa-distro/bin/casa_distro help

Note that this "initial" install of casa-distro can be temporary, since once an environment is setup, it is possible to use the casa-distro reinstalled in the build-workflow, which will be easier to update and maintain (see the `Update the casa_distro command`_ section to set it up).


Install with brainvisa-cmake
----------------------------

This advanced method can be used by people that are familiar with the use of :bv-cmake:`BrainVisa-Cmake <index.html>`. Casa-distro belong to the standard projects of brainvisa-cmake so in most case, there is no specific modification to do on ``bv_maker.cfg``. casa_distro can be downloaded, configured and built like any other brainvisa-cmake components. Once built, it can be used as other commands compiled by ``bv_maker``. For instance :

.. code-block:: bash

  <path_to_build_dir>/bin/bv_env_host casa_distro --help


.. Retrieve a CASA build
.. =====================
..
.. Images with compiled softwares and tools are available to download. It allows to install ready-to-use softwares without need of compilation. For developper, you can refer to `Building CASA projects`_.
..
.. You can install the default image using this command :
..
.. .. code-block:: bash
..
..   casa_distro setup distro=brainvisa container_type=singularity
..
.. The command will launch the download of the corresponding image. After some minutes (according to your internet connection speed), your environment is ready to use :
..
.. .. code-block:: bash
..
..   casa_distro run brainvisa


Building CASA projects
======================

First time
----------

Casa-distro is pre-setup to handle CATI/BrainVisa open-source projects. In this situation, once casa_distro has been downloaded or installed, a user has to:

* create an environment, which will contain the sources repository for BrainVisa projects, a build directory, etc.

.. code-block:: bash

    python /tmp/casa-distro/bin/casa_distro setup_dev distro=opensource system=ubuntu-18.04 branch=master

This command specifies to setup a developper environment for the open-source projects set (``distro_source=opensource`` is actually the default and can be omitted), for the ``master`` branch (default is ``latest_release``), using a container system based on Ubuntu 18.04.
Directories and files will be created accordingly in the repository directory, here the default is ``$HOME/casa_distro``.
The location of casa-distro container images and environments can be specified either using the ``-r`` option, or the ``base_directory=`` parameter to many sub-commands, or if the environment variable ``CASA_DEFAULT_REPOSITORY`` is set to an appropriate directory.

* build everything

.. code-block:: bash

    python /tmp/casa-distro/bin/casa_distro bv_maker name=opensource-dev-ubuntu-18.04

If name, distro, branch, or system are not provided, all matching environments will be processed.

Additional options can be passed to the underlying :bv-cmake:`bv_maker <index.html>` command, which will run inside the container. Typically, the documentation can be built, testing and packaging can be performed.

Update the casa_distro command
------------------------------

Once an environment has been initialized, and at least source code has been updated (using ``casa_distro bv_maker``), most *distributions* actually include the *casa-distro* project, which will be updated with the rest of the source code. As it is python-only, it can be run from the host system, so it may be a good idea to use this updated ``casa_distro`` command instead of */tmp/casa-distro/bin/casa_distro* which has been downloaded temporarily to initialize the process. This can be done by "updating" a build-workflow (actually any one which contains casa-distro):

.. code-block:: bash

    python /tmp/casa-distro/bin/casa_distro update distro=opensource branch=master system=ubuntu-18.04

Then the run script will use the casa-distro from this source tree.
You can setup your host environment (``$HOME/.bashrc`` typically) to use it by defaul by setting it first in the ``PATH`` environment variable:

.. code-block:: bash

    export PATH="$HOME/casa_distro/opensource-dev-ubuntu-18.04/bin:$PATH"

Here you should of course replace the path ``$HOME/casa_distro/opensource-dev-ubuntu-18.04`` with the environment path listed by the command ``casa_distro list``.

Bash completion
---------------

Bash completion scripts have been developed for ``casa_distro`` and ``bv_maker``. Inside a casa-distro container, these completions are already setup and should be active as soon as environments have been built, and the container is restarted (exit a casa-distro shell and re-run it).
On the host, it is possible to *source* the bash completion scripts. You can set it in your ``$HOME/.bashrc`` file by adding to it:

.. code-block:: bash

    BUILD_WF=$HOME/casa_distro/opensource-dev-ubuntu-18.04
    if [ -f "$BUILD_WF/host/src/development/casa-distro/*/etc/bash_completion.d/casa_distro-completion.bash" ]; then
        . "$BUILD_WF/host/src/development/casa-distro/*/etc/bash_completion.d/casa_distro-completion.bash"
    fi
    if [ -f "$BUILD_WF/host/src/development/brainvisa-cmake/*/etc/bash_completion.d/bv_maker-completion.bash" ]; then
        . "$BUILD_WF/host/src/development/brainvisa-cmake/*/etc/bash_completion.d/bv_maker-completion.bash"
    fi

This completion will help typing the commands and its options by providing possible options and values by typing ``<tab>`` or ``<tab> <tab>`` when typing the command code, which will significantly speed-up working intensively with casa_distro and bv_maker.

Updating projects
-----------------

To update to the most recent versions of the projects sources, and rebuild, it is simply a matter of re-running ``casa_distro bv_maker`` (with corresponding options, if needed).

Customizing projects
--------------------

It is possible to customize the projects list to be retreived and built. It is done by editing the :bv-cmake:`bv_maker.cfg file <configuration.html>` in the environment, which can be found in the directory ``<repository>/<environment>/host/conf/``

where ``<repository>`` is the base casa-distro repository directory (passed as the ``-r`` option of casa_distro if needed), ``<environment>`` is the environment name.


Using Casa-Distro as a runtime environment to run BrainVISA-related software
============================================================================

It's possible to do so:

.. code-block:: bash

    casa_distro run branch=master gui=yes brainvisa

``brainvisa`` could be replaced by any other command (``anatomist``, ``AimsSomething``, ``morphologist``) with parameters.

Note that graphical software need to run the containers with a graphical "bridge": a X server has to be running on the host system, and OpenGL may or may not work. The options ``gui=yes`` and ``opengl`` of casa_distro try to handle common cases (at least on Linux hosts), possibly using Nvidia proprietary OpenGL implementation and drivers from the host system.
Note that the option ``gui=yes`` is now the default, thus it is not needed.

For OpenGL rendering problems may differ between docker and singularity. We tried to handle some of them in the options passed to containers by casa_distro with gui active, but some additional options / tweaking may be helpful. See the :ref:`OpenGL troubleshooting <opengl_troubleshooting>` section for details.

.. warning:: BUT...

    But soma-workflow distributed execution, in its current released version, will not spawn Docker or Singularity (or casa_distro run) in remote processing. We have made modifications in the `github/master branch <https://github.com/neurospin/soma-workflow>`_ (which is included in brainvisa/bug_fix branches) to add support for it. However it needs some additional configuration on server side to specify how to run the containers.

Remember that software run that way live in a container, which is more or less isolated from the host system. To access data, casa_distro will likeky need additional directories mount options. It can be specified on ``casa_distro`` commandline, or in the file ``container_options`` item in ``<casa_distro_environment>/host/conf/casa_distro.json``.


:doc:`concepts`
===============

.. toctree::

    concepts


:doc:`bv_command`
=================

.. toctree::

    bv_command


:doc:`casa_distro_command`
==========================

.. toctree::

    casa_distro_command


:doc:`casa_distro_admin_command`
================================

.. toctree::

    casa_distro_admin_command


:doc:`install_setup`
====================

.. toctree::

    install_setup


:doc:`quickstart`
=================

.. toctree::

    quickstart
