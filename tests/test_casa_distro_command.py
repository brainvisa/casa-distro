# -*- coding: utf-8 -*-

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


@pytest.mark.parametrize("subcommand", [
    'help',
    'distro',
    'list',
    'run',
    'pull_image',
    'list_images',
    'shell',
    'mrun',
    'bv_maker',
    'clean_images',
])
def test_help_of_subcommands(subcommand):
    p = subprocess.Popen(['casa_distro', 'help', subcommand],
                         stdout=subprocess.PIPE, bufsize=-1,
                         universal_newlines=True)
    stdoutdata, _ = p.communicate()
    assert p.returncode == 0
    assert subcommand in stdoutdata


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
