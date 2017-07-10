=============================
Using the casa_distro command
=============================

Subcommands
===========

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

