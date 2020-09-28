======================
Casa-Distro quickstart
======================

This page contains informations to quickly and simply install casa-distro, and the `BrainVISA software distribution <http://brainvisa.info>`_ through casa-distro.

If you are a developper looking for more details about casa-distro and its installation, you can follow the first steps here to install ``casa-distro``, but skip the ``casa_distro setup`` step, then follow the instructions in :doc:`install_setup`.


Quickstart Tutorial
===================

What is Casa-Distro ?
---------------------

Casa-Distro is a cross-paltform ready-to-use environment which is used to install BranVisa and CATI environment. It avoids manual installation of required softwares and librairies.

This is possible by the use of virtualization technology to create a virtual applicance.

Casa-Distro supports a container technology, `Singularity <https://www.sylabs.io/>`_ and a virtual machine technology : `VirtualBox <https://www.virtualbox.org/>`_.

Support and installation instructions matrix
--------------------------------------------

+----------+-------------------------------------------------------------+-------------------------------------------------------+
|          | Singularity                                                 | VirtualBox                                            |
+----------+-------------------------------------------------------------+-------------------------------------------------------+
| Linux    | :ref:`✓ <sing_linux>`                                       | :ref:`✓ <vbox>`                                       |
+----------+-------------------------------------------------------------+-------------------------------------------------------+
| Windows  | (:ref:`✓ <sing_win>` :ref:`(1) <win_sing_troubleshooting>`) | :ref:`✓ <vbox>`                                       |
+----------+-------------------------------------------------------------+-------------------------------------------------------+
| Mac OS   | :ref:`✓ <sing_mac>` :ref:`(2) <mac_sing_troubleshooting>`   | :ref:`✓ <vbox>` :ref:`(3) <mac_vbox_troubleshooting>` |
+----------+-------------------------------------------------------------+-------------------------------------------------------+

.. _sing_linux:
.. _sing_win:
.. _sing_mac:

Installation with singularity
-----------------------------

To use Casa-Distro with **singularity**, a user must have a system with
the following characteristics:


* `Singularity v3 <https://www.sylabs.io/>`_ must be installed and setup for
  the use on the building system. To install Singularity on Debian based Linux systems (such as Ubuntu), follow `Singularity installation instructions <https://sylabs.io/guides/3.6/admin-guide/installation.html#install-from-source>`_

* Python >= 2.7 is necessary to run the ``casa_distro`` command. Python is usually installed on most Linux distributions. To check its installation, open a terminal and type: ``python`` (you can leave the interpreter using `<ctrl>-D` or by typing `exit()`. If it is not installed, do it (https://python.org).

* Install Casa-Distro with python

  Casa_distro is available in the official python package repository `PyPi <https://pypi.org/project/casa-distro/>`_. Once python is installed, you can use this command to install casa_distro :

  .. code-block:: bash

      pip install casa-distro

* Setup an environment

  Once installed, you can use the ``casa_distro`` command in your terminal to download and install a compiled image with open software and tools :

  .. code-block:: bash

      casa_distro setup [options]

  for instance:

  .. code-block:: bash

      casa_distro setup distro=brainvisa version=5.0

  This is the step which will actually install a BrainVISA software distribution.

* Run programs from the container

  There are several ways actually:

  1. The simplest way, from a Unix host machine (or windows with a bash shell):

    * Add to the ``PATH`` environment variable the directory containing run scripts

      .. code-block:: bash

          # this line could be in a ~/.bashrc or ~/.bash_profile script
          export PATH="$HOME/casa_distro/brainvisa-5.0/host/host_bin:$PATH"

    * then call the programs like if they were on the host machine:

      .. code-block:: bash

          # run programs
          AimsFileInfo --info

  2. Similar, from a Windows host machine:

    * add the directory containing the run scripts in the ``%PATH%`` environment variable (can be done globally in the user / machine settings):

      .. code-block:: bat

          set PATH=%HOMEDRIVE%%HOMEPATH%\casa_distro\brainvisa-5.0\host\win_bin;%PATH%

    * run the programs from a cmd shell:

      .. code-block:: bat

          AimsFileInfo --info

  3. Using ``casa_distro`` or ``bv`` interface to containers:

    * The ``bv`` command accepts ``shell`` or an executable program name as sub-commands, they both allow to run programs installed inside the container, for instance:

      .. code-block:: bash

          bv brainvisa
          bv anatomist
          bv AimsFileInfo -h
          bv shell

      As programs are actually running in a container or a virtual machine (transparently), the user may have to configure additional mount points to actually see his data and working directories from his host machine in the container. This is done graphically, simply using:

      .. code-block:: bash

          bv

      Technically, ``bv`` is a simplified version of ``casa_distro`` which is contained inside a single *environment* (distribution installation) and only allows to run and configure this environment.

    * The ``casa_distro`` command accepts ``run`` or ``shell`` as sub-commands, they both allow to run programs installed inside the container, for instance:

      .. code-block:: bash

          casa_distro run brainvisa
          casa_distro run anatomist
          casa_distro run AimsFileInfo -h
          casa_distro shell

      Compared to ``bv``, ``casa_distro`` allows to handle multiple *environments* (distribution installations) via parameters, and allows to setup (download/install) or remove environments or container images.

      Note that ``bv`` is made available inside each environment (distribution installation) and makes an installation self-contained (it doesn't depend on a global host installation of ``bv`` outside of the environment directory), whereas ``casa_distro`` is cross-environments and thus needs to be installed on the host system. Note also that ``bv`` still depends on Python which still needs to be installed and working on the host machine.

* see the :ref:`troubleshooting` section, especially the :ref:`OpenGL troubleshooting <sing_opengl>`, :ref:`Singularity on Mac <mac_sing_troubleshooting>` and :ref:`Singularity on Windows <win_sing_troubleshooting>` subsections.

.. _vbox:

Installation with VirtualBox
----------------------------
To use Casa-Distro with **VirtualBox**

* `VirtualBox <https://www.virtualbox.org/>`_ must be installed for the user of the system.
* Download a VirtualBox image from http://brainvisa.info/casa-distro/releases/vbox/
* start ``virtualbox``
* in VirtualBox, import the downloaded image - some configuration (memory, CPU, video, sound etc) may be useful for it in VirtualBox.
* some mount points to the host filesystem can be added to see the host filesystem directories from the VM.
* start it
* in the running Linux virtual machine, BrainVISA is installed and configured.  You can open a terminal and type:

  .. code-block:: bash

      AimsFileInfo -h
      brainvisa
      anatomist

The virtual machine has a configured user named "brainvisa", with the password "brainvisa", which has ``sudo`` (admin) permissions.

* see the :ref:`troubleshooting` section, especially the :ref:`VirtualBox on Mac <mac_vbox_troubleshooting>` subsection.
