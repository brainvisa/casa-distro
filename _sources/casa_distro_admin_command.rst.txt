=============================
The casa_distro_admin command
=============================

Creation and publication of casa-distro releases and container images.

.. include:: casa_distro_admin_command_help.rst


Images and releases creation
============================

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


A casa-distro release is done by a member of the BrainVISA team using the ``casa_distro_admin`` command. This document contains all the steps that are necessary to build and publish all versions of casa-distro images.

Creation a base VirtualBox image
================================

The base VirtualBox image is a minimal configuration of a system image downloaded from internet as an *.iso file. It serves as starting point for the building of run and dev images. Once created, the image is published on BrainVISA website in the following URL `<http://brainvisa.info/casa-distro/casa-<iso_name>.ova>`_ where `<iso name>̀ is the name of the *.iso file of the distribution. For instance if one uses `ubuntu-18.04.4-desktop-amd64.iso`, the uploaded image name would be `casa-ubuntu-18.04.4-desktop-amd64.ova`.

1) Install VirtualBox version 6 or greater
2) Download an Ubuntu iso file from internet (any Debian based distro may work but only recent Ubuntu LTS are tested).
3) Run `casa_distro_admin create_system` to create an empty VirtualBox image with appropriate base settings (e.g. enough maximum disk size)
4) Perform Ubuntu minimal installation with an autologin account named "brainvisa" and with password "brainvisa"
5) Perform system updates and install kernel module creation packages :

.. code::

    sudo apt update
    sudo apt upgrade
    sudo apt install gcc make perl

6) Set root password to "brainvisa" (this is necessary to automatically connect to the VM to perform post-install)
7) Reboot the VM
8) Download and install VirtualBox guest additions
9) Shut down the VM
10) Configure the VM in VirualBox (especially 3D acceleration, processors and memory)


Managing container images
=========================

----------------------
Singularity and Docker
----------------------

In a general way, we designed casa-distro first using `Docker <https://www.docker.com>`_, and then extended it to `Singularity <https://www.sylabs.io/>`_. We use Singularity by actually converting Docker images, so images should be built first using Docker. So Docker is needed to build Singularity images for Casa-distro (this is not needed for regular users, which just download system images, and can use singularity alone, or docker alone).

Thus, to build a singularity image, one needs to use first ``casa_distro_admin create_docker``, then ``casa_distro_admin create_singularity``.

--------------
Sharing images
--------------

Images can be uploaded to a centralized place to allow other users to use them.

By default ``publish_docker`` will use `Docker Hub <https://hub.docker.com/>`_, which requires an account and access rights to push images.

Singularity did not have a public hub by the time we started casa-distro, so ``publish_singularity`` will push by default somewhere on the `BrainVISA web site <http://brainvisa.info>`_, which also requires to have access to the website account to push. We could use `Singularity Hub <https://singularity-hub.org/>`_ in the future.

Downloading and updating images do not need any access rights, they are public.

--------------------
Designing new images
--------------------

*create_docker* may be used to update and rebuild the images which are proposed inside the *casa-distro* distribution, but this specific use has a limited benefit since they are normally pre-built and are downloaded from the hubs when needed.

*create_docker* may prove useful however for an application designer who needs to ship specific or additional system packages in the images. In this situation a new image type needs to be designed.

New image types correspond to subdirectories which will looked for in the following directory trees (when they exist):

* ``<workflow_repository>/share/docker/<image_name>/<system>``
* ``$HOME/.config/casa-distro/docker/<image_name>/<system>``
* ``$HOME/.casa-distro/docker/<image_name>/<system>``
* ``<casa_builtin>/docker/<image_name>/<system>``

where:

* ``<workflow_repository>`` is the main workflow repository either passed via the ``--repository`` option, or via the ``CASA_DEFAULT_REPOSITORY`` environment variable, or in the default location ``$HOME/casa_distro``
* ``<casa_builtin>`` if the builtin share directory of casa-distro (or its sources)
* ``<image_name>`` is a name (or type name) for the image, like the builtin ones ``casa-test``, ``casa-dev`` etc.
* ``<system>`` is the name of the system running inside the docker image (the builtin ones are ``ubuntu-18.04``, ``ubuntu-16.04``, ``ubuntu-14.04``, ``ubuntu-12.04``, ``centos-7.4``, ``windows-7-32``, ``windows-7-64``.

So custom, user-defined images can be added in a personal directory.
Such an image definition directory should contain at least two files:

* ``casa_distro_docker.yaml`` is a Yaml file definig dependencies, name and tags for the image. Ex:

.. code-block:: yaml

    dependencies:
        - ../../casa-dev
    image_sources:
      - name: pytorch
        tags:
          - ubuntu-16.04
        visibility: public

* a `Dockerfile <https://docs.docker.com/engine/reference/builder/>`_
  The Dockerfile may (should) be based on another image, in the usual way of building docker images. Thus an existing casa-distro image can be the base for a new one.

Once an image is created with docker, it can be converted to singularity using ``casa_distro create_singularity``.
