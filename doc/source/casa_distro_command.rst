=============================
Using the casa_distro command
=============================

General syntax::

    casa_distro <general options> <subcommand> <subcommand_options>

General and Common options
==========================

``-h``:
    print help, equivalent to::

        casa_distro help

``-r REPOSITORY``:
    specify the base repository directory containing build workflows (default:
    ``$HOME/casa_distro``).
    This base directory may also be specified via an `environment variable <#environment-variables>`_: ``CASA_DEFAULT_REPOSITORY``

``-v``:
    verbose mode

``--version``:
    print the version number of casa_distro and exit

Many subcommands need build_workflows selection specifications:
:ref:`how to specify a workflow <workflow_options>`

Subcommands
===========

help
----

print help about casa_distro:

.. highlight:: bash

::

    casa-distro help

or print help about a command:

::

    casa_distro help <command>

list
----

List (eventually selected) build workflows created by the `create`_ command.

create
------

Initialize a new build workflow directory. This creates a conf subdirectory with casa_distro.json, bv_maker.cfg and svn.secret files that can be edited before compilation.

run
---

Start any command in the configured container (Docker or Singularity) with the given repository configuration. example::

    casa_distro -r /home/casa run branch=bug_fix ls -als /casa

The "conf" parameter may address an additional config dictionary within the casa_distro.json config file. Typically, a test config may use a different system image (casa-test images), or options, or mounted directories.

.. _shell:

shell
-----

Start a bash shell in the configured container with the given repository configuration.

bv_maker
--------

Start bv_maker in the configured container for all the selected build workflows (by default, all created build workflows).

update_image
------------

Update the container images of (eventually selected) build workflows created by `create`_ command.

update
------

Update an existing build workflow directory. For now it only re-creates the run script in bin/casa_distro, pointing to the casa_distro command used to actually perform the update.


The complexity of arguments parsing
===================================

As casa_distro runs a chain of sub-commands, each of them passing some user-provided arguments, there may be some ambiguity on who should receive arguments. The argument delimiter ``--`` should be used appropriately.
For instance:

.. code-block:: bash

    casa_distro -r ~/casa_distro run branch=bug_fix gui=1 anatomist /casa/tests/some_image.nii

Casa_distro will run the ``anatomist`` command through Docker or Singularity, which also parses its commandline options:

* Casa_distro gets arguments ``run``, ``branch=bug_fix``, and ``gui=1``, and identifies the remaining args as the command to run.
* It invokes ``docker`` or ``singularity``, passing it some specific arguments, and the remaining ``anatomist`` and ``/casa/tests/some_image.nii``, which will be executed in a bash shell inside docker.

But the following command is ambiguous:

.. code-block:: bash

    casa_distro -r ~/casa_distro run branch=bug_fix bv_maker gui=1 --directory=/tmp

Why ?

The last argument, ``--directory=/tmp``, will be interpreted by ``casa_distro``, and you will get an error from the ``casa_distro`` command which does not know this option (but even if it did, it would not pass it to the ``bv_maker`` command). But as it is located, you likeky expected to get passed to ``bv_maker``... At the moment ``casa_distro`` intercetps all arguments in the shape ``argument=value`` for himself.

In the first example there was not this ambiguity since ``casa_distro`` did not recognize the arguments ``anatomist`` and ``/casa/tests/some_image.nii``, so passed them to the following (docker or singularity) command. But now, ``--directory=/tmp`` is understood by ``casa_distro``, used, and consumed by it.

So, how to pass the option to bv_maker ?

You have to stop arguments parsing inside ``casa_distro`` and make it pass the remaining arguments to the following command, using ``--``:

.. code-block:: bash

    casa_distro -r ~/casa_distro run branch=bug_fix gui=1 -- bv_maker --directory=/tmp

The other useful option is to pass options to the container program (docker for instance) (not to the command executed inside docker), typically to mount host directories etc. This is done using the ``container_optioins`` option, followed by more options:

.. code-block:: bash

    casa_distro -r ~/casa_distro run branch=bug_fix gui=1 container_options='-v /home/albert/my_data:/docker_data' -- anatomist /docker_data/image.nii


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


