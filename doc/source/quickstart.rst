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

+----------+--------------+-------------+
|          | Singularity  | VirtualBox  |
+----------+--------------+-------------+
| Linux    | X            | X           |
+----------+--------------+-------------+
| Windows  |              | X           |
+----------+--------------+-------------+
| Mac OS   |              | X           |
+----------+--------------+-------------+


Installation with singularity
-----------------------------
To use Casa-Distro with **singularity**, a user must have a system with 
the following characteristics:


* `Singularity v3 <https://www.sylabs.io/>`_ must be installed and setup for 
  the use on the building system. To install Singularity on Debian based Linux systems (such as Ubuntu), follow `Singularity installation instructions <https://sylabs.io/guides/3.6/admin-guide/installation.html#install-from-source>`_

* Python >= 2.7 is necessary to run the ``casa_distro`` command. Python is usually install on most Linux distribution. To check its installation, open a terminal and type python

* Install Casa-Distro with python

Casa_distro is available in the official python package repository `PyPi <https://pypi.org/project/casa-distro/>`_. If python is installed, you can use this command to install casa_distro :

.. code-block:: bash

    pip install casa_distro

* Setup an environment

Once installed, you can use the casa_distro command in your terminal to download a compiled image with open softwares and tools :

.. code-block:: bash

    casa_distro setup [options]


Installation with VirtualBox
----------------------------
To use Casa-Distro with **VirtualBox**

* `VirtualBox <https://www.virtualbox.org/>`_ must be installed for the user of the system.
* Download a VirtualBox image from brainvisa.info.fr
