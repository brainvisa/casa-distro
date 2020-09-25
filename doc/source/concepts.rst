====================
Casa-distro concepts
====================

.. |bv| replace:: BrainVISA_

.. _BrainVISA: http://brainvisa.info

.. _repository:

repository
==========

The *repository* is the root directory for all casa-distro files. It contains :ref:`container images <image>` and :ref:`environments <environment>`.


.. _environment:

environment
===========

An *environment* is a workspace, directory and associated container image(s), containing a user installation of the applications (|bv| software) or a developer build (sources and build).

It represents all what is necessary to work on a :ref:`distro` at
a given version for a given operating system. In ``casa_distro``, an
environment is identified by several variables:

| - :ref:`name <env_name>`
| - :ref:`type <env_type>`
| - :ref:`distro`
| - :ref:`branch`
| - :ref:`system`
| - :ref:`version`

Note that in casa-distro 2, we used to call this environment "*build workflow*". We changed the name after extending it to user "run" environments which are not designed to build the software but just to use it.

An environment is based on an :ref:`image` located at the :ref:`repository` level. In some situations (developer environments with tests, release building) several :ref:`images <image>` may be used within a single environment.

The hardware representation of an environment is a set of directories in the :ref:`repository`, under the sub-directory named after th :ref:`env_name`:

* For a **user environment**:

  | - **host/conf:** configuration of the environment (config file, etc.). There are some predefined content for ``conf`` that can be generated with the command ``casa_distro setup`` but the whole environment can be customized by editing files in this directory.
  | - **host/home:** a "home directory" for the user inside the casa-distro container of the environment. This is separated from the host home directory because as it is a container, the configuration here may differ from the host one, and cause confusions and incompatibilities.
  | - **host/host_bin:** directory containing run scripts for all |bv| executable programs, and also the :doc:`bv_command`. Programs here are meant to be run from the *host machine*, not from within the container. This directory can safely be setup in the host system ``PATH`` environment variable.
  | - **host/python:** contains the python modules needed to run the :doc:`bv_command` on the *host machine* side.
  | - **install:** the |bv| distribution directory. This directory is actually in the container image, and is not visible from the host machine.

* for a **developer environment**:

  | - **host/conf:** configuration of the environment (config file, BioProj passwords, ``bv_maker.cfg``, etc.). The content of this directory is the input of the compilation, packaging and testing steps. There are some predefined content for ``conf`` that can be generated with the command ``casa_distro setup_dev`` but the whole environment can be customized by editing files in this directory.
  | - **host/home:** a "home directory" for the user inside the casa-distro container of the environment. This is separated from the host home directory because as it is a container, the configuration here may differ from the host one, and cause confusions and incompatibilities.
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


.. _env_type:

environment type
================

There are two environment types:
* ``user``: the environment is an installation of a ready-to-run, precompiled |bv| distribution in a container image. It is designed for users who just need to run the software.
* ``dev``: the environment is a developer environment, it is using a container image containing all development tools, and will hold source code and compilation files.


.. _env_name:

environment name
================

 Identifier for the :ref:`environment`. The *name* has to be unique in a :ref:`repository` and can be used as a shortcut to select a specific environment, once setup and installed: it can replace :ref:`distro`, :ref:`branch`, :ref:`version`, :ref:`system` and :ref:`type <env_type>` to select an existing environment.


 .. _distro:

distro
======

The identifier of the *distro*. It represents a set of software handled (installed or built) in the :ref:`environment`. There are a few predefined *distro* in cqsq-distro:

* ``opensource``: brainvisa projects subset which are fully open-source and don't need a personal login/password to access the sources repositories. The contain the core libraries and software infrastructure (Aims, Anatomist, Axon, Soma-Workflow, Capsul, and more)
* ``brainvisa``: all |bv| public distribution
* ``cati``
* ``cea``: complete |bv| components, including internal (non-publicly distributed) components


.. _system:

system
======

the operating system the :ref:`distro` is built for (*e.g.* ``ubuntu-18.04``, ``ubuntu-20.04``, we used to have also ``win32`` or ``win64``).


.. _branch:

branch
======

The name of the virtual :ref:`branch` used to select software component sources (``latest_release``, ``master`` or ``integration``) in an :ref:`environment`. This variable is only used in *developer environments*, when *user environments* use :ref:`version` instead.


.. _version:

version
=======

The version of the user distribution of |bv|.

.. _image:

image
=====

Container image file, located in the :ref:`repository`. Casa-distro can use Singularity images (``.sif`` or ``.simg`` files), Docker images (located in the docker images repository, not in Casa-distro repository directory), or VirtualBox images (``.vdi`` or ``.ova`` files).

An images may be of three types:
* **user image:** user-oriented, it contains a full system with |bv| already installed in it.
* **dev image:** developer-oriented, it contains a system with all needed development tools, but not the |bv| software which are meant to be built by the developer, in the :ref:`environment` but outside of the image.
* **run image:** normally not used by users nor by developers, but used by distribution maintainers to build a |bv| release (user image): it contains a system with the needed runtime third-party libraries and modules required to run the |bv| software. It is thus lighter than the corresponding dev image. A user image is a run image with |bv| additionally installed in it.
