# -*- coding: utf-8 -*-

import os
import subprocess

def test_help():
    retval = subprocess.call(['casa_distro', '--help'])
    assert retval == 0
