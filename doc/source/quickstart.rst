===========
Casa-Distro
===========

This page contains informations to quickly and simply install casa-distro. If you are a developper looking for more details about casa-distro and its installation, you can see :doc:`Casa-Distro overview<index>`

Quickstart Tutorial
===================

What is Casa-Distro ?
---------------------

Casa-Distro is a cross-paltform ready-to-use environment which is used to install BranVisa and CATI environment. It avoids manual installation of required softwares and librairies.

This is possible by the use of virtualization technology to create a virtual applicance.

Casa-Distro supports a container technology, `Singularity <https://www.sylabs.io/>`_ and a virtual machine technology : `VirtualBox <https://www.virtualbox.org/>`_.

+----------+------------------------+-------------+
|          | Singularity            | VirtualBox  |
+----------+------------------------+-------------+
| Linux    | X                      | X           |
+----------+------------------------+-------------+
| Windows  | :ref:`(X (1)) <ref_1>` | X           |
+----------+------------------------+-------------+
| Mac OS   | :ref:`X (2) <ref_2>`   | X           |
+----------+------------------------+-------------+


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

      pip install casa_distro

* Setup an environment

  Once installed, you can use the casa_distro command in your terminal to download a compiled image with open softwares and tools :

  .. code-block:: bash

      casa_distro setup [options]

  for instance:

  .. code-block:: bash

      casa_distro setup distro=brainvisa version=5.0

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

    The ``casa_distro`` command accepts ``run`` or ``shell`` as sub-commands, they both allow to run programs installed inside the container, for instance:

    .. code-block:: bash

        casa_distro run brainvisa
        casa_distro run anatomist
        casa_distro run AimsFileInfo -h
        casa_distro shell

Installation with VirtualBox
----------------------------
To use Casa-Distro with **VirtualBox**

* `VirtualBox <https://www.virtualbox.org/>`_ must be installed for the user of the system.
* Download a VirtualBox image from brainvisa.info.fr


Notes
-----

.. _ref_1:

.. note:: Singularity on Windows

    Singiularity may be a bit touchy to install on Windows, it needs Windows 10 with linux subsystem plus other internal options. It's possible, not easy.

.. _ref_2:


.. note:: Singularity on Mac

    Singularity for Mac is available as a beta at the time this document is written. It somewhat works but we sometimes ended up with a "silent" virtual machine which seems to do just nothing. But it should work in principle, and sometimes does ;)
