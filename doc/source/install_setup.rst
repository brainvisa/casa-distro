
======================
Installation and setup
======================

.. highlight:: bash

Setting up Docker
=================

Install and use docker on an Ubuntu host
----------------------------------------

* Install docker using apt-get :

  ::

    sudo apt-get install docker.io

* To enable users other than root and users with sudo access to be able to run Docker commands:

  .. warning::

    Users who can run Docker commands have effective root control of the system. Only grant this privilege to trusted users.

  The following procedure applies to version 1.5 and later of Docker.

  #. Create the ``docker`` group (maybe group ``docker`` already exists):

    ::

      sudo groupadd docker

  2. Restart the docker service:

    ::

      sudo service docker restart

    .. warning::

      For some os system version (Ubuntu 14.04-15.10) use **docker.io** instead of **docker**

    .. warning::

      The UNIX socket ``/var/run/docker.sock`` is now readable and writable by members of the docker group.

  3. Add the users that should have Docker access to the docker group:

    ::

      sudo usermod -a -G docker <username>

  4. logout / login to update groups cache

    Or use the following command to open a new shell forcing to take group updates into account:

    ::

      sudo su <login>


.. _change_docker_base_dir:

Change Docker's storage base directory
--------------------------------------

By default, docker images are stored in will be ``/var/lib/docker/aufs`` but can fall back to ``btrfs``, ``devicemapper`` or ``vfs``.

* ``/var/lib/docker/{driver-name}`` will contain the driver specific storage for contents of the images.
* ``/var/lib/docker/graph/`` now only contains metadata about the image, in the ``json`` and ``layersize`` files.

In the case of aufs:

* ``/var/lib/docker/aufs/diff/`` has the file contents of the images.
* ``/var/lib/docker/repositories-aufs`` is a JSON file containing local image information. This can be viewed with the command ``docker images``.

#. First method

  You can change Docker's storage base directory (where container and images go) using the ``-g`` option when starting the Docker daemon.
  You must to stop docker:

  ::

    sudo service docker stop

  Create a new directory for docker:

  ::

    sudo mkdir /mnt/docker

.. _dns_setup:

  * Ubuntu/Debian: edit your ``/etc/default/docker`` file with the ``-g`` option:

    ::

      DOCKER_OPTS="-dns 8.8.8.8 -dns 8.8.4.4 -g /mnt/docker" # (or write it if the line doesn't exist in this file)

  * Fedora/Centos: edit ``/etc/sysconfig/docker``, and add the ``-g`` option in the ``other_args`` variable: ex.

    ::

      other_args="-g /var/lib/ testdir".

    If there's more than one option, make sure you enclose them in ``" "``.

  Docker should use the new directory after a restart:

  ::

    sudo service docker start

  You can check it using:

  ::

    docker info

2. Second method (Using a symlink)

  .. warning::

    These steps depend on your current /var/lib/docker being an actual directory (not a symlink to another location).

  #. Stop docker:

    ::

      service docker stop.

    Verify no docker process is running:

    ::

      ps faux

  2. Double check docker really isn't running. Take a look at the current docker directory:

    ::

      ls /var/lib/docker/

  3. Make a backup:

    ::

      tar -zcC /var/lib docker > /mnt/pd0/var_lib_docker-backup-$(date +%s).tar.gz

  4. Move the /var/lib/docker directory to your new partition:

    ::

      mv /var/lib/docker /mnt/pd0/docker

  5. Make a symlink:

    ::

      ln -s /mnt/pd0/docker /var/lib/docker

  6. Take a peek at the directory structure to make sure it looks like it did before the ``mv``:

    ::

      ls /var/lib/docker/

    (note the trailing slash to resolve the symlink)

  7. Start docker back up service

    ::

      docker start

  8. restart your containers


Overview of the existing public brainvisa images
================================================

To search available images on docker hub (example with ubuntu) :

::

  docker search --stars=10 ubuntu

or using this url: https://hub.docker.com

* An open source brainvisa repository is available on docker hub: https://hub.docker.com/r/cati

.. note:: It is a public repository !

* **cati/casa-test** image

  Minimal OS system to test a package of brainvisa in lambda-user conditions.

  Just some libraries are installed to run a X server and to test the creation of snapshots.

  Several images:

  #. Ubuntu 12.04
  #. Ubuntu 16.04
  #. windows-7-32: Ubuntu 14.04 + Wine for windows-7-32
  #. windows-7-64: Ubuntu 14.04 + Wine for windows-7-64

* **cati/brainvisa-dev** image

  Based on ``cati/casa-test`` image.

  Include all system dependencies (using ``apt get``) to run a compilation of brainvisa and Qt Installer Framework to create a brainvisa package.

  These images are dedicated for developers.

  Several images:

  #. Ubuntu 12.04
  #. Ubuntu 16.04
  #. windows-7-32: Ubuntu 14.04 + Wine for windows-7-32
  #. windows-7-64: Ubuntu 14.04 + Wine for windows-7-64

.. * **cati/brainvisa-dev-opensource** image
    Use cati/brainvisa-devbase image.
    Include the compilation of all open source projects in brainvisa.
    bv_maker.cfg, svn and svn_secret files are needed to get sources and run the build.
    It is necessary to store the bioproj account password in clear (svn_secret).
    Four images :
      trunk for Ubuntu 12.04
      bug_fix for Ubuntu 12.04
      trunk for Ubuntu 16.04
      bug_fix for Ubuntu 16.04


How to use a docker image
=========================

* Get docker image:

  ::

    docker pull cati/casa-test:ubuntu-12.04


  Examples with other cati images in docker hub :

  ::

    docker pull cati/casa-test:ubuntu-16.04
    docker pull cati/casa-dev:ubuntu-12.04
    docker pull cati/casa-dev:ubuntu-16.04

* Run a docker image:

  ::

    docker run -it --rm cati/casa-dev:ubuntu-16.04-bug_fix /bin/bash


.. _cleaning_up_docker:

Cleaning up docker
==================

Containers
----------

* Remove exited containers

  ::

    docker ps --filter status=dead --filter status=exited -aq | xargs -r docker rm -v

* Remove older containers (example: 2 weeks or more)

  ::

    docker ps --filter "status=exited" | grep 'weeks ago' | awk '{print $1}' | xargs --no-run-if-empty sudo docker rm

* Remove all containers

  ::

    docker rm $(docker ps -a -q)


Images
------

* Remove an image:

  ::

    $ docker images
    REPOSITORY                  TAG                    IMAGE ID            CREATED             VIRTUAL SIZE
    cati/brainvisa-devbase      ubuntu-12.04           7c1691e1e9d1        2 days ago          2.264 GB

  To know the id of the image to remove...

  ::

    docker rmi 7c1691e1e9d1

  To remove ``cati/brainvisa-devbase``.

  If one or more containers are using the image, use the option ``-f`` to force the command ``rmi``:

  ::

    docker rmi -f 7c1691e1e9d1

* Remove unused images

  ::

    docker images --no-trunc | grep '<none>' | awk '{ print $3 }' | xargs -r docker rmi

* Remove all images

  ::

    docker rmi $(docker images -q)


How to change the development environment ?
===========================================

To add an external library, modify the Dockerfile of ``brainvisa-dev`` for ubuntu-12.04 or ubuntu-16.04:

.. code-block:: dockerfile

  # Dockerfile for image cati/brainvisa-devbase:ubuntu-16.04

  FROM cati/casa-test:ubuntu-16.04

  USER root

  # Install system dependencies
  RUN apt-get install -y \
      build-essential \
      (...)
      liblapack-dev \
      <your_library> \  ###### HERE INSERT THE NAME OF THE EXTERNAL LIBRARY
    && apt-get clean

  # Install Qt Installer Framework
  COPY qt_installer_script /tmp/qt_installer_script
  RUN wget -q http://download.qt.io/official_releases/qt-installer-framework/2.0.3/QtInstallerFramework-linux-x64.run -O /tmp/QtInstallerFramework-linux-x64.run && \
      chmod +x /tmp/QtInstallerFramework-linux-x64.run && \
      xvfb-run /tmp/QtInstallerFramework-linux-x64.run --script /tmp/qt_installer_script && \
      ln -s /usr/local/qt-installer/bin/* /usr/local/bin/ && \
      rm /tmp/QtInstallerFramework-linux-x64.run /tmp/qt_installer_script

  (...)

  ###### OR WRITE THE COMMAND LINES TO INSTALL THE LIBRARY FROM SOURCES

  USER brainvisa

After, run the script called create_images (``[sources]/casa-distro/[trunk|bug_fix]/docker/create_images``).

This script will rebuild ``casa-test`` and ``casa-dev`` images if the ``Dockefile`` was modified and will push all images in docker hub.

In our example, only the ``Dockerfile`` of ``casa-dev`` is different, so only ``casa-dev`` image will rebuilt.

.. todo::

    Deploying a registry server

The aim of a registry server for docker is to share private images of brainvisa for CATI members.
.. Create the registry on https://catidev.cea.fr is more complicated due to CEA retrictions, so we use https://sandbox.brainvisa.info.

The Registry is compatible with Docker engine version 1.6.0 or higher.

In progress....

To update from changes in the image on server:

::

  docker pull is208614:5000/casa/system


Troubleshooting
===============

Typical problems are listed here.

System disk full
----------------

Docker images are big, and may grow bigger...

* :ref:`Change the filesystem / disk for docker images <change_docker_base_dir>`
* :ref:`cleanup leftover docker images or containers <cleaning_up_docker>`


Cannot build docker image, network access denied
------------------------------------------------

With Docker versions older than 1.13, the ``docker build`` command did not have a host networking option. On some systems (Ubuntu 14 for instance) the contents of ``/etc/resolv.conf`` point to a local proxy DNS server (at least that's what I understand), and docker could not use it during image building.

Either upgrade to a newer Docker, or change the :ref:`DNS setup <dns_setup>` for Docker.


Cannot mount ``~/.ssh/id_rsa`` when starting docker
---------------------------------------------------

When docker starts, even when running as a specific user, it starts up as root. The mount options specified on docker commandline are setup as root. If the user home directory is on a network filesystem (NFS...), the local root user cannot override the filesystem access rights. Thus the directory tree must be traversable to reach the mounted directory.

In other words, the ``+x`` flag has to be set for "other" users on the directory and its parents. Typically:

::

  chmod o+x ~
  chmod o+x ~/.ssh
