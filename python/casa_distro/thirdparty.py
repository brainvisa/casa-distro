# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

import os.path as osp
import glob
import sys


all_software = ['spm12-standalone', 'freesurfer']
default_software = ['spm12-standalone', ]
search_paths = ['/usr/local', '/i2bm/local']


def get_thirdparty_software(install_thirdparty='default'):
    '''
    Iterate over thirdparty software, either given in the install_thirdparty
    parameter, or using a default list.

    Parameters
    ----------
    install_thirdparty: str
        software to be found. If 'default', the default list
        (``default_software``) will be used instead. If 'all', the complete
        list (``all_software``) will be used. Otherwise it is a coma-
        separated list of software names. Each can be provided a source
        installation directory on the host, separated with a ``=`` sign. Ex::

            'spm12-standalone=/opt/spm12-standalone,freesurfer'

        When no path is specified, it will be looked for in a search path list
        (``search_paths``).

    Yields
    ------
    sw_path:    str
        path of the detected software
    soft_bame:  str
        name (and main directory) of the software
    scripts:    dict
        scripts that should be run inside the container to install the software
        or set it up in other software (like axon). The dict keys are the
        install path inside the container, and the value is the script to be
        run there, in a string.
    env:    dict
        environment variables to be set in the container in order to make the
        software work.

    '''
    if install_thirdparty.lower() == 'all':
        software = all_software
    elif install_thirdparty.lower() == 'default':
        software = default_software
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

        env_fn = getattr(sys.modules[__name__],
                         'get_%s_env' % soft_name.replace('-', '_'),
                         None)
        if env_fn:
            env = env_fn()
        else:
            env = {}

        yield sw_path, soft_name, scripts, env


def get_spm12_standalone_init():
    ''' SPM setup script for Axon
    '''
    # init script for axon
    spm_script = '''#!/usr/bin/env python

import sys
sys.path.insert(0, '/casa/install/python')
try:
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

except ImportError:
    # no axon in the image
    pass
'''
    scripts = {'/casa/install/templates/brainvisa/spm.py': spm_script}

    return scripts


def get_spm12_standalone_env():
    ''' SPM env variables
    '''
    # env variables for SPM
    # (see https://github.com/brainvisa/casa-distro/issues/268)
    env = {'SPM_HTML_BROWSER': '0'}
    return env


def get_freesurfer_init():
    ''' Freesurfer setup script for Axon
    '''
    # init script for axon
    fs_script = '''#!/usr/bin/env python

import sys
sys.path.insert(0, '/casa/install/python')
try:
    from brainvisa.configuration import neuroConfig
    import glob
    import os
    from brainvisa.configuration.freesurfer_configuration import \
        FreeSurferConfiguration

    conf = list(neuroConfig.readConfiguration(neuroConfig.mainPath, None, ''))
    siteOptionFile = conf[0][1]
    if siteOptionFile and os.path.exists(siteOptionFile):
        neuroConfig.app.configuration.load(siteOptionFile)

    if 'freesurfer' not in neuroConfig.app.configuration.signature:
        neuroConfig.app.configuration.add('freesurfer',
                                          FreeSurferConfiguration())

    neuroConfig.app.configuration.freesurfer.freesurfer_home_path = \
        '/usr/local/freesurfer'
    neuroConfig.app.configuration.freesurfer.subjects_dir_path = \
        '/usr/local/freesurfer/subjects'

    neuroConfig.app.configuration.save(siteOptionFile)

except ImportError:
    # no axon in the image
    pass
'''
    scripts = {'/casa/install/templates/brainvisa/freesurfer.py': fs_script}

    return scripts


def get_freesurfer_env():
    ''' Freesurfer env variables
    '''
    # env variables for Freesurfer
    env = {'FREESURFER_HOME': '/usr/local/freesurfer'}
    return env
