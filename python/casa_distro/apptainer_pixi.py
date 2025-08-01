# -*- coding: utf-8 -*-

from . import singularity as apptainer
from .log import boolean_value
from casa_distro.defaults import default_base_directory
import tempfile
import subprocess
import sys
import getpass
import os.path as osp


class RecipeBuilder(apptainer.RecipeBuilder):

    def setup_pixi_env(self, install_dir):
        env_dir = install_dir
        self.run_root(
            f'if [ ! -d ${{SINGULARITY_ROOTFS}}/{env_dir} ]; then '
            f'mkdir -p  ${{SINGULARITY_ROOTFS}}/{env_dir}; fi'
        )
        self.run_root(
            f'cd ${{SINGULARITY_ROOTFS}}/{env_dir}'
        )
        self.run_user(
            '/usr/local/bin/pixi init -c pytorch -c nvidia -c conda-forge '
            '-c https://brainvisa.info/neuro-forge'
        )

        tmpscr = '/tmp/edit_pixpitoml.py'

        with open(tmpscr, 'w') as f:
            f.write(
                f'''#!/usr/bin/env python

import os.path as osp

env_dir = '{env_dir}'
pixi_toml = osp.join(env_dir, 'pixi.toml')
with open(pixi_toml) as f:
    lines = list(f.readlines())
lines.insert(1, 'channel-priority = "disabled"\\n')
lines += ['\\n',
          '[pypi-dependencies]\\n',
          'dracopy = ">=1.4.2, <2"\\n',
         ]
with open(pixi_toml, 'w') as f:
    f.write(''.join(lines))
'''
            )

        self.copy_user(tmpscr, '/tmp')
        self.run_user(
            'chmod +x /tmp/edit_pixpitoml.py')
        self.run_user(
            'python3 /tmp/edit_pixpitoml.py')
        self.run_user(
            'rm -f /tmp/edit_pixpitoml.py')

    def install_distrib(self, install_dir, distro, version, install=True):
        self.run_user(f'cd {install_dir}')
        self.run_user(
            'echo export SOMA_ROOT="$PIXI_PROJECT_ROOT" > '
            f'{install_dir}/activate.sh')
        self.run_user(
            'echo export '
            'PATH="$PATH:$CONDA_PREFIX/x86_64-conda-linux-gnu/sysroot/usr/bin"'
            f' >> {install_dir}/activate.sh')
        self.run_user(
            f'echo export LC_NUMERIC=C > {install_dir}/activate.sh')
        if install:
            self.run_user(f'/usr/local/bin/pixi add {distro}={version}')
            self.run_user('/usr/local/bin/pixi run bv_update_bin_links')

        self.run_user(
            f'if [ ! -d {install_dir}/bin ]; then '
            f'mkdir -p  {install_dir}/bin; fi'
        )
        source = osp.dirname(osp.dirname(osp.dirname(__file__)))
        self.copy_user(
            f'{source}/image-recipes/casa-pixi/5.4/bv_install_environment',
            '/casa/install/bin')


def create_user_image(base_image,
                      dev_config,
                      version,
                      output,
                      force='no',
                      fakeroot='yes',
                      base_directory=default_base_directory,
                      verbose=None,
                      install_thirdparty='all',
                      cleanup=True,
                      install=True):
    '''
    Returns
    -------
    uuid, msg: tuple
    '''
    force = boolean_value(force)
    fakeroot = boolean_value(fakeroot)
    recipe = tempfile.NamedTemporaryFile(mode='wt')
    recipe.write('''\
Bootstrap: localimage
    From: {base_image}

%runscript
    export CASA_SYSTEM='{system}'
    export CASA_TYPE='{type}'
    export CASA_DISTRO='{distro}'
    export CASA_VERSION='{version}'

    use_pixi=true
    help=false
    finished=false

    while getopts :hp opt; do
        case $opt in
            p) use_pixi="";;
            h) echo options:
            echo -h: help
            echo "-p: don't start pixi"
            ;;
            *) finished=true;;
        esac
        if [ -n "$finished" ]; then
            break
        fi
    done

    shift "$(( OPTIND - 1 ))"

    if [ -d /casa/setup ]; then
        /casa/casa-distro/cbin/casa_container setup_user "$@"
    elif [ $# -ne 0 ]; then
        if [ -f /casa/host/install/bin/bv ] && [ -n "$use_pixi" ]; then
            # try r/w install
            /usr/local/bin/entrypoint /casa/host/install/bin/bv "$@"
        elif [ -f /casa/install/bin/bv ] && [ -n "$use_pixi" ]; then
            # otherwise use the builtin (read-only) install in the image
            /usr/local/bin/entrypoint /casa/install/bin/bv "$@"
        else
            # fall back to no bv if it is missing
            /usr/local/bin/entrypoint "$@"
        fi
    else
        echo 'The Apptainer image has been run without arguments, and'
        echo 'without a setup mount point.'
        echo 'This run will do nothing. If you want to setup an environment'
        echo '(install BrainVISA), then you need to specify an'
        echo 'installation directory as a mount point in the /casa/setup'
        echo 'container directory. Typically, to setup into the host '
        echo "directory ~/brainvisa-$CASA_VERSION, run the following commands:"
        echo
        echo "mkdir -p ~/brainvisa-$CASA_VERSION"
        echo "mv \"${{SINGULARITY_CONTAINER:-$APPTAINER_CONTAINER}}\"" \
             "~/brainvisa-$CASA_VERSION/"
        echo "cd ~/brainvisa-$CASA_VERSION"
        echo "apptainer run -c -B .:/casa/setup" \
             "${{SINGULARITY_NAME:-$APPTAINER_NAME}}"
        echo
        echo 'If you have already setup such an environment, you should'
        echo 'run the image using appropriate options, mount points, and'
        echo 'a command to run (bash for instance).'
        echo 'This is normally done using the 'bv' command found in the'
        echo 'bin/ directory of the install environment directory.'
        echo '(the 'bv' command depends only on Python being installed):'
        echo
        echo "~/brainvisa-$CASA_VERSION/bin/bv bash"
        echo
        echo 'Please visit https://brainvisa.info/ for complete help.'
    fi
'''.format(base_image=base_image,
           system=dev_config['system'],
           type='user',
           distro=dev_config['distro'],
           version=version))

    distro = dev_config['distro']
    rb = RecipeBuilder(output)
    try:
        inst_dir = '/casa/install'
        rb.setup_pixi_env(inst_dir)

        rb.run_user('echo "{\\"image_id\\": \\"%s\\"}" > /casa/image_id'
                    % rb.image_id)
        rb.install_distrib(inst_dir, distro, version, install=install)

        rb.install_casa_distro('/casa/casa-distro')
        rb.write(recipe)
        recipe.flush()

        if verbose:
            print('---------- Apptainer recipe ----------', file=verbose)
            print(open(recipe.name).read(), file=verbose)
            print('----------------------------------------', file=verbose)
            verbose.flush()
        build_command = apptainer._singularity_build_command(
            force=force, fakeroot=fakeroot, cleanup=cleanup)
        # Set cwd to a directory that root is allowed to 'cd' into, to avoid a
        # permission issue with --fakeroot and NFS root_squash.
        try:
            subprocess.check_call(build_command + [output, recipe.name],
                                  cwd='/')
        except Exception:
            if fakeroot:
                print('** Image creation has failed **', file=sys.stderr)
                print('If you see an error message about fakeroot not working '
                      'on your system, then try the following command (you '
                      'need sudo permissions):', file=sys.stderr)
                print('sudo %s config fakeroot --add %s'
                      % (apptainer.singularity_name(), getpass.getuser()),
                      file=sys.stderr)
                print(file=sys.stderr)
            raise

        return (rb.image_id, None)
    finally:
        pass
