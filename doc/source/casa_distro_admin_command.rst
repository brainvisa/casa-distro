===================================
Using the casa_distro_admin command
===================================

``casa_distro_admin`` command is the part of casa-distro which is not needed for regular users / developers: it allows to create docker and singularity system images, push them on a server to be downloadable by regular users, and to manage brainisa distributions release plans.

The admin part has been separated from the other ``casa_distro`` command, both for sake of clarity, and because the admin part is bigger since it contains everything needed to build system images, including some precompiled software for various operating systems, some libraries source code, etc. All this makes the casa-distro complete packages more than 100MB large, whereas the user part is only 300 or 400 KB zipped.

Subcommands
===========

help
----

package_casa_distro
-------------------

publish_casa_distro
-------------------

create_release_plan
-------------------

update_release_plan
-------------------

publish_release_plan
--------------------

apply_release_plan
------------------

create_docker
-------------

update_docker
-------------

publish_docker
--------------

create_singularity
------------------

*create_singularity* converts a docker image into a singularity image. To do so it needs to unpack the docker image into a temporary directory, and re-pack it in a different way. It requires

* sudo / root privileges: the user has to be allowed to run sodo commands, the password will be asked when needed.
* lots of temporary disk space. It may be needed to setup the following environment variables while running ``casa_distro_admin create_singularity``:
    * ``TMPDIR``
    * ``SINGULARITY_TMPDIR``
    * ``SINGULARITY_CACHEDIR``

And *create_docker* needs to have run before, or the docker image should have been pulled. Thus docker is required at this point in the current way things have been impemented (this may change in the future).


publish_singularity
-------------------

publish_build_workflows
-----------------------


Managing container images
=========================

Singularity and Docker
----------------------

In a general way, we designed casa-distro first using `Docker <https://www.docker.com>`_, and then extended it to `Singularity <https://www.sylabs.io/>`_. We use Singularity by actually converting Docker images, so images should be built first using Docker. So Docker is needed to build Singularity images for Casa-distro (this is not needed for regular users, which just download system images, and can use singularity alone, or docker alone).

Thus, to build a singularity image, one needs to use first ``casa_distro_admin create_docker``, then ``casa_distro_admin create_singularity``.

Sharing images
--------------

Images can be uploaded to a centralized place to allow other users to use them.

By default ``publish_docker`` will use `Docker Hub <https://hub.docker.com/>`_, which requires an account and access rights to push images.

Singularity did not have a public hub by the time we started casa-distro, so ``publish_singularity`` will push by default somewhere on the `BrainVISA web site <http://brainvisa.info>`_, which also requires to have access to the website account to push. We could use `Singularity Hub <https://singularity-hub.org/>`_ in the future.

Downloading and updating images do not need any access rights, they are public.

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
