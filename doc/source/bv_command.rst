
The ``bv`` command
==================

usage: bv [-h] [-v] [command...]

Command used to start any BrainVISA related program.

Used without parameter, it starts a graphical interface
allowing the configuration of the environment.

optional arguments:
  -h, --help     show this help message and exit
  -v, --verbose

Currently bv is just a shorthand to the "casa_distro run" command, and follows the same syntax and options. In the future it will change to more "conventional" arguments syntax (say, "--opengl container" instead of "opengl=container").

See the doc in casa_distro::

    casa_distro help run
