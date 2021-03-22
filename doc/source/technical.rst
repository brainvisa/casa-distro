
================
Technical issues
================

.. highlight:: bash

.. |bv| replace:: BrainVISA_

.. _BrainVISA: http://brainvisa.info

* The :bv:`BrainVisa download / install section <download.html>` explains how to install casa-distro and a released, compiled, version of BrainVISA. This is what a "regular user" needs.

* Developers can find information on the :doc:`developer` section.

This document explains how to setup and use some container systems (Singularity, Docker), and tries to solve some technical issues which can occur when using them.


Containers and distributed execution
====================================

|bv| can perform distributed execution, using :soma-workflow:`Soma-Workflow <index.html>`.

But soma-workflow distributed execution, in its current released version, will not spawn Docker or Singularity (or casa_distro run) in remote processing. We have made modifications in the `github/master branch <https://github.com/neurospin/soma-workflow>`_ (which is included in brainvisa/master branches) to add support for it. However it needs some additional configuration on server side to specify how to run the containers.

Alternately, in an installed :ref:`environment`, commands are also available via "run scripts", located in ``<environment>/host/host_bin/``. If this directory is in the computing resource ``PATH`` environment variable, then the commands will run the container transparently.

For commands run directly through the ``python`` command, more work will be required because the system ``python`` is, of course, not overloaded in BrainVISA/Casa run scripts.

Remember that software running that way live in a container, which is more or less isolated from the host system. To access data, casa_distro will likeky need additional directories mount options. It can be specified on ``casa_distro`` commandline, or in the file ``container_options`` item in ``<casa_distro_environment>/host/conf/casa_distro.json``.



.. Setting up Docker
.. =================
..
.. Install and use docker on an Ubuntu host
.. ----------------------------------------
..
.. * Install docker using apt-get :
..
..   ::
..
..     sudo apt-get install docker.io
..
.. * To enable users other than root and users with sudo access to be able to run Docker commands:
..
..   .. warning::
..
..     Users who can run Docker commands have effective root control of the system. Only grant this privilege to trusted users.
..
..   The following procedure applies to version 1.5 and later of Docker.
..
..   #. Create the ``docker`` group (maybe group ``docker`` already exists):
..
..     ::
..
..       sudo groupadd docker
..
..   2. Restart the docker service:
..
..     ::
..
..       sudo service docker restart
..
..     .. warning::
..
..       For some os system version (Ubuntu 14.04-15.10) use **docker.io** instead of **docker**
..
..     .. warning::
..
..       The UNIX socket ``/var/run/docker.sock`` is now readable and writable by members of the docker group.
..
..   3. Add the users that should have Docker access to the docker group:
..
..     ::
..
..       sudo usermod -a -G docker <username>
..
..   4. logout / login to update groups cache
..
..     Or use the following command to open a new shell forcing to take group updates into account:
..
..     ::
..
..       sudo su <login>
..
..
.. .. _change_docker_base_dir:
..
.. Change Docker's storage base directory
.. --------------------------------------
..
.. By default, docker images are stored in will be ``/var/lib/docker/aufs`` but can fall back to ``btrfs``, ``devicemapper`` or ``vfs``.
..
.. * ``/var/lib/docker/{driver-name}`` will contain the driver specific storage for contents of the images.
.. * ``/var/lib/docker/graph/`` now only contains metadata about the image, in the ``json`` and ``layersize`` files.
..
.. In the case of aufs:
..
.. * ``/var/lib/docker/aufs/diff/`` has the file contents of the images.
.. * ``/var/lib/docker/repositories-aufs`` is a JSON file containing local image information. This can be viewed with the command ``docker images``.
..
.. #. First method
..
..   You can change Docker's storage base directory (where container and images go) using the ``-g`` option when starting the Docker daemon.
..   You must to stop docker:
..
..   ::
..
..     sudo service docker stop
..
..   Create a new directory for docker:
..
..   ::
..
..     sudo mkdir /mnt/docker
..
.. .. _dns_setup:
..
..   * Ubuntu/Debian: edit your ``/etc/default/docker`` file with the ``-g`` option:
..
..     ::
..
..       DOCKER_OPTS="-dns 8.8.8.8 -dns 8.8.4.4 -g /mnt/docker" # (or write it if the line doesn't exist in this file)
..
..   * Fedora/Centos: edit ``/etc/sysconfig/docker``, and add the ``-g`` option in the ``other_args`` variable: ex.
..
..     ::
..
..       other_args="-g /var/lib/ testdir".
..
..     If there's more than one option, make sure you enclose them in ``" "``.
..
..   Docker should use the new directory after a restart:
..
..   ::
..
..     sudo service docker start
..
..   You can check it using:
..
..   ::
..
..     docker info
..
.. 2. Second method (Using a symlink)
..
..   .. warning::
..
..     These steps depend on your current /var/lib/docker being an actual directory (not a symlink to another location).
..
..   #. Stop docker:
..
..     ::
..
..       service docker stop.
..
..     Verify no docker process is running:
..
..     ::
..
..       ps faux
..
..   2. Double check docker really isn't running. Take a look at the current docker directory:
..
..     ::
..
..       ls /var/lib/docker/
..
..   3. Make a backup:
..
..     ::
..
..       tar -zcC /var/lib docker > /mnt/pd0/var_lib_docker-backup-$(date +%s).tar.gz
..
..   4. Move the /var/lib/docker directory to your new partition:
..
..     ::
..
..       mv /var/lib/docker /mnt/pd0/docker
..
..   5. Make a symlink:
..
..     ::
..
..       ln -s /mnt/pd0/docker /var/lib/docker
..
..   6. Take a peek at the directory structure to make sure it looks like it did before the ``mv``:
..
..     ::
..
..       ls /var/lib/docker/
..
..     (note the trailing slash to resolve the symlink)
..
..   7. Start docker back up service
..
..     ::
..
..       docker start
..
..   8. restart your containers
..
..
.. Overview of the existing public brainvisa Docker images
.. -------------------------------------------------------
..
.. To search available images on docker hub (example with ubuntu) :
..
.. ::
..
..   docker search --stars=10 ubuntu
..
.. or using this url: https://hub.docker.com
..
.. * An open source brainvisa repository is available on docker hub: https://hub.docker.com/r/cati
..
.. .. note:: It is a public repository !
..
..
.. How to use a docker image
.. -------------------------
..
.. * Get docker image:
..
..   ::
..
..     docker pull cati/casa-dev:ubuntu-18.04
..
..
..   Examples with other cati images in docker hub :
..
..   ::
..
..     docker pull cati/casa-test:ubuntu-16.04
..     docker pull cati/casa-dev:ubuntu-16.04
..     docker pull cati/casa-dev:ubuntu-18.04
..
.. * Run a docker image:
..
..   ::
..
..     docker run -it --rm cati/casa-dev:ubuntu-18.04-bug_fix /bin/bash
..
..
.. .. _cleaning_up_docker:
..
.. Cleaning up docker
.. ------------------
..
.. Containers
.. ++++++++++
..
.. * Remove exited containers
..
..   ::
..
..     docker ps --filter status=dead --filter status=exited -aq | xargs -r docker rm -v
..
.. * Remove older containers (example: 2 weeks or more)
..
..   ::
..
..     docker ps --filter "status=exited" | grep 'weeks ago' | awk '{print $1}' | xargs --no-run-if-empty sudo docker rm
..
.. * Remove all containers
..
..   ::
..
..     docker rm $(docker ps -a -q)
..
..
.. Images
.. ++++++
..
.. * Remove an image:
..
..   ::
..
..     $ docker images
..     REPOSITORY                  TAG                    IMAGE ID            CREATED             VIRTUAL SIZE
..     cati/casa-dev       ubuntu-12.04           7c1691e1e9d1        2 days ago          2.264 GB
..
..   To know the id of the image to remove...
..
..   ::
..
..     docker rmi 7c1691e1e9d1
..
..   To remove ``cati/casa-dev``.
..
..   If one or more containers are using the image, use the option ``-f`` to force the command ``rmi``:
..
..   ::
..
..     docker rmi -f 7c1691e1e9d1
..
.. * Remove unused images
..
..   ::
..
..     docker images --no-trunc | grep '<none>' | awk '{ print $3 }' | xargs -r docker rmi
..
.. * Remove all images
..
..   ::
..
..     docker rmi $(docker images -q)
..
..
.. How to change the development environment ?
.. -------------------------------------------
..
.. To add an external library, modify the Dockerfile of ``casa-dev`` for ubuntu-16.04 or ubuntu-18.04:
..
.. .. code-block:: dockerfile
..
..   # Dockerfile for image cati/casa-dev:ubuntu-16.04
..
..   FROM cati/casa-test:ubuntu-16.04
..
..   USER root
..
..   # Install system dependencies
..   RUN apt-get install -y \
..       build-essential \
..       (...)
..       liblapack-dev \
..       <your_library> \  ###### HERE INSERT THE NAME OF THE EXTERNAL LIBRARY
..     && apt-get clean
..
..   # Install Qt Installer Framework
..   COPY qt_installer_script /tmp/qt_installer_script
..   RUN wget -q http://download.qt.io/official_releases/qt-installer-framework/2.0.3/QtInstallerFramework-linux-x64.run -O /tmp/QtInstallerFramework-linux-x64.run && \
..       chmod +x /tmp/QtInstallerFramework-linux-x64.run && \
..       xvfb-run /tmp/QtInstallerFramework-linux-x64.run --script /tmp/qt_installer_script && \
..       ln -s /usr/local/qt-installer/bin/* /usr/local/bin/ && \
..       rm /tmp/QtInstallerFramework-linux-x64.run /tmp/qt_installer_script
..
..   (...)
..
..   ###### OR WRITE THE COMMAND LINES TO INSTALL THE LIBRARY FROM SOURCES
..
..   USER brainvisa
..
.. After, run the script called create_images (``[sources]/casa-distro/[trunk|bug_fix]/docker/create_images``).
..
.. This script will rebuild ``casa-test`` and ``casa-dev`` images if the ``Dockefile`` was modified and will push all images in docker hub.
..
.. In our example, only the ``Dockerfile`` of ``casa-dev`` is different, so only ``casa-dev`` image will rebuilt.
..
.. .. todo::
..
..     Deploying a registry server
..
.. The aim of a registry server for docker is to share private images of brainvisa for CATI members.
.. .. Create the registry on https://catidev.cea.fr is more complicated due to CEA retrictions, so we use https://sandbox.brainvisa.info.
..
.. The Registry is compatible with Docker engine version 1.6.0 or higher.
..
.. In progress....
..
.. To update from changes in the image on server:
..
.. ::
..
..   docker pull is208614:5000/casa/system


Developing in containers
========================

See also the BrainVisa developers site: https://brainvisa.github.io/

Using Git
---------

Both git ans svn are used in Brainvisa projects sources. svn will probably be completely replaced with git.

git URLs use https by default. It's OK for anonymous download and update, but they require manual authentication for each push, thus it's painful. If you have a github account, you can use ssh with a ssh key instead. See https://brainvisa.github.io/contributing.html

Once done git will automatically use ssh. But then ssh needs to be working...


Using ssh
---------

git and ssh may be used either on the host side (since sources are actually stored on the host filesystem), or within the container. As users may have ssh keys and have already registered them in GitHub, they will want to reuse their host ssh keys.

On Linux (or Mac) hosts, it is possible.

Singularity 3 does not allow to mount the host ``.ssh`` directory into the already mounted container home directory. So there are 2 other options:

#. copy the host ``.ssh`` directory into the container home::

    cp -a "/host/$CASA_HOST_HOME/.ssh" ~/

   But copying private ssh keys is not recommended for security reasons.

#. use a ssh agent:
    - install ``keychain``. On debian-based Linux distributions, this is::

        sudo apt-get install keychain

    - add in your host ``$HOME/.bash_profile`` file::

        eval $(keychain --eval --agents ssh id_rsa)


.. _troubleshooting:

Troubleshooting
===============

Typical problems are listed here.

.. System disk full
.. ----------------
..
.. Docker images are big, and may grow bigger...
..
.. * :ref:`Change the filesystem / disk for docker images <change_docker_base_dir>`
.. * :ref:`cleanup leftover docker images or containers <cleaning_up_docker>`
..
..
.. Cannot build docker image, network access denied
.. ------------------------------------------------
..
.. With Docker versions older than 1.13, the ``docker build`` command did not have a host networking option. On some systems (Ubuntu 14 for instance) the contents of ``/etc/resolv.conf`` point to a local proxy DNS server (at least that's what I understand), and docker could not use it during image building.
..
.. Either upgrade to a newer Docker, or change the :ref:`DNS setup <dns_setup>` for Docker.
..
..
.. Cannot mount ``~/.ssh/id_rsa`` when starting docker
.. ---------------------------------------------------
..
.. When docker starts, even when running as a specific user, it starts up as root. The mount options specified on docker commandline are setup as root. If the user home directory is on a network filesystem (NFS...), the local root user cannot override the filesystem access rights. Thus the directory tree must be traversable to reach the mounted directory.
..
.. In other words, the ``+x`` flag has to be set for "other" users on the directory and its parents. Typically:
..
.. ::
..
..   chmod o+x ~
..   chmod o+x ~/.ssh


.. _opengl_troubleshooting:

OpenGL is not working, or is slow
---------------------------------

with docker
+++++++++++

Several options are needed to enable display and OpenGL. Normally casa_distro tries to set them up and should do the best it can.

On machines with nvidia graphics cards and nvidia proprietary drivers, casa_distro will add options to mount the host system drivers and OpenGL libraries into the container in order to have hardware 3D rendering.

Options are setup in the ``casa_distro.json`` file so you can check and edit them. Therefore, the detection of nvidia drivers is done on the host machine at the time of build workflow creation: if the build workflow is shared accross several machines on a network, this config may not suit all machines running the container.

However it does not seem to work when ssh connections and remote display are involved.

.. _sing_opengl:

with singularity
++++++++++++++++

There are several ways to use OpenGL in singularity, depending on the host system, the 3D hardware, the X server, the type of user/ssh connection.

Our container images include  a software-only Mesa implementation of OpenGL, which can be used if other solutions fail.

Casa-distro tries to use "reasonable" settings but cannot always detect the best option. Thus the user can control the behavior using the ``opengl`` option in ``casa_distro run``, ``casa_distro shell``, ``casa_distro mrun`` and ``casa_distro bv_maker`` subcommands. This option can take several values: ``auto``, ``container``, ``nv``, or ``software``. The default is, of course, ``auto``.

* ``auto``: performs auto-detection: same as ``nv`` if an NVidia device is detected on a host linux system, otherwise same as ``container``, unless we detect a case where that is known to fail (in which case we would use ``software``).
* ``container``: passes no special options to Singularity: the mesa installed in the container is used
* ``nv`` tries to mount the proprietary NVidia driver of the host (linux) system in the container
* ``software`` sets ``LD_LIBRARY_PATH`` to use a software-only OpenGL rendering. This solution is the slowest but is a fallback when no other solution works.

There are cases where the nvidia option makes things worse (see ssh connections below). If you ever need to disable the nvidia option, you can add an option ``opengl=software`` or ``opengl=container`` to ``run``, ``shell`` and other subcommands:

.. code-block:: bash

    casa_distro run gui=1 opengl=software glxinfo

If it is OK, you can set this option in the build workflow ``casa_distro.json`` config, under the ``"container_gui_env"`` key::

    {
        "casa_distro_compatibility": "3",
        "name": "brainvida-5.0",
        "image": "/home/bilbo/casa_distro/brainvisa-5.0.sif",
        "type": "user",
        "system": "ubuntu-18.04",
        "container_type": "singularity",
        "distro": "brainvisa",
        "container_options": [
            "--softgl",
        ],
        # ...
    }

Via a ssh connection:
    same host, different user:
        ``xhost +`` must have been used on the host system. Works (as long as
        the ``XAUTHORITY`` env variable points to the ``.Xauthority`` file from
        the host user home directory).
    different host:
        I personally could not make it work using the ``nv`` option. But
        actually outside of casa-distro or any container, it doesn't work
        either. Remote GLX rendering has always been a very delicate thing...

        It works for me using the software Mesa rendering (slow). So at this point, using casa_distro actually makes it possible to render OpenGL when the host system cannot (or not directly)...


.. _mac_sing_troubleshooting:

On MacOS systems
----------------

Singularity is not working, it's just doing nothing
+++++++++++++++++++++++++++++++++++++++++++++++++++

Singularity for Mac is available as a beta at the time this document is written (but with no updates nor news in more than a year). It somewhat works but we sometimes ended up with a "silent" virtual machine which seems to do just nothing. But it should work in principle, and sometimes does ;)

We experienced this behaviour on MacOS 10.11 using Singularity Desktop 3.3-beta for Mac. We had to upgrade the system (to 10.15) and then it worked. But then after a few days became silent again, for certain users, using certain images... but it still worked for our BrainVisa images...


GUI is not working in singularity
+++++++++++++++++++++++++++++++++

Graphical commands (brainvisa, anatomist, others...) should run through a X11 server. Xquartz is installed in MacOS systems, but need to be started, and a bit configured.

* open Xquartz, either using the desktop / finder icon, or by running a X command such as::

    xhost +

* in the Xquartz preferences menu, go to "security" and check the option to enable network connections (tcp) to the X server
* quit the server, it needs to be restarted
* run
    ::

        xhost +

    to enable other users / apps to use the graphical server (this will start Xquartz, if not already running). Note that this command needs to be run again each time the Xquartz server is stopped / restarted.
* You should use the ``opengl=software`` option in ``casa_distro`` otherwise 3D will likely crash the programs.
* now graphical applications should run inside singularity containers. 3D hardware is not used however, rendering is using a software rendering, so it is not fast.

.. _mac_vbox_troubleshooting:

VirtualBox images are crashing when booting
+++++++++++++++++++++++++++++++++++++++++++

I personally had trouble getting the VirtualBox image to actually run on MacOS 10.15. The virtual machine consistently crashed at boot time. After inspecting the logs I found out that the sound card support might be the cause, and I had to use a "fake sound device" in the virtualbox image settings. Then it appeared that all graphics display was notably slow (either 2D and 3D), whatever video / accelerated 3D support options. And icons and fonts in the virtual machine were microscopic, almost impossible to read, and difficult if even possible to configure in the linux desktop. The "zoom factor x2" option in virtualbox was very handy for that, but reduced the actual resolution by a factor of 2 if I understand. Apart from these limitations, the software was running.

We have a working install procedure from one of our friends using a Mac here:

On a Mac Book Pro, with MacOs 10.15.7 and 16Gb of memory:

* Install VirtualBox v 6.1
* Import the Brainvisa VM
* Disable sound (fake sound device)
* Guests additions: run the Linux additions after mounting the CD and opening its contents.
* Shutdown the virtual machine, go to its configuration, and in the 'Display' section, chose 'Graphics Controller: VMSVGA', tick 'Activate 3D acceleration' and increase the 'Video memory' to 128Mb.
* setup shared directory to mount the computer filesystem (my user directory). For this I went into the 'shared directory' section of the VM configuration, and asked to have ``/media/olivier`` to point on my home directory (on my Mac: ``/Users/olivier``) .
* There is an issue to fix before accessing ``/media/olivier``, because of a permission issue. It is fixed by typing the following into the terminal::

    sudo usermod -aG vboxsf $(whoami)

* reboot the VM.
* there is still a keyboard mapping issue, it can probably be fixed in the linux desktop config somewhere.

Good to go !


.. _win_sing_troubleshooting:

On Windows systems
------------------

Installing Singularity on Windows
+++++++++++++++++++++++++++++++++

* Singularity may be a bit touchy to install on Windows, it needs Windows 10 with linux subsystem (WSL2) plus other internal options (hyper-V something). It's possible, not easy.
* Once singularity is working, to be able to run graphical programs, a X server must be installed. Several ones exist for Windows, several are free, but most of them do not support hardware-accelerated 3D. `Xming <https://sourceforge.net/projects/xming/>`_ supports hardware acceleration, but has gone commercial. The latest free implementation was released in 2016, and seems to work. Microsoft is possibly working on another implementation.
