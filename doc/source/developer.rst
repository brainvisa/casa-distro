===================================================
Developing in the Casa-Distro BrainVISA environment
===================================================

.. Casa-distro project is the metronome and swiss knife for the management of compilation and publication of CASA software distributions. It contains all tools to create and publish the virtual images as well as tools for the management of the whole distro creation pipeline (configuration source retrieval, compilation, packaging, publication, etc.).

.. Use cases
.. ---------

..   * I develop toolboxes, I need to build and release them as binary compatible with the official BrainVisa distrtibutions
..   * I am a contributor of Cati/BrainVisa environment, and need to get started quickly
..   * I am release maintainer of BrainVisa and need to produce a new release yesterday


Installation and setup
======================

.. highlight:: bash

* The :bv:`BrainVisa download / install section <download.html>` explains how to install both a released, compiled, version of BrainVISA (This is what a "regular user" needs), or a developer environment which will build from sources.

* Alternatively it is possible to install Casa-Distro from its sources on GitHub. To get the latest release you can simply download it from https://github.com/brainvisa/casa-distro, using  the ``git`` command::

    git clone https://github.com/brainvisa/casa-distro.git /tmp/casa-distro

  Once downloaded, no "install step" is required, you can use the casa_distro command directly::

    /tmp/casa-distro/bin/casa_distro help

Casa-distro is pre-setup to handle CATI/BrainVisa open-source projects. In this situation, once casa-distro has been downloaded or installed, a user has to follow the next steps:


Building CASA projects
======================

First time
----------

* Developers will need access to source and development tools. Thus instead of installing a "user" release of BrainVISA using the ``casa_distro setup`` command, they will rather install a developer image and setup. This is done (once casa-distro is installed) using the command ``casa_distro setup_dev``::

      casa_distro setup_dev system=ubuntu-18.04 distro=brainvisa branch=master

  This will setup an :ref:`environment` dedicated to development.

  This command specifies to setup a developer :ref:`environment` for the open-source projects set (``distro_source=opensource`` is actually the default and can be omitted), for the ``master`` branch (default is ``latest_release``), using a container system based on Ubuntu 18.04.

  Directories and files will be created accordingly in the :REF:`repository` directory (location of casa-distro container images and :ref:`environments <environment>`), here the default is ``$HOME/casa_distro``.

  The location of casa-distro :ref:`repository` can be specified either using the ``base_directory=`` parameter to many sub-commands, or if the environment variable ``CASA_DEFAULT_REPOSITORY`` is set to an appropriate directory.

  Such an :ref:`environment` will use source code from BrainVisa code repositories (partly on https://github.com and partly on https://bioproj.extra.cea.fr). The code needs to be downloaded and built using a build system: :bv-cmake:`bv_maker <index.html>`

* Setup credentials for source code reposotories

  This step is optional and is especially not need if just retrieving only the open-source projects.
  The file ``svn.secret`` may be created / edited to store login / password information for the svn `BioProj <http://bioproj.extra.cea.fr>`_ server. If not filled, the ``svn`` program will ask for them interactively, and propose to store them.

* build everything::

      casa_distro bv_maker name=opensource-dev-ubuntu-18.04

  If :ref:`name <env_name>`, :ref:`distro`, :ref:`branch`, or :ref:`system` are not provided, all matching :ref:`environments <environment>` will be processed.

  Additional options can be passed to the underlying :bv-cmake:`bv_maker <index.html>` command, which will run inside the container. Typically, the documentation can be built, testing and packaging can be performed.

Update the casa_distro command
------------------------------

Once an environment has been initialized, and at least source code has been updated (using ``casa_distro bv_maker``), most :ref:`distributions <distro>` actually include the *casa-distro* project, which will be updated with the rest of the source code. As it is python-only, it can be run from the host system (if stored on the host filesystem), so it may be a good idea to use this updated ``casa_distro`` command instead of the oned previously installed (either via pip or from `github <https://github.com>`_ sources) to initialize the process.

.. This can be done by "updating" a build-workflow (actually any one which contains casa-distro):
..
.. .. code-block:: bash
..
..     python /tmp/casa-distro/bin/casa_distro update distro=opensource branch=master system=ubuntu-18.04
..
.. Then the run script will use the casa-distro from this source tree.
.. You can setup your host environment (``$HOME/.bashrc`` typically) to use it by default by setting it first in the ``PATH`` environment variable:
..
.. .. code-block:: bash
..
..     export PATH="$HOME/casa_distro/opensource-dev-ubuntu-18.04/bin:$PATH"
..
.. Here you should of course replace the path ``$HOME/casa_distro/opensource-dev-ubuntu-18.04`` with the environment path listed by the command ``casa_distro list``.

Bash completion
---------------

Bash completion scripts have been developed for ``casa_distro`` and ``bv_maker``. Inside a casa-distro container, these completions are already setup and should be active as soon as environments have been built, and the container is restarted (exit a casa-distro shell and re-run it).
On the host, it is possible to *source* the bash completion scripts. You can set it in your ``$HOME/.bashrc`` file by adding to it::

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

It is possible to customize the projects list to be retrieved and built. It is done by editing the :bv-cmake:`bv_maker.cfg file <configuration.html>` in the environment, which can be found in the directory ``<repository>/<environment>/host/conf/``

where ``<repository>`` is the base casa-distro :ref:`repository` directory (passed as the ``base_directory`` option of casa_distro if needed), ``<environment>`` is the :ref:`environment` :ref:`env_name`.


Casa-Distro  concepts
=====================

The :doc:`concepts` document shows the vocabulary used to describe the elements of Casa-Distro.


Administration
==============

What we call "administration" in Casa-Distro is handling tools to build a new (BrainVISA) release, to build new images, not just developing code. This part is the job of :doc:`casa_distro_admin_command`.
