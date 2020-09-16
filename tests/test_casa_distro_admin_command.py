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


@pytest.mark.parametrize("subcommand", [
    'help',
    'create_base_image',
    'publish_base_image',
    'create_user_image',
])
def test_help_of_subcommands(subcommand):
    p = subprocess.Popen(['casa_distro_admin', 'help', subcommand],
                         stdout=subprocess.PIPE, bufsize=-1,
                         universal_newlines=True)
    stdoutdata, _ = p.communicate()
    assert p.returncode == 0
    assert subcommand in stdoutdata
