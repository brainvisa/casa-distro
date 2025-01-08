# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

import json
import locale
import os
import os.path as osp
import sys
import re
import shutil
import subprocess
import tempfile
import getpass
import uuid
import shlex

from . import six
from .log import boolean_value
from casa_distro.defaults import default_base_directory
from .thirdparty import install_thirdparty_software

try:
    from shutil import which as find_executable
except ImportError:
    from distutils.spawn import find_executable

quote = shlex.quote


# we need support for --pwd, which appeared in Singularity 3.1
MINIMUM_SINGULARITY_VERSION = (3, 1, 0)


class RecipeBuilder:

    '''
    Class to interact with an existing VirtualBox machine.
    This machine is supposed to be based on a casa_distro system image.

    Needs rsync installed on the host system to perform copies which manage
    symlinks.
    '''

    def __init__(self, name):
        self.name = name
        self.tmp_dir = None
        self.user = None
        self.sections = {}
        # identify image/build with a unique identifier
        self.image_id = str(uuid.uuid4())

    def run_user(self, command):
        '''
        Run a shell command in VM as self.user
        '''
        self.sections.setdefault('post', []).append(command)

    def run_root(self, command):
        '''
        Run a shell command in VM as root
        '''
        self.sections.setdefault('post', []).append(command)

    def copy_root(self, source_file, dest_dir, preserve_symlinks=True,
                  preserve_ext_symlinks=True):
        '''
        Copy a file in VM as root

        Warning: if the target already exists and is a directory, files will be
        copied to the wrong location (inside this directory).

        Parameters
        ----------
        source_file: str
            source file or directory. If it is a directory, a recursive copy is
            performed.
        dest_dir: str
            destination directory
        preserve_symlinks: bool
            Copy symbolic links as they are (symbolic links).
        preserve_ext_symlinks: bool
            If False: Copy symbolic links as symlinks only if they point inside
            the source tree. Otherwise replace them with the pointed file.
            The ``rsync`` command is used to perform this.
        '''
        if not preserve_symlinks:
            # this variant is safer
            # the files section copies do not preserve symlinks.
            self.sections.setdefault('files', []).append(
                '%s %s' % (osp.realpath(source_file),
                           dest_dir + '/' + osp.basename(source_file)))
        else:
            self.sections.setdefault('setup', []).append(
                'if [ ! -d ${SINGULARITY_ROOTFS}/' + dest_dir + ' ]; then '
                'mkdir -p ${SINGULARITY_ROOTFS}/' + dest_dir + '; fi')
            if not preserve_ext_symlinks:
                # alternative using rsync
                self.sections.setdefault('setup', []).append(
                    'rsync -a --copy-unsafe-links %s %s'
                    % (osp.realpath(source_file),
                       '${SINGULARITY_ROOTFS}/' + dest_dir + '/'))
                if osp.basename(osp.realpath(source_file)) \
                        != osp.basename(source_file):
                    self.sections.setdefault('setup', []).append(
                        'mv ${SINGULARITY_ROOTFS}/%s/%s '
                        '${SINGULARITY_ROOTFS}/%s/%s'
                        % (dest_dir, osp.basename(osp.realpath(source_file)),
                           dest_dir, osp.basename(source_file)))
            else:
                # alternative using cp -a: preserve symlinks even outside the
                # source tree
                self.sections.setdefault('setup', []).append(
                    'cp -a %s %s'
                    % (osp.realpath(source_file),
                       '${SINGULARITY_ROOTFS}/%s/%s'
                       % (dest_dir, osp.basename(source_file))))

    def extract_tar(self, source_file, dest_dir):
        ''' Extract a tar archive into the dest directory

        Returns
        -------
        list of root files / directories
        '''
        self.sections.setdefault('setup', []).append(
            'if [ ! -d ${SINGULARITY_ROOTFS}/' + dest_dir + ' ]; then '
            'mkdir -p ${SINGULARITY_ROOTFS}/' + dest_dir + '; fi')
        self.sections.setdefault('setup', []).append(
            'tar -C ${SINGULARITY_ROOTFS}/' + dest_dir
            + ' --no-same-owner -xf %s'
            % osp.realpath(source_file))

    def symlink(self, target, link_name):
        '''
        Create a symbolic link inside the VM
        '''
        self.sections.setdefault('setup', []).append(
            'ln -s %s ${SINGULARITY_ROOTFS}/%s' % (target, link_name)
        )

    def copy_user(self, source_file, dest_dir, preserve_symlinks=True,
                  preserve_ext_symlinks=True):
        '''
        Copy a file in VM as root

        Warning: if the target already exists and is a directory, files will be
        copied to the wrong location (inside this directory).

        Parameters
        ----------
        source_file: str
            source file or directory. If it is a directory, a recursive copy is
            performed.
        dest_dir: str
            destination directory
        preserve_symlinks: bool
            Copy symbolic links as they are (symbolic links).
        preserve_ext_symlinks: bool
            If False: Copy symbolic links as symlinks only if they point inside
            the source tree. Otherwise replace them with the pointed file.
            The ``rsync`` command is used to perform this.
        '''
        if not preserve_symlinks:
            # this variant is safer
            # the files section copies do not preserve symlinks.
            self.sections.setdefault('files', []).append(
                '%s %s' % (source_file,
                           dest_dir + '/' + osp.basename(source_file)))
        else:
            self.sections.setdefault('setup', []).append(
                'if [ ! -d ${SINGULARITY_ROOTFS}/' + dest_dir + ' ]; then '
                'mkdir -p ${SINGULARITY_ROOTFS}/' + dest_dir + '; fi')
            if not preserve_ext_symlinks:
                # alternative using rsync
                self.sections.setdefault('setup', []).append(
                    'rsync -a --copy-unsafe-links %s %s'
                    % (source_file, '${SINGULARITY_ROOTFS}/' + dest_dir + '/'))
            else:
                # alternative using cp -a: preserve symlinks even outside the
                # source tree
                self.sections.setdefault('setup', []).append(
                    'cp -a %s %s'
                    % (source_file, '${SINGULARITY_ROOTFS}/' + dest_dir + '/'))

    def environment(self, environment_dict):
        for variable, value in environment_dict.items():
            self.sections.setdefault('environment', []).append(
                'export {}="{}"'.format(variable, value)
            )

    def write(self, file):
        for section, lines in self.sections.items():
            print('\n%%%s' % section, file=file)
            for line in lines:
                print('   ', line, file=file)
        file.flush()

    def install_casa_distro(self, dest):
        source = osp.dirname(osp.dirname(osp.dirname(__file__)))
        for i in ('bin', 'cbin', 'python', 'etc', 'share'):
            self.copy_root(osp.join(source, i), dest)
        self.run_root(("find %s -name __pycache__ -o -name '*\\.pyc' "
                       "-o -name '*~' -exec rm -Rf '{}' \\;") % dest)


def _singularity_build_command(cleanup=True, force=False, fakeroot=True):
    build_command = []
    if not fakeroot:
        build_command += ['sudo']
        if 'SINGULARITY_TMPDIR' in os.environ:
            build_command += ['SINGULARITY_TMPDIR='
                              + os.environ['SINGULARITY_TMPDIR']]
        if 'APPTAINER_TMPDIR' in os.environ:
            build_command += ['APPTAINER_TMPDIR='
                              + os.environ['APPTAINER_TMPDIR']]
        if 'TMPDIR' in os.environ:
            build_command += ['TMPDIR=' + os.environ['TMPDIR']]
    build_command += [singularity_executable(), 'build', '--disable-cache']
    if fakeroot:
        build_command += ['--fakeroot']
    if not cleanup:
        build_command.append('--no-cleanup')
    if force:
        build_command.append('--force')
    return build_command


def create_image(base, base_metadata,
                 output, metadata,
                 image_builder,
                 cleanup='yes',
                 force='no',
                 fakeroot='yes',
                 verbose=None):
    '''
    Returns
    -------
    uuid, msg: tuple
    '''

    cleanup = boolean_value(cleanup)
    force = boolean_value(force)
    fakeroot = boolean_value(fakeroot)
    type = metadata['type']
    if type == 'system':
        shutil.copy(base, output)
        image_id = str(uuid.uuid4())
        return (image_id, None)
    else:
        recipe = tempfile.NamedTemporaryFile(mode='wt')
        recipe.write('''\
Bootstrap: localimage
    From: {base}

%runscript
    export CASA_SYSTEM='{system}'
    export CASA_TYPE='{type}'

    if [ -d /casa/setup ]; then
        /usr/local/bin/entrypoint casa_container setup_dev "$@"
    elif [ $# -ne 0 ]; then
        . /usr/local/bin/entrypoint
    elif [ "$CASA_TYPE" = dev ]; then
        # if we are invoked without any argument, and setup is not mounted,
        # display a usage message
        echo 'The Singularity image has been run without arguments, and'
        echo 'without a setup mount point.'
        echo 'This run will do nothing. If you want to setup an environment'
        echo '(install a BrainVISA development environment), then you need'
        echo 'to specify an installation directory as a mount point in the'
        echo '/casa/setup container directory. Typically, to setup into the'
        echo 'directory ~/casa_distro/brainvisa-master, run the following'
        echo 'commands:'
        echo
        echo 'mkdir -p ~/casa_distro/brainvisa-master'
        echo "mv \"${{SINGULARITY_CONTAINER:-$APPTAINER_CONTAINER}}\"" \
             "~/casa_distro/"
        echo 'cd ~/casa_distro'
        echo "singularity run -c -B ./brainvisa-master:/casa/setup \\\\"
        echo "    ${{SINGULARITY_NAME:-$APPTAINER_NAME}} distro=core"
        echo
        echo 'If you have already setup such an environment, you should'
        echo 'run the image using appropriate options, mount points, and'
        echo 'a command to run (bash for instance).'
        echo 'This is normally done using the 'bv' command found in the'
        echo 'bin/ directory of the install environment directory.'
        echo '(the 'bv' command needs Python language installed):'
        echo
        echo '~/casa_distro/brainvisa-master/bin/bv bash'
        echo
        echo 'Please visit https://brainvisa.info/ for complete help.'
    elif [ "$CASA_TYPE" = run ]; then
        echo 'This casa-run image is not intended to be used directly,'
        echo 'but as an intermediate building block for the creation'
        echo 'of the casa-dev images or user images using casa-distro.'
        echo
        echo 'Please visit https://brainvisa.info/ for complete help.'
    fi
'''.format(base=base,  # noqa: E501
           system=metadata['system'],
           type=type))

        installer = RecipeBuilder(output)
        installer.image_version = metadata['image_version']
        installer.metadata = metadata
        for step in image_builder.steps:
            if verbose:
                print('Performing:', step.__doc__, file=verbose)
            step(base_dir=image_builder.build_dir,
                 builder=installer)
        installer.write(recipe)
        if verbose:
            print('---------- Singularity recipe ----------', file=verbose)
            print(open(recipe.name).read(), file=verbose)
            print('----------------------------------------', file=verbose)
            verbose.flush()
        build_command = _singularity_build_command(cleanup=cleanup,
                                                   force=force,
                                                   fakeroot=fakeroot)
        if verbose:
            print('run create command:\n',
                  *(build_command + [output, recipe.name]))
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
                      % (singularity_name(), getpass.getuser()),
                      file=sys.stderr)
                print(file=sys.stderr)
            raise

        return (installer.image_id, None)


def create_user_image(base_image,
                      dev_config,
                      version,
                      output,
                      force='no',
                      fakeroot='yes',
                      base_directory=default_base_directory,
                      verbose=None,
                      install_thirdparty='all',
                      cleanup=True):
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

    if [ -d /casa/setup ]; then
        /casa/casa-distro/cbin/casa_container setup_user "$@"
    elif [ $# -ne 0 ]; then
        if [ -f /casa/host/install/bin/bv_env ]; then
            # try r/w install
            /usr/local/bin/entrypoint /casa/host/install/bin/bv_env "$@"
        elif [ -f /casa/install/bin/bv_env ]; then
            # otherwise use the builtin (read-only) install in the image
            /usr/local/bin/entrypoint /casa/install/bin/bv_env "$@"
        else
            # fall back to no bv_env if it is missing
            /usr/local/bin/entrypoint "$@"
        fi
    else
        echo 'The Singularity image has been run without arguments, and'
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
        echo "singularity run -c -B .:/casa/setup" \
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

    rb = RecipeBuilder(output)
    rb.copy_root(dev_config['directory'] + '/install', '/casa')

    temps = install_thirdparty_software(install_thirdparty, rb)
    try:
        # # replace the python symlink (not needed any longer as copy_root here
        # # preserves all symlinks)
        # py_exe = osp.join(dev_config['directory'], 'install/bin/python')
        # if osp.exists(py_exe) and osp.islink(py_exe):
        #     py_link = os.readlink(py_exe)
        #     rb.run_root('ln -sf %s /casa/install/bin/python' % py_link)
        rb.install_casa_distro('/casa/casa-distro')
        rb.run_user('if [ -f /casa/install/share/brainvisa-share-*/'
                    'database-*.sqlite ]; '
                    'then touch /casa/install/share/brainvisa-share-*/'
                    'database-*.sqlite; fi')
        rb.run_user('echo "{\\"image_id\\": \\"%s\\"}" > /casa/image_id'
                    % rb.image_id)

        rb.write(recipe)
        recipe.flush()

        if verbose:
            print('---------- Singularity recipe ----------', file=verbose)
            print(open(recipe.name).read(), file=verbose)
            print('----------------------------------------', file=verbose)
            verbose.flush()
        build_command = _singularity_build_command(force=force,
                                                   fakeroot=fakeroot,
                                                   cleanup=cleanup)
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
                      % (singularity_name(), getpass.getuser()),
                      file=sys.stderr)
                print(file=sys.stderr)
            raise

        return (rb.image_id, None)
    finally:
        for d in temps:
            shutil.rmtree(d)


_singularity_raw_version = None


def check_singularity_version():
    """Check if Singularity is recent enough.

    A warning message is printed to stderr if Singularity is too old.
    """
    raw_version = singularity_raw_version()
    if raw_version.startswith('apptainer'):
        # We support every version of apptainer
        return True
    # We are on Singularity (not apptainer), check the version
    m = re.search(r'([0-9]+(\.[0-9]+)*)', raw_version)
    if m:
        version = m.group(1)
        version_tuple = tuple(int(x) for x in version.split('.'))
    else:
        raise RuntimeError(
            'Cannot determine singularity numerical version : '
            'version string = "{0}"'.format(raw_version))
    if version_tuple < MINIMUM_SINGULARITY_VERSION:
        print('Your version of Singularity ({0}) is not supported, '
              'please install Singularity {1} or later '
              '(see https://brainvisa.info/).'
              .format(
                  raw_version,
                  '.'.join(str(i) for i in MINIMUM_SINGULARITY_VERSION),
              )
              , file=sys.stderr)
        return False
    return True


# These variables take different values if we are running Singularity or
# Apptainer.
_singularity_executable = None
_singularity_name = None
_envvar_prefix = None


def singularity_executable(exit_if_missing=True):
    global _singularity_executable
    if not _singularity_executable:
        _singularity_executable = find_executable('apptainer')
    if not _singularity_executable:
        _singularity_executable = find_executable('singularity')
    if not _singularity_executable:
        if exit_if_missing:
            sys.exit(
                'Cannot find singularity nor apptainer on the PATH. You need '
                'to install Apptainer or Singularity in order to use '
                'BrainVISA, see https://brainvisa.info/ for detailed '
                'instructions.'
            )
    return _singularity_executable


def singularity_name():
    global _singularity_name
    if _singularity_name is None:
        if singularity_executable().endswith('apptainer'):
            _singularity_name = 'apptainer'
        else:
            _singularity_name = 'singularity'
    return _singularity_name


def envvar_prefix():
    if _singularity_name is None:
        if singularity_executable().endswith('apptainer'):
            _envvar_prefix = 'APPTAINER'
        else:
            _envvar_prefix = 'SINGULARITY'
    return _envvar_prefix


def singularity_raw_version():
    global _singularity_raw_version
    if _singularity_raw_version is None:
        output = subprocess.check_output(
            [singularity_executable(), '--version'],
            universal_newlines=True,  # backward-compatible text=True
            bufsize=-1,
        )
        _singularity_raw_version = output.strip()
    return _singularity_raw_version


def _X_has_proprietary_nvidia():
    """Test if the X server is configured for the proprietary NVidia driver.
    """
    try:
        with open(os.devnull, 'w') as devnull:
            stdoutdata = subprocess.check_output('xdpyinfo', bufsize=-1,
                                                 stderr=devnull,
                                                 universal_newlines=True)
    except (OSError, subprocess.CalledProcessError):
        # xdpyinfo cannot be found or returns an error. Stay on the safe side
        # by returning False, which triggers the fallback to software
        # rendering.
        return False
    else:
        return bool(re.search(r'^\s+NV-GLX\s*$', stdoutdata, re.M))


def _guess_opengl_mode():
    """Guess a working OpenGL configuration for opengl=auto.

    See https://github.com/brainvisa/casa-distro/issues/160 for the rationale
    behind this heuristic. If it does not work for you, please reopen that
    issue.
    """
    # Although Singularity supports --nv even without nvidia-container-cli, it
    # has been found to generate random failures at runtime, see
    # https://github.com/brainvisa/casa-distro/issues/153.
    if os.access('/dev/nvidiactl', os.R_OK | os.W_OK):
        if find_executable('nvidia-container-cli'):
            # This is the option that provides the best graphical performance
            # on NVidia hardware, and enables the use of CUDA. It seems to work
            # in all tested configurations (physical X server, CLI, Xvnc,
            # x2go).
            return 'nv'
        else:
            # Although Singularity supports --nv without nvidia-container-cli,
            # it has been found to generate random failures at runtime, see
            # https://github.com/brainvisa/casa-distro/issues/153.
            if _X_has_proprietary_nvidia():
                # In that case, we cannot fall back to 'container' because that
                # is not compatible with a X server that has the proprietary
                # NVidia module, so we have to fall back to the software-only
                # libGL.
                return 'software'
            else:
                # When nvidia-container-cli is not present, --nv causes
                # systematic segfaults on a X server that is *not* configured
                # to use the NVidia proprietary driver (such as Xvnc or x2go).
                # It seems safe to fall back to 'container' in those cases.
                return 'container'
    else:
        # When the system does not have NVidia hardware, the in-container
        # DRI-enabled OpenGL libraries seem to work in all cases. If we find
        # cases where they do not, we will need to add a quirk here.
        return 'container'


def _nv_libs_binds(image=None):
    '''Workaround for missing NVidia libraries.

    This is a workaround for some cases where Singularity with the --nv option
    fails to mount all libraries required for OpenGL programs to function
    properly, see <https://github.com/brainvisa/casa-distro/issues/153>.

    Singularity seems to miss one library (or directory):
    libnvidia-tls is present twice in their drivers, ie:
    /usr/lib/x86_64-linux-gnu/libnvidia-tls.so.390.138
    /usr/lib/x86_64-linux-gnu/tls/libnvidia-tls.so.390.138
    the latter is not mounted through nvidia-container-cli and this seems to
    cause random crashes in OpenGL applications (ramdom: from one container
    start to another, but within the same singularity run the behaviour is
    consistent).

    _nv_libs_binds() adds the additional missing lib directory (tls/)

    '''
    added_libs = []
    try:
        with open(os.devnull, 'w') as devnull:
            out_data = subprocess.check_output(
                ['nvidia-container-cli', 'list', '--libraries'],
                bufsize=-1, stderr=devnull,
                universal_newlines=True,  # return decoded str instead of bytes
            )
        libs = out_data.strip().split()
    except OSError:
        libs = []  # nvidia-container-cli not found
    except subprocess.CalledProcessError:
        libs = []  # nvidia-container-cli returns an error

    for lib in libs:
        ldir, blib = osp.split(lib)
        if blib.startswith('libnvidia-tls.so'):
            if osp.exists(osp.join(ldir, 'tls')):
                added_libs.append(osp.join(ldir, 'tls'))
            elif osp.basename(ldir) == 'tls':
                # 'tls' is already the dir for libnvidia-tls. Unfortunately
                # singularity doesn't bind it but takes its parent dir's
                # libnvidia-tls...
                added_libs.append(ldir)
            break

    if image is None:
        return added_libs

    # check libc versions and use the newer between host and container ones
    libc_path = '/usr/lib/x86_64-linux-gnu/libc.so.6'
    host_ver = None
    cont_ver = None
    if osp.exists(libc_path):
        try:
            out_data = subprocess.check_output([libc_path]).decode()
            ver_line = out_data.split('\n')[0]
            m = re.match('^.* version ([0-9.]+)\\.$', ver_line)
            if m is not None:
                ver_s = m.group(1)
                host_ver = [int(x) for x in ver_s.split('.')]
        except subprocess.CalledProcessError:
            pass
    if host_ver is not None:
        try:
            cmd = [singularity_executable(), 'exec', image, libc_path]
            out_data = subprocess.check_output(cmd).decode()
            ver_line = out_data.split('\n')[0]
            m = re.match('^.* version ([0-9.]+)\\.$', ver_line)
            if m is not None:
                ver_s = m.group(1)
                cont_ver = [int(x) for x in ver_s.split('.')]
        except subprocess.CalledProcessError:
            pass
        if cont_ver is not None and cont_ver < host_ver:
            added_libs += [
                '%s:%s' % (libc_path, libc_path),
                '/lib64/ld-linux-x86-64.so.2:/lib64/ld-linux-x86-64.so.2']

    return added_libs


def run(config, command, gui, opengl, root, cwd, env, image, container_options,
        base_directory, verbose):
    """Run a command in the Singularity container.

    Return the exit code of the command, or raise an exception if the command
    cannot be run.
    """
    temps = []

    singularity = [singularity_executable(), 'run', '--cleanenv']
    if root:
        singularity = ['sudo'] + singularity
    if cwd:
        singularity += ['--pwd', cwd]

    overlay = osp.join(config['directory'], 'overlay.img')
    if osp.exists(overlay):
        singularity += ['--overlay', overlay]

    configured_env = dict(config.get('env', {}))
    if gui:
        configured_env.update(config.get('gui_env', {}))
    if env is not None:
        configured_env.update(env)

    # This configuration key is always set by
    # casa_distro.environment.run_container
    casa_home_host_path = config['mounts']['/casa/home']
    if gui and os.environ.get('DISPLAY'):
        # Use a temporary file for each run, because a single ~/.Xauthority
        # file could be overwritten by concurrent runs... which may not all be
        # using the same X server.
        with tempfile.NamedTemporaryFile(prefix='casa-distro-',
                                         suffix='.Xauthority',
                                         delete=False) as f:
            xauthority_tmpfile = f.name
        temps.append(xauthority_tmpfile)
        retcode = subprocess.call(['xauth', 'extract', xauthority_tmpfile,
                                   os.environ['DISPLAY']], bufsize=-1)
        if retcode == 0:
            config['mounts']['/casa/Xauthority'] = xauthority_tmpfile
            configured_env['XAUTHORITY'] = '/casa/Xauthority'

    # Make the host ssh-agent usable in the container
    if 'SSH_AUTH_SOCK' in os.environ:
        configured_env['SSH_AUTH_SOCK'] = '/casa/ssh_auth_sock'
        config['mounts']['/casa/ssh_auth_sock'] = '$SSH_AUTH_SOCK'

    # workaround problem with Xvfb
    if osp.exists(osp.join(casa_home_host_path, '.varlib/xkb')):
        config['mounts']['/var/lib/xkb'] = osp.join(casa_home_host_path,
                                                    '.varlib/xkb')

    home_mount = False
    host_homedir = os.path.realpath(os.path.expanduser('~'))
    for dest, source in config.get('mounts', {}).items():
        if not source:
            continue  # a mount can be deactivated by setting it to None (null)
        source = source.format(**config)
        source = osp.expandvars(source)
        dest = dest.format(**config)
        dest = osp.expandvars(dest)
        if not os.path.exists(source):
            print('WARNING: the path {0} cannot be found on your system, '
                  'so it cannot be mounted in the container as requested by '
                  'your casa-distro configuration.'.format(source),
                  file=sys.stderr)
            continue
        singularity += ['--bind', '%s:%s' % (source, dest)]
        if source == host_homedir:
            # FIXME: the condition should actually be: if pathlib.Path(dest) ==
            # pathlib.Path(host_homedir) or pathlib.Path(dest) in
            # pathlib.Path(host_homedir).parents. The problem is that pathlib
            # is not in stdlib on Python 2. Also, beware of trailing slashes
            # (use os.path.normpath)!
            home_mount = True
    if not home_mount:
        # singularity 3 doesn't mount the home directory automatically.
        singularity += ['--bind', host_homedir]

    singularity_home = None

    # Environment variables to set in the container
    container_env = {}
    # allow to access host home directory from the container
    container_env['CASA_HOST_HOME'] = os.path.realpath(os.path.expanduser('~'))
    for name, value in configured_env.items():
        value = value.format(**config)
        value = osp.expandvars(value)
        value = six.ensure_str(value, locale.getpreferredencoding())
        if name == 'HOME':
            # Allow overriding HOME in configuration. Not recommended, as some
            # functions depend on HOME=/casa/home (e.g. automatic Xauthority).
            # Should we even allow that?
            singularity_home = value
        else:
            name = six.ensure_str(name, locale.getpreferredencoding())
            container_env[name] = value
    default_casa_home = '/casa/home'
    if singularity_home is None:
        singularity_home = default_casa_home

    # In singularity >= 3.0 host home directory is mounted
    # and configured (e.g. in environment variables) if no
    # option is given.
    singularity += ['--home',
                    '%s:%s' % (casa_home_host_path, singularity_home)]

    container_options = config.get(
        'container_options', []) + (container_options or [])

    if cwd:
        for i, opt in enumerate(container_options):
            if opt == '--pwd':
                container_options = (
                    container_options[:i] + container_options[i + 2:])
                break
    if gui:
        gui_options = config.get('container_gui_options', [])
        if gui_options:
            container_options += [osp.expandvars(i) for i in gui_options]

    if opengl == 'auto':
        opengl = _guess_opengl_mode()

    # These options/environment variables can interfere, unset them.
    while '--nv' in container_options:
        container_options.remove('--nv')
    container_env.pop('SOFTWARE_OPENGL', None)

    # determine image now
    if image is None:
        image = config.get('image')
        if image is None:
            raise ValueError(
                'image is missing from environment configuration file '
                '(casa_distro.json)')
    image = osp.join(base_directory, image)
    if not osp.exists(image):
        image = osp.join(osp.realpath(base_directory), image)
        if not osp.exists(image):
            raise ValueError("'%s' does not exist" % image)

    # if needed, write an ini.sh mounted in /casa/start_scripts
    init_script = []

    if opengl == 'nv':
        if '--nv' not in container_options:
            container_options.append('--nv')
        nv_binds = _nv_libs_binds(image=image)
        for ldir in nv_binds:
            if ':' in ldir:
                singularity += ['--bind', ldir]
            else:
                singularity += ['--bind',
                                '%s:/usr/local/lib/%s'
                                % (ldir, osp.basename(ldir))]
            init_script += [
                '# add missing nvidia libs in LD_LIBRARY_PATH',
                'export LD_LIBRARY_PATH=/usr/local/lib/tls'
                '${LD_LIBRARY_PATH+:}${LD_LIBRARY_PATH}']

    elif opengl == 'software':
        # activate mesa path in entrypoint
        container_env['SOFTWARE_OPENGL'] = '1'
        # this variable avoids to use "funny" transparent visuals
        container_env['XLIB_SKIP_ARGB_VISUALS'] = '1'
    elif opengl == 'container':
        pass  # nothing to do
    else:
        raise ValueError('Invalid value for the opengl option')

    if init_script:
        tmpdir = tempfile.mkdtemp(prefix='casa_singularity')
        script = osp.join(tmpdir, 'init.sh')
        with open(script, 'w') as f:
            print('#!/bin/bash\n', file=f)
            for line in init_script:
                print(line, file=f)
        container_options += ['--bind', '%s:/casa/start_scripts' % tmpdir]
        temps.append(tmpdir)

    singularity += container_options

    singularity += [image]
    singularity += command
    env_for_singularity = os.environ.copy()
    for n, v in six.iteritems(container_env):
        env_for_singularity[envvar_prefix() + 'ENV_' + n] = v
    if verbose:
        print('-' * 40, file=verbose)
        print('Consolidated casa_distro environment configuration:',
              file=verbose)
        json.dump(config, verbose,
                  indent=4, separators=(',', ': '), sort_keys=True)
        print('\nRunning singularity with the following command:',
              file=verbose)
        print(*("'%s'" % i for i in singularity), file=verbose)
        print('\nUsing the following environment:', file=verbose)
        for n in sorted(env_for_singularity):
            v = env_for_singularity[n]
            print('    %s=%s' % (n, v), file=verbose)
        print('-' * 40, file=verbose)
        # When verbose is stdout or stderr we must flush buffers to avoid the
        # output of the singularity command to be intermixed with verbose
        # output.
        verbose.flush()

    retval = 127
    try:
        retval = subprocess.call(singularity, env=env_for_singularity)
    except KeyboardInterrupt:
        pass  # avoid displaying a stack trace
    finally:
        for temp in temps:
            if os.path.isdir(temp):
                shutil.rmtree(temp)
            else:
                os.unlink(temp)
    if retval != 0:
        # If execution fails, the error could be due to either the container
        # command, or an incompatibility with Singularity: check the version of
        # Singularity and tell the user to upgrade if it is too old.
        check_singularity_version()
    return retval


def setup(type, distro, branch, system, name, base_directory, image,
          output, vm_memory, vm_disk_size, verbose, force):
    """
    Singularity specific part of setup command
    """
    raise NotImplementedError('setup is not implemented for Singularity')


def convert_image(source, metadata, output, convert_from, verbose=None):
    raise NotImplementedError(
        'Currently converting to singularity images is not implemented.')


def get_env_host_dir():
    ''' Get environment dir on host side, if possible
    '''
    host_dir = os.environ.get('CASA_HOST_DIR')
    if host_dir:
        return host_dir
    bind = (os.environ.get('SINGULARITY_BIND')
            or os.environ.get('APPTAINER_BIND'))
    if bind:
        binds = bind.split(',')
        for bind in binds:
            bpath = bind.split(':')
            if len(bpath) >= 2 and osp.normpath(bpath[1]) == '/casa/setup':
                return bpath[0]
    return None
