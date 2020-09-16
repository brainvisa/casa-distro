# -*- coding: utf-8 -*-

import os
import subprocess

import pytest

@pytest.fixture(autouse=True)
def isolate_from_home(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))


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
    retval = subprocess.call(['casa_distro', 'distro'])
    assert retval == 0
