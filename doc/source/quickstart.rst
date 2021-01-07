======================
Casa-Distro quickstart
======================

.. highlight:: bash

This page contains informations to quickly and simply install the `BrainVISA software distribution <http://brainvisa.info>`_ through container images and an embedded casa-distro inside them.

If you are a developper looking for more details about casa-distro and its installation, you can follow the first steps here to install ``casa-distro``, but skip the ``casa_distro setup`` step, then follow the instructions in :doc:`developer`.


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
  the use on the building system. To install Singularity on Debian based Linux systems (such as Ubuntu),

    * Look in http://brainvisa.info/casa-distro/singularity/ for a suitable debian (.deb) package named ``singularity-container-<version>-<system>.deb``. If found, download it and install it, either using a graphical tool, or the following commandline::

        sudo dpkg -i singularity-container-*.deb

    * if no package can be found for your system, then follow `Singularity installation instructions <https://sylabs.io/guides/3.6/admin-guide/installation.html#install-from-source>`_

* Download the BrainVISA image found in http://brainvisa.info/casa-distro/releases/singularity/.
  It's a ``.sif`` file, for instance ``brainvisa-5.0.0.sif``.
  Download it in a "safe" place where it can be reused, typically in a directory ``casa_distro`` on your home directory.

* Create an installation directory for the :ref:`environment`::

    mkdir $HOME/casa_distro/brainvisa-5.0.0

* Execute the container image it using Singularity, with an option to tell it to run its setup procedure. The installation directory should be passed::

    singularity run -B $HOME/casa_distro/brainvisa-5.0.0:/casa/setup $HOME/casa_distro/brainvisa-5.0.0.sif

* Python >= 2.7 is necessary to run the ``bv`` command. Python is usually installed on most Linux distributions. To check its installation, open a terminal and type: ``python`` (you can leave the interpreter using `<ctrl>-D` or by typing `exit()`. If it is not installed, do it (https://python.org).

* set the ``bin/`` directory of the :ref:`environment` installation directory in the ``PATH`` environment variable of your host system config, typically in ``$HOME/.bashrc`` or ``$HOME/.bash_profile`` if you are using a Unix Bash shell::

    export PATH="$HOME/casa_distro/brainvisa-5.0.0/bin:$PATH"

* Optionally, you may want to run the configuration GUI, through the ``bv`` program: as programs are actually running in a container or a virtual machine (transparently), the user may have to configure additional mount points to actually see his data and working directories from his host machine in the container. This is done graphically, simply using::

    bv

* Installation is finished, you can run programs from the container.

  There are several ways actually:

  #. The simplest way, call commands directly from the above ``PATH`` like if they were on the host machine::

        # run programs
        AimsFileInfo --info
        anatomist
        brainvisa

  2. Using :doc:`bv <bv_command>` interface to containers or :doc:`casa_distro <casa_distro_command>`:

    The :doc:`bv <bv_command>` program is found in each :ref:`environment` ``bin`` directory in order to be always compatible with this environment.

    * :doc:`bv_command` accepts an executable program name as sub-command, it allows to run programs installed inside the container, for instance::

          bv brainvisa
          bv anatomist
          bv AimsFileInfo -h

      or to open an interactive shell in the container::

          bv bash

      More options may be used. :doc:`See the complete documentation of the bv command <bv_command>`.

      Technically, ``bv`` is a simplified version of ``casa_distro`` which is contained inside a single *environment* (distribution installation) and only allows to run and configure this environment.


    * :doc:`casa_distro_command` accepts ``run`` or ``shell`` as sub-commands, they both allow to run programs installed inside the container, for instance::

          casa_distro run brainvisa
          casa_distro run anatomist
          casa_distro run AimsFileInfo -h
          casa_distro shell

      Compared to ``bv``, ``casa_distro`` allows to handle multiple :ref:`environments <environment>` (distribution installations) via parameters, and allows to setup (download/install) or remove environments or container images.

      More options may be used. :doc:`See the complete documentation of the casa_distro command <casa_distro_command>`.

  .. note::

      Note that ``bv`` is made available inside each environment (distribution installation) and makes an installation self-contained (it doesn't depend on a global host installation of ``bv`` outside of the environment directory), whereas ``casa_distro`` is cross-environments and thus may be, either installed on the host system, or picked from one particular environment, but can manage others. Note also that ``bv`` **still depends on Python which still needs to be installed and working on the host machine**.

* If you are using ``casa-distro`` using Singularity or Docker containers, graphical software need to run the containers with a graphical "bridge": a *X server* has to be running on the host system, and *OpenGL* may or may not work. The options ``gui=yes`` and ``opengl`` of casa_distro try to handle common cases, possibly using Nvidia proprietary OpenGL implementation and drivers from the host system.

  Note that the option ``gui=yes`` is now the default, thus it is not needed.

  * On MacOS: MacOS includes its own, XQuartz (which needs some setup).
  * On Windows an external X server software has to be installed.

  For OpenGL, rendering problems may differ between docker and singularity. We tried to handle some of them in the options passed to containers by casa_distro with gui active, but some additional options / tweaking may be helpful. See the :ref:`OpenGL troubleshooting <opengl_troubleshooting>` section for details.

* see the :ref:`troubleshooting` section, especially the :ref:`OpenGL troubleshooting <sing_opengl>`, :ref:`Singularity on Mac <mac_sing_troubleshooting>` and :ref:`Singularity on Windows <win_sing_troubleshooting>` subsections.

* If you want to develop software using the Casa-Distro / BrainVISA environment, read the :doc:`developer` section.


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

* If you want to develop software using the Casa-Distro / BrainVISA environment, read the :doc:`developer` section.
