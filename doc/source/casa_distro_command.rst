=======================
The casa_distro command
=======================

.. highlight:: bash

.. include:: casa_distro_command_help.rst


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

.. _environment_options:

-------------------------
Environment specification
-------------------------

::

    distro=brainvisa
    branch=bug_fix
    system=ubuntu-16.04

An environment may also be given as its unique :ref:`name <env_name>` insead of the above variables.

.. _conf_option:


Environment variables
=====================

Rather than systematically passing options, some environment variables may be used to specify some parameters to `̀ casa_distro``:

::

    # replaces the -r option
    CASA_DEFAULT_REPOSITORY=/home/someone/casa_distro


Environment configuration file
==============================

The ``casa_distro.json`` file found in each :ref:`environment` subdirectory (in the ``conf`` subdirectory, actually) is a dictionary which contains variables used to define the environment, the type of container used (docker or singularity), mounted directories in the container image, etc.

Some variables substitution can occur in the string values, in a "pythonic" shape: ``%(variable)s`` will be replaced by the contents of a variable ``variable``. The following variables are available:

::

    name
    casa_distro_compatibility
    image
    system
    container_type
    branch
    mounts
    type
    distro

Moreover some environment variables replacement also takes place, in the shape: ``${VARIABLE}``.


----------------------------------
Configuration dictionary variables
----------------------------------

branch: string
    name of the source and build branch (``master``, ``latest_release``, ``release_candidate``)
container_env: dictionary
    environment variables set when running a container.
container_gui_env: dictionary
    environment variables set when running a container in gui mode.
container_gui_options: list
    list of commandline options passed to the container command in gui mode: depends on the container types.
image: string
    container image name. May be a filename, or a docker-style identifier. Docker-style identifiers are converted into filenames when using singularity, thus are still understood, so ``cati/casa-dev:ubuntu-16.04`` is a valid name.
container_options: list
    list of commandline options passed to the container command: depends on the container types, options passed to docker and to singularity actually differ.
container_type: string
    ``docker`` or ``singularity``. New container types, ``virtualbox`` for instance, may be added in future extensions.
mounts: dictionary
    mount points in the container. Directories from the host filesystem (source) are exported to the container (dest). The dictionary is a map of destination:source directories.
distro: string
    name of the distribution (set of configured sources built in the build workflow).
system: string
    system the container runs (``ubuntu-18.04``, etc.).
