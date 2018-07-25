=============================
Using the casa_distro command
=============================

Subcommands
===========

help
----

.. highlight:: bash

::

    casa-distro help

::

    casa_distro help <command>

list
----

create
------

run
---

.. _shell:

shell
-----

bv_maker
--------

update_image
------------

specify :ref:`a workflow <workflow_options>`


The complexity of arguments parsing
===================================

As casa_distro runs a chain of sub-commands, each of them passing some user-provided arguments, there may be some ambiguity on who should receive arguments. The argument delimiter ``--`` should be used appropriately.
For instance:

.. code-block:: bash

    casa_distro -r ~/casa_distro run branch=bug_fix X=1 anatomist /casa/tests/some_image.nii

Casa_distro will run the ``anatomist`` command through Docker, docker being called in turn through a run script ``run_docker.sh``:

* Casa_distro gets arguments ``run``, ``branch=bug_fix``, and ``X=1``, and identifies the remaining args as the command to run.
* It invokes ``run_docker.sh``, passing it some specific arguments, and the remaining ``anatomist`` and ``/casa/tests/some_image.nii``
* The scripts invokes ``docker``, also passing a set of arguments to docker, then the command ``anatomist`` ``/casa/tests/some_image.nii``, which will be executed in a bash shell inside docker.

But the following command is ambiguous:

.. code-block:: bash

    casa_distro -r ~/casa_distro run branch=bug_fix X=1 anatomist -h

Why ?

The last argument, ``-h``, will be interpreted by ``casa_distro``, and you will get the help for the ``casa_distro`` command. But as it is located, you likeky expected to get the help of ``anatomist``...

In the first example there was not this ambiguity since ``casa_distro`` did not recognize the arguments ``anatomist`` and ``/casa/tests/some_image.nii``, so passed them to the following command (``run_docker.sh``), which does the same and passes it to the docker command. But now, ``-h`` is understood by ``casa_distro``, used, and consumed by it.

So, how to het help for Anatomist ?

You have to stop arguments parsing inside ``casa_distro`` and make it pass the remaining arguments to the following command, using ``--``:

.. code-block:: bash

    casa_distro -r ~/casa_distro run branch=bug_fix X=1 -- anatomist -h

Is it OK ? No, still not...

This time, ``anatomist`` ``-h`` is passed to ``run_docker.sh``, which also interprets ``-h`` for himself. So you get the help for ``run_docker.sh``... (which is actually useful, also).

So you have to provide a double ``--`` argument, so that ``run_docker.sh`` also stops parsing arguments and passes them to the docker command:

.. code-block:: bash

    casa_distro -r ~/casa_distro run branch=bug_fix X=1 -- -- anatomist -h

This time we actually get help for anatomist.

It is possible to provide arguments to ``run_docker.sh``, like ``-X11``, but this one can be passed more easily by passing ``X=1`` to ``casa_distro``. The other useful option is to pass options to docker (not to the command executed inside docker), typically to mount host directories etc. This is done using the ``-d`` option, followed by more options:

.. code-block:: bash

    casa_distro -r ~/casa_distro run branch=bug_fix X=1 -- -d -v /home/albert/my_data:/docker_data -- anatomist /docker_data/image.nii

Here,

* ``-r``, ``~/casa_distro``, ``run``, ``branch=bug_fix``, and ``X=1`` are options to ``casa_distro``
* ``-d``, ``-v``, and ``/home/albert/my_data:/docker_data`` are options to ``run_docker.sh`` (and ``-v``, and ``/home/albert/my_data:/docker_data`` are actually options passed to ``docker``)
* ``anatomist`` and ``/docker_data/image.nii`` are passed inside docker as the command to be run.


Options common to several commands
==================================

.. _workflow_options:

Workflow specification
----------------------

::

    distro=brainvisa
    branch=bug_fix
    system=ubuntu-16.04

.. _conf_option:

Alternative configurations
--------------------------

in `run`_ and `shell`_ commands

::

    conf=test


Environment variables
=====================

Rather than systematically passing options, some environment variables may be used to specify some parameters to `̀ casa_distro``:

::

    # replaces the -r option
    CASA_DEFAULT_REPOSITORY=/home/someone/casa_distro


Workflow configuration file
===========================

The ``casa_distro.json`` file found in each workflow subdirectory (in the ``conf`` subdirectory, actually) is a dictionary which contains varaibles used to define the build workflow, the type of container used (docker or singularity), mounted directories in the container image, etc.

Some variables substitution can occur in the string values, in a "pythonic" shape: ``%(variable)s`` will be replaced by the contents of a variable ``variable``. The following variables are available:

::

  build_workflow_dir
  casa_branch
  distro_name
  system

Moreover some environment variables replacement also takes place, in the shape: ``${VARIABLE}``.


Alternative configurations
--------------------------

Alternative configurations are used with the :ref:`conf option <conf_option>` in `run`_ and `shell`_ commands. They allow to change or add some configuration variables during a specific run. A typical use is to run test cases for installed packages in a different, minimal, container to check for missing libraries or files in a package.

They are specified as entries in an ``alt_configs`` sub-directory in the json configuration file. Otherwise they have the same structure as the main dictionary.

.. code-block:: json

    {
        "container_env": {
            "CASA_HOST_DIR": "%(build_workflow_dir)s",
            "HOME": "/casa/home",
            "CASA_BRANCH": "%(casa_branch)s",
            "CASA_DISTRO": "%(distro_name)s",
            "CASA_SYSTEM": "%(system)s"
        },
        "system": "ubuntu-16.04",
        "distro_source": "opensource",
        "container_gui_env": {
            "DISPLAY": "${DISPLAY}"
        },
        "container_volumes": {
            "%(build_workflow_dir)s/src": "/casa/src",
            "%(build_workflow_dir)s/pack": "/casa/pack",
            "%(build_workflow_dir)s/tests": "/casa/tests",
            "%(build_workflow_dir)s/custom/src": "/casa/custom/src",
            "%(build_workflow_dir)s/build": "/casa/build",
            "%(build_workflow_dir)s/conf": "/casa/conf",
            "%(build_workflow_dir)s/home": "/casa/home",
            "%(build_workflow_dir)s/install": "/casa/install",
            "%(build_workflow_dir)s/custom/build": "/casa/custom/build"
        },
        "container_options": [
            "--pwd",
            "/casa/home"
        ],
        "casa_branch": "bug_fix",
        "container_type": "singularity",
        "distro_name": "brainvisa",
        "container_image": "cati/casa-dev:ubuntu-16.04",
        "alt_configs": {
            "test": {
                "container_image": "cati/casa-test:ubuntu-18.04"
            }
        }
    }


