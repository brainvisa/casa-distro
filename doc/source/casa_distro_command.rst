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

bv_maker
--------

Start bv_maker in the configured container for all the selected build workflows (by default, all created build workflows).

clean_images
------------

Delete singularity images which are no longer used in any build workflow, or those listed in image_names.

create
------

Initialize a new build workflow directory. This creates a conf subdirectory with casa_distro.json, bv_maker.cfg and svn.secret files that can be edited before compilation.

create_writable_image
---------------------

Create a writable version of a Singularity image used to run containers. This allows to modify an image (for instance install custom packages). To use a writable image in a build workflow, it is necessary to edit its "casa_distro.json" file (located in the "conf" directory of the build workflow) to add ".writable" to the image name. For instance::

    "container_image": "cati/casa-dev:ubuntu-16.04.writable"

The singularity image can be identified by its Docker-like name::

    casa_distro create_writable_image cati/casa-dev:ubuntu-16.04

It is also possible to identify an image by selecting a build workflow::

    casa_distro create_writable_image distro=brainvisa branch=bug_fix

Due to Singularity security, it is necessary to be root on the host system to create an image (sudo is used for that and can ask you a password).

delete
------

Delete (physically remove files) an entire build workflow. The container image will not be erased, see clean_images for that.

example::

    casa_distro delete branch=bug_fix

By default the "interactive" mode is on, and a confirmation will be asked before proceding. If interactive is disabled, then the deletion will be done without confirmation.

list
----

List (eventually selected) build workflows created by the `create`_ command.

mrun
----

Start any command in one or several container with the given repository configuration. By default, command is executed in all existing build workflows.

example::

    # Launch bv_maker on all build workflows using any version of Ubuntu
    casa_distro mrun bv_maker system=ubuntu-*

The "conf" parameter may address an additional config dictionary within the casa_distro.json config file. Typically, a test config may use a different system image (casa-test images), or options, or mounted directories.

root_shell
----------

Start a shell with root privileges allowing to modify a writable singularity image. Before using this command, a writable image must have been created with the create_writable_image command. Using this command allows to modify the writable image (for instance to install packages). Due to Singularity security, it is necessary to be root on the host system to start a root shell within the container (sudo is used for that and can ask you a password).

The image can be identified by its Docker-like name::

    casa_distro root_shell cati/casa-dev:ubuntu-16.04

It is also possible to identify an image by selecting a build workflow::

    casa_distro root_shell distro=brainvisa branch=bug_fix

run
---

Start any command in the configured container (Docker or Singularity) with the given repository configuration. example::

    casa_distro -r /home/casa run branch=bug_fix ls -als /casa

The "conf" parameter may address an additional config dictionary within the casa_distro.json config file. Typically, a test config may use a different system image (casa-test images), or options, or mounted directories.

.. _shell:

shell
-----

Start a bash shell in the configured container with the given repository configuration.

update
------

Update an existing build workflow directory. For now it only re-creates the run script in bin/casa_distro, pointing to the casa_distro command used to actually perform the update.

update_image
------------

Update the container images of (eventually selected) build workflows created by `create`_ command.



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

This selects the appropriate sub-configuration block in the configuration file of the build workflow. See :ref:`alt_configs`


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


Configuration dictionary variables
----------------------------------

alt_configs: dictionary
    alternative configurations dictionary. see :ref:`alt_configs`.
build_workflow_dir: string
    build workflow directory
casa_branch: string
    name of the source and build branch (``bug_fix``, ``trunk``, ``latest_release``, ``release_candidate``)
container_env: dictionary
    environment variables set when running a container.
container_gui_env: dictionary
    environment variables set when running a container in gui mode.
container_gui_options: list
    list of commandline options passed to the container command in gui mode: depends on the container types.
container_image: string
    container image name. May be a filename, or a docker-style identifier. Docker-style identifiers are converted into filenames when using singularity, thus are still understood, so ``cati/casa-dev:ubuntu-16.04`` is a valid name.
container_options: list
    list of commandline options passed to the container command: depends on the container types, options passed to docker and to singularity actually differ.
container_type: string
    ``docker`` or ``singularity``. New container types, ``virtualbox`` for instance, may be added in future extensions.
container_volumes: dictionary
    mount points in the container. Directories from the host filesystem (source) are exported to the container (dest). The dictionary is a map of source:destination directories.
distro_name: string
    name of the distribution (set of configured sources built in the build workflow).
distro_source: string
    name of the distribution used to base this one on. ``brainvisa``, ``opensource``, ``cati_platform``.
init_workflow_cmd: string
    command run when initializing the build workflow. Normally none.
system: string
    system the container runs (``ubuntu-12.04``, ``ubuntu-14.04``, ``ubuntu-16.04``, ``ubuntu-18.04``, ``centos-7.4``, ``windows-7-64``).


.. _alt_configs:

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


