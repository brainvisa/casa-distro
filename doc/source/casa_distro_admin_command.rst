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

Singularity has no public hub, so ``publish_singularity`` will push by default somewhere on the `BrainVISA web site <http://brainvisa.info>`_, which also requires to have access to the website account to push.

Downloading and updating images do not need any access rights, they are public.

