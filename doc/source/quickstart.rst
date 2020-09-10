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

Casa-Distro supports two container technologies, `Singularity <https://www.sylabs.io/>`_ and `Docker <https://www.docker.com>`_ and one virtual machine technology : `VirtualBox <https://www.virtualbox.org/>`_.

+----------+--------------+---------+-------------+
|          | Singularity  | Docker  | VirtualBox  |
+----------+--------------+---------+-------------+
| Linux    | X            | X       | X           |
+----------+--------------+---------+-------------+
| Windows  |              |         | X           |
+----------+--------------+---------+-------------+
| Mac OS   |              |         | X           |
+----------+--------------+---------+-------------+


Requirements
------------

To use Casa-Distro, a user must have a system with 
the following characteristics:

For Linux we recommend:

* Either `Singularity <https://www.sylabs.io/>`_ or
  `Docker <https://www.docker.com>`_ must be installed and setup for the user
  on the building system. These container technologies only runs 
  on reasonably recent Linux systems, recent Mac systems, and Windows. 
* Python >= 2.7 is necessary  run the ``casa_distro`` command.


Singularity is available as an apt package on Ubuntu 16.04 in `neurodebian repositories <http://neuro.debian.net/>`_ and on Ubuntu 18.04 in the main repository, as the ``singularity-container`` package.

Otherwise, to install Singularity on Debian based Linux systems (such as Ubuntu), the following packages must be installed :

.. code-block:: bash

  # System dependencies
  sudo apt-get install python build-essential

  # Singularity install
  VERSION=2.4.5
  wget https://github.com/singularityware/singularity/releases/download/$VERSION/singularity-$VERSION.tar.gz
  tar xvf singularity-$VERSION.tar.gz
  cd singularity-$VERSION
  ./configure --prefix=/usr/local
  make
  sudo make install

For Windows and Mac OS we recommend:

* `VirtualBox <https://www.virtualbox.org/>`_ must be installed for the user of the system.
* Python >= 2.7 is necessary  run the ``casa_distro`` command.

The rest takes place inside containers, so are normally not restricted by the building system, (as long as it has enough memory and disk space).

Install with python
-------------------

Casa_distro is available in the official python package repository `PyPi <https://pypi.org/project/casa-distro/>`_. If python is installed, you can use this command to install casa_distro :

.. code-block:: bash

    pip install casa_distro


Setup brainvisa installation
----------------------------

Once installed, you can use the casa_distro command in your terminal to download a compiled image with open softwares and tools :

.. code-block:: bash

    casa_distro setup [options]
