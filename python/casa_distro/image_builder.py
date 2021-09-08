# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

import json
import os
import os.path as osp
import subprocess
import sys
import tempfile


class LocalInstaller:
    '''
    class to run locally commands provided by an image builder
    '''

    def __init__(self, log_file, user='brainvisa', image_version='0.0'):
        self.name = 'local machine'
        self.user = user
        self.log_file = log_file
        self.image_id = subprocess.check_output(['hostid']).strip()
        self.image_version = image_version
        if not osp.exists(self.log_file):
            self.log = {}
        else:
            self.log = json.load(open(self.log_file))

    def run_user(self, command):
        '''
        Run a shell command as self.user
        '''
        subprocess.check_call(['sudo', '-u', self.user, 'sh', '-c', command])

    def run_root(self, command):
        '''
        Run a shell command as root
        '''
        subprocess.check_call(['sh', '-c', 'umask 0022 && ' + command])

    def copy_root(self, source_file, dest_dir):
        '''
        Copy a file as root
        '''
        self.run_root("cp -r '{}' '{}'".format(source_file, dest_dir))

    def copy_user(self, source, dest_dir):
        '''
        Copy a file or a directory as self.user
        '''
        self.run_user("cp -r '{}' '{}'".format(source, dest_dir))

    def perform_step(self, build_file, step_name):
        '''
        Perform a single installation step
        '''
        if os.getuid() != 0:
            raise SystemError('This command must be executed as root')

        builder = get_image_builder(build_file)
        for step in builder.steps:
            if step.__name__ == step_name:
                break
        else:
            raise ValueError('Image builder "{}" '
                             'has no "{}" step'.format(builder.name,
                                                       step_name))

        log = tempfile.NamedTemporaryFile()
        stdout = sys.stdout
        stderr = sys.stderr
        sys.stderr = sys.stdout = log
        try:
            step(osp.dirname(build_file), self)
            self.log.setdefault(builder.name, {})[step.__name__] = \
                {'output': open(log.name, 'r').read()}
        finally:
            sys.stderr = stderr
            sys.stdout = stdout
            log.flush()
            json.dump(self.log, open(self.log_file, 'w'))


def get_image_builder(build_file):
    '''
    Return the image builder defined in a build_image.py file
    '''
    v = {}
    exec(compile(open(build_file, "rb").read(),
                 build_file, 'exec'), v, v)
    if 'builder' not in v:
        raise RuntimeError(
            'No builder object defined in {0}'.format(build_file))
    v['builder'].build_dir = os.path.dirname(os.path.abspath(build_file))
    return v['builder']


class ImageBuilder:
    def __init__(self, name, base):
        self.name = name
        self.base = base
        self.steps = []
        self.build_dir = None  # set later by get image_builder

    def step(self, step_function):
        self.steps.append(step_function)
