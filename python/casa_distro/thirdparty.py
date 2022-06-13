# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

import os.path as osp
import glob
import sys


all_software = ['spm12-standalone', ]
search_paths = ['/usr/local', '/i2bm/local']


def get_thirdparty_software(install_thirdparty):
    if install_thirdparty.lower() == 'all':
        software = all_software
    else:
        software = [x.strip() for x in install_thirdparty.split(',')]
    for soft_name in software:
        sw_path1 = [x.strip() for x in soft_name.split('=')]
        sw_path = None
        if len(sw_path1) == 2:
            soft_name, sw_path = sw_path1
        else:
            for sp in search_paths:
                if osp.exists(osp.join(sp, soft_name)):
                    sw_glob = [osp.join(sp, soft_name)]
                else:
                    sw_glob = glob.glob(osp.join(sp, '%s*', soft_name))
                if sw_glob:
                    sw_path = osp.realpath(sorted(sw_glob)[0])
                    break
        if sw_path is None:
            raise ValueError(
                'Could not find location of %s. Please specify it as %s=<path>'
                % (soft_name, soft_name))

        init_fn = getattr(sys.modules[__name__],
                          'get_%s_init' % soft_name.replace('-', '_'),
                          None)
        if init_fn:
            scripts = init_fn()
        else:
            scripts = {}
        yield sw_path, soft_name, scripts


def get_spm12_standalone_init():
    # init script for axon
    spm_script = '''#!/usr/bin/env python

import sys
sys.path.insert(0, '/casa/install/python')
from brainvisa.configuration import neuroConfig
import glob
import os

conf = list(neuroConfig.readConfiguration(neuroConfig.mainPath, None, ''))
siteOptionFile = conf[0][1]
if siteOptionFile and os.path.exists(siteOptionFile):
    neuroConfig.app.configuration.load(siteOptionFile)

neuroConfig.app.configuration.SPM.spm12_standalone_path = \
    '/usr/local/spm12-standalone'
neuroConfig.app.configuration.SPM.spm12_standalone_command = \
    '/usr/local/spm12-standalone/run_spm12.sh'
neuroConfig.app.configuration.SPM.spm12_standalone_mcr_path = \
    glob.glob('/usr/local/spm12-standalone/mcr/v*')[0]


neuroConfig.app.configuration.save(siteOptionFile)
'''
    scripts = {'/casa/install/templates/brainvisa/spm.py': spm_script}

    return scripts
