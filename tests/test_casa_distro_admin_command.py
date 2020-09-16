# -*- coding: utf-8 -*-

import os
import subprocess

import pytest


# Use an empty temporary HOME and unset CASA_DEFAULT_REPOSITORY (see
# conftest.py)
pytestmark = pytest.mark.usefixtures("isolate_from_home")


def test_help():
    retval = subprocess.call(['casa_distro_admin', '--help'])
    assert retval == 0


def test_help_subcommand():
    retval = subprocess.call(['casa_distro_admin', 'help'])
    assert retval == 0
