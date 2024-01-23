# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

import json
import glob
import os
import os.path as osp
import shutil
import sys
import tempfile


all_software = {
    'spm12-standalone': None,
    'freesurfer': None,
}
default_software = {
    'spm12-standalone': None,
}
search_paths = ['/usr/local', '/drf/local', '/i2bm/local']


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
    elif install_thirdparty.startswith('file://'):
        filename = install_thirdparty[7:]
        with open(filename) as f:
            software = json.load(f)
    else:
        software_list = [x.strip() for x in install_thirdparty.split(',')]
        software = {}
        for soft_name in software_list:
            sw_path1 = [x.strip() for x in soft_name.split('=', 1)]
            sw_path = None
            if len(sw_path1) == 2:
                soft_name, sw_path = sw_path1
            software[soft_name] = sw_path
    for soft_name, sw_path in software.items():
        if sw_path is None:
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
                    'Could not find location of %s. Please specify it as '
                    '%s=<path>' % (soft_name, soft_name))

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


def install_thirdparty_software(install_thirdparty, builder):
    temps = []
    try:
        env = {}
        if install_thirdparty not in (None, 'none', 'None', 'NONE'):
            for source_dir, symlink_name, setup_scripts, env_dict \
                    in get_thirdparty_software(install_thirdparty):
                print('installing %s from %s...' % (symlink_name, source_dir))
                if source_dir.endswith('.tar') \
                        or source_dir.endswith('.tar.gz') \
                        or source_dir.endswith('.tar.bz2'):
                    builder.extract_tar(source_dir, '/usr/local')
                    source_dir = '.tar'.join(source_dir.split('.tar')[:-1])
                else:
                    builder.copy_root(source_dir, '/usr/local')
                if symlink_name and osp.basename(source_dir) != symlink_name:
                    builder.symlink(osp.basename(source_dir),
                                    osp.join('/usr/local', symlink_name))
                for script_file, script in setup_scripts.items():
                    d = tempfile.mkdtemp(prefix='casa_distro_script')
                    temps.append(d)
                    tmp_name = osp.join(d, osp.basename(script_file))
                    with open(tmp_name, 'w') as f:
                        f.write(script)
                    os.chmod(tmp_name, 0o755)
                    dest_dir = osp.dirname(script_file)
                    builder.run_root(('if [ ! -d "{dest_dir}" ]; then '
                                      'mkdir -p "{dest_dir}"; '
                                      'fi').format(dest_dir=dest_dir))
                    builder.copy_root(tmp_name, dest_dir)
                    builder.run_root('chmod a+rx "{}"'.format(script_file))
                    builder.run_user(script_file)
                env.update(env_dict)

            if env:
                builder.environment(env)
    except Exception:
        for d in temps:
            shutil.rmtree(d)
        raise
    return temps


def get_spm12_standalone_init():
    ''' SPM setup script for Axon

    Note about SPM standalone:

    Here we copy an already installed directory, which should contain both the
    SPM standalone distribution, and the matlab MCR. We have used (for now)
    SPM12-7771 and MCR v97 as in:
    https://github.com/spm/spm-docker/blob/main/matlab/singularity.def

    The MCR is "lightened" using only the core + numerics packages, not the
    whole MCR (thus is 2.6 GB instead of 5.8 GB, which will increase in v911
    and later).
    See:
    https://github.com/brainvisa/casa-distro/issues/268

    We could have run the installation procedure the "official" way as in the
    spm-docker project, but this would involve systematic download of the SPM
    distribution and of the full MCR distribution at each container build,
    which takes too much time. So for now SPM has to be pre-installed on the
    host system. We could improve the procedure and download / install it only
    if it is not already present, but this would need to handle installation
    paths, permissions (sudo to install in /usr/local for instance) etc, which
    we don't want to deal with at the moment.
    '''
    # init script for axon
    spm_script = '''#!/usr/bin/env python

import glob
import os
import sys

sys.path.insert(0, '/casa/install/python')
try:
    from brainvisa.configuration import neuroConfig
except ImportError:
    # no axon in the image
    neuroConfig = None

if neuroConfig is not None:
    conf = list(neuroConfig.readConfiguration(neuroConfig.mainPath, None, ''))
    siteOptionFile = conf[0][1]
    if siteOptionFile and os.path.exists(siteOptionFile):
        neuroConfig.app.configuration.load(siteOptionFile)

    neuroConfig.app.configuration.SPM.spm12_standalone_path = \
        '/usr/local/spm12-standalone'
    neuroConfig.app.configuration.SPM.spm12_standalone_command = \
        '/usr/local/spm12-standalone/run_spm12.sh'
    mcr_paths = glob.glob('/usr/local/spm12-standalone/mcr/v*')
    if len(mcr_paths) != 1:
        raise RuntimeError("Cannot find the MATLAB Compiler Runtime in the "
                        "expected location, please check your "
                        "install_thirdparty setting.")
    neuroConfig.app.configuration.SPM.spm12_standalone_mcr_path = mcr_paths[0]

    from pprint import pprint
    pprint(neuroConfig.app.configuration)
    neuroConfig.app.configuration.save(siteOptionFile)
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
