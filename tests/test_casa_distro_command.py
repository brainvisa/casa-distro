# -*- coding: utf-8 -*-

import os
import subprocess

import pytest


# Use an empty temporary HOME and unset CASA_DEFAULT_REPOSITORY (see
# conftest.py)
pytestmark = pytest.mark.usefixtures("isolate_from_home")


def test_help():
    retval = subprocess.call(['casa_distro', '--help'])
    assert retval == 0


def test_help_subcommand():
    retval = subprocess.call(['casa_distro', 'help'])
    assert retval == 0


def test_list():
    retval = subprocess.call(['casa_distro', 'list'])
    assert retval == 0


def test_distro_subcommand():
    p = subprocess.Popen(['casa_distro', 'distro'],
                         stdout=subprocess.PIPE, bufsize=-1,
                         universal_newlines=True)
    stdoutdata, _ = p.communicate()
    assert p.returncode == 0
    assert 'brainvisa' in stdoutdata
