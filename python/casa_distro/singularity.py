# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

from distutils.spawn import find_executable
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

from . import six
from .image_builder import get_image_builder
from .log import boolean_value


MINIMUM_SINGULARITY_VERSION = (3, 0, 0)


class RecipeBuilder:

    '''
    Class to interact with an existing VirtualBox machine.
    This machine is suposed to be based on a casa_distro system image.
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

    def copy_root(self, source_file, dest_dir):
        '''
        Copy a file in VM as root

        Warning: if the target already exists and is a directory, files will be
        copied to the wrong location (inside this directory).
        '''
        self.sections.setdefault('files', []).append(
            '%s %s' % (source_file,
                       dest_dir + '/' + osp.basename(source_file)))

    def copy_user(self, source_file, dest_dir):
        '''
        Copy a file in VM as self.user

        Warning: if the target already exists and is a directory, files will be
        copied to the wrong location (inside this directory).
        '''
        self.sections.setdefault('files', []).append(
            '%s %s' % (source_file,
                       dest_dir + '/' + osp.basename(source_file)))

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


def iter_images(base_directory):
    for filename in os.listdir(base_directory):
        if filename.endswith('.sif') or filename.endswith('.simg'):
            yield osp.join(base_directory, filename)


def _singularity_build_command(cleanup=True, force=False, fakeroot=True):
    build_command = []
    if not fakeroot:
        build_command += ['sudo']
        if 'SINGULARITY_TMPDIR' in os.environ:
            build_command += ['SINGULARITY_TMPDIR='
                              + os.environ['SINGULARITY_TMPDIR']]
        if 'TMPDIR' in os.environ:
            build_command += ['TMPDIR=' + os.environ['TMPDIR']]
    build_command += ['singularity', 'build', '--disable-cache']
    if fakeroot:
        build_command += ['--fakeroot']
    if not cleanup:
        build_command.append('--no-cleanup')
    if force:
        build_command.append('--force')
    return build_command


def create_image(base, base_metadata,
                 output, metadata,
                 build_file,
                 cleanup='yes',
                 force='no',
                 verbose=None):
    '''
    Returns
    -------
    uuid, msg: tuple
    '''
    cleanup = boolean_value(cleanup)
    force = boolean_value(force)
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
        echo "mv \"$SINGULARITY_CONTAINER\" ~/casa_distro/"
        echo 'cd ~/casa_distro'
        echo "singularity run -B ./brainvisa-master:/casa/setup \\\\"
        echo "    $SINGULARITY_NAME distro=opensource"
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
        image_builder = get_image_builder(build_file)

        installer = RecipeBuilder(output)
        installer.image_version = metadata['image_version']
        for step in image_builder.steps:
            if verbose:
                print('Performing:', step.__doc__, file=verbose)
            step(base_dir=osp.dirname(build_file),
                 builder=installer)
        installer.write(recipe)
        if verbose:
            print('---------- Singularity recipe ----------', file=verbose)
            print(open(recipe.name).read(), file=verbose)
            print('----------------------------------------', file=verbose)
            verbose.flush()
        fakeroot = True
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
                print('sudo singularity config fakeroot --add %s'
                      % getpass.getuser(), file=sys.stderr)
                print(file=sys.stderr)
            raise

        return (installer.image_id, None)


def create_user_image(base_image,
                      dev_config,
                      version,
                      output,
                      force,
                      base_directory,
                      verbose):
    '''
    Returns
    -------
    uuid, msg: tuple
    '''
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
        else
            # otherwise use the builtin (read-only) install in the image
            /usr/local/bin/entrypoint /casa/install/bin/bv_env "$@"
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
        echo "mv \"$SINGULARITY_CONTAINER\" ~/brainvisa-$CASA_VERSION/"
        echo "cd ~/brainvisa-$CASA_VERSION"
        echo "singularity run -B .:/casa/setup $SINGULARITY_NAME"
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
    rb.install_casa_distro('/casa/casa-distro')
    rb.run_user('touch /casa/install/share/brainvisa-share-*/'
                'database-*.sqlite')
    rb.run_user('echo "{\\"image_id\\": \\"%s\\"}" > /casa/image_id'
                % rb.image_id)
    rb.write(recipe)
    recipe.flush()

    if verbose:
        print('---------- Singularity recipe ----------', file=verbose)
        print(open(recipe.name).read(), file=verbose)
        print('----------------------------------------', file=verbose)
        verbose.flush()
    build_command = _singularity_build_command(force=force, fakeroot=True)
    # Set cwd to a directory that root is allowed to 'cd' into, to avoid a
    # permission issue with --fakeroot and NFS root_squash.
    subprocess.check_call(build_command + [output, recipe.name],
                          cwd='/')

    return (rb.image_id, None)


_singularity_raw_version = None
_singularity_run_help = None


def singularity_major_version():
    return singularity_version()[0]


def singularity_version():
    raw_version = singularity_raw_version()
    m = re.search(r'([0-9]+(\.[0-9]+)*)', raw_version)
    if m:
        version = m.group(1)
        return tuple(int(x) for x in version.split('.'))
    else:
        raise RuntimeError(
            'Cannot determine singularity numerical version : '
            'version string = "{0}"'.format(raw_version))


def singularity_raw_version():
    global _singularity_raw_version
    if _singularity_raw_version is None:
        output = subprocess.check_output(
            ['singularity', '--version'],
            universal_newlines=True,  # backward-compatible text=True
            bufsize=-1,
        )
        _singularity_raw_version = output.strip()
    return _singularity_raw_version


def singularity_run_help(error_msg=None):
    """
    Useful to get available commandline options, because they differ with
    versions and systems.
    """
    global _singularity_run_help
    if _singularity_run_help is None:
        try:
            _singularity_run_help = subprocess.check_output(
                ['singularity', 'help', 'run'],
                universal_newlines=True,  # backward-compatible text=True
                bufsize=-1,
            )
        except OSError:
            strings = {
                'singularity_version':
                    '.'.join(str(i) for i in MINIMUM_SINGULARITY_VERSION)}
            if not error_msg:
                error_msg = 'Cannot execute singularity. Please install ' \
                    'Singularity %(singularity_version)s or later (see ' \
                    'https://brainvisa.info/).' % strings
            else:
                error_msg = error_msg % strings
            sys.exit(error_msg)
    return _singularity_run_help


def singularity_has_option(option, error_msg=None):
    doc = singularity_run_help(error_msg=error_msg)
    match = re.search(r'(\s|\|)' + re.escape(option) + r'(\s|\|)', doc)
    return match is not None


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


def _nv_libs_binds():
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
    if not find_executable('nvidia-container-cli'):
        # here nvidia-container-cli is not involved, we don't handle this.
        return []

    out_data = subprocess.check_output(['nvidia-container-cli', 'list',
                                        '--libraries'], bufsize=-1)
    libs = out_data.decode(locale.getpreferredencoding()).strip().split()
    added_libs = []
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
    return added_libs


def run(config, command, gui, opengl, root, cwd, env, image, container_options,
        base_directory, verbose):
    """Run a command in the Singularity container.

    Return the exit code of the command, or raise an exception if the command
    cannot be run.
    """
    # With --cleanenv only variables prefixd by SINGULARITYENV_ are transmitted
    # to the container
    temps = []

    singularity = ['singularity', 'run']
    if singularity_has_option(
            '--cleanenv', error_msg=config.get('container_failure_message',
                                               None)):
        singularity.append('--cleanenv')
    if cwd and singularity_has_option('--pwd'):
        singularity += ['--pwd', cwd]

    if root:
        singularity = ['sudo'] + singularity

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
    if not home_mount and singularity_major_version() > 2:
        # singularity 3 doesn't mount the home directory automatically.
        singularity += ['--bind', host_homedir]

    singularity_home = None

    # Creates environment with variables prefixed by SINGULARITYENV_
    # with --cleanenv only these variables are given to the container
    container_env = os.environ.copy()
    # allow to access host home directory from the container
    container_env['SINGULARITYENV_CASA_HOST_HOME'] \
        = os.path.realpath(os.path.expanduser('~'))
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
            singularityenv_name = six.ensure_str('SINGULARITYENV_' + name,
                                                 locale.getpreferredencoding())
            container_env[singularityenv_name] = value
    default_casa_home = '/casa/home'
    if singularity_home is None:
        singularity_home = default_casa_home

    if singularity_has_option('--home'):
        # In singularity >= 3.0 host home directory is mounted
        # and configured (e.g. in environment variables) if no
        # option is given.
        singularity += ['--home',
                        '%s:%s' % (casa_home_host_path, singularity_home)]
    else:
        container_env['SINGULARITYENV_HOME'] = singularity_home
        singularity += ['--bind',
                        '%s:%s' % (casa_home_host_path, singularity_home)]

    container_options = config.get(
        'container_options', []) + (container_options or [])

    if cwd:
        for i, opt in enumerate(container_options):
            if opt == '--pwd' and singularity_has_option('--pwd'):
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
    container_env.pop('SINGULARITYENV_SOFTWARE_OPENGL', None)

    # if needed, write an ini.sh mounted in /casa/start_scripts
    init_script = []

    if opengl == 'nv':
        if '--nv' not in container_options:
            container_options.append('--nv')
        nv_binds = _nv_libs_binds()
        for ldir in nv_binds:
            singularity += ['--bind',
                            '%s:/usr/local/lib/%s'
                            % (ldir, osp.basename(ldir))]
            init_script += [
                '# add missing nvidia libs in LD_LIBRARY_PATH',
                'export LD_LIBRARY_PATH=/usr/local/lib/tls'
                '${LD_LIBRARY_PATH+:}${LD_LIBRARY_PATH}']

    elif opengl == 'software':
        # activate mesa path in entrypoint
        container_env['SINGULARITYENV_SOFTWARE_OPENGL'] = '1'
        # this variable avoids to use "funny" transparent visuals
        container_env['SINGULARITYENV_XLIB_SKIP_ARGB_VISUALS'] = '1'
    elif opengl == 'container':
        pass  # nothing to do
    else:
        raise ValueError('Invalid value for the opengl option')

    if singularity_version()[:3] == (3, 3, 0) and sys.platform == 'darwin':
        # the beta of singularity 3.3 for Mac doesn't pass envars in any way
        # (no --env option, --home doesn't work, SINGULARITYENV_something vars
        # are not transmitted). We work around this using a mount and a bash
        # script. Bidouille bidouille... ;)
        forbidden = set(['HOME', 'SINGULARITYENV_HOME', 'PWD', 'PATH',
                         'LD_LIBRARY_PATH', 'PYTHONPATH'])
        for var, value in container_env.items():
            if var not in forbidden:
                if var.startswith('SINGULARITYENV_'):
                    init_script.append('export %s="%s"'
                                       % (var[15:], value))
                else:
                    init_script.append('export %s="%s"' % (var, value))
        # --home does not work either
        init_script.append('export HOME=%s' % singularity_home)

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

    if image is None:
        image = config.get('image')
        if image is None:
            raise ValueError(
                'image is missing from environment configuration file '
                '(casa_distro.json)')
        image = osp.join(base_directory, image)
        if not osp.exists(image):
            raise ValueError("'%s' does not exist" % image)
    singularity += [image]
    singularity += command
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
        for n in sorted(container_env):
            v = container_env[n]
            print('    %s=%s' % (n, v), file=verbose)
        print('-' * 40, file=verbose)
        # When verbose is stdout or stderr we must flush buffers to avoid the
        # output of the singularity command to be intermixed with verbose
        # output.
        verbose.flush()

    retval = 127
    try:
        retval = subprocess.call(singularity, env=container_env)
    except KeyboardInterrupt:
        pass  # avoid displaying a stack trace
    finally:
        for temp in temps:
            if os.path.isdir(temp):
                shutil.rmtree(temp)
            else:
                os.unlink(temp)
    if retval == 255:
        # This exit code is returned by Singularity 2 when it is given a .sif
        # image.
        if singularity_version() < MINIMUM_SINGULARITY_VERSION:
            print('Your version of Singularity ({0}) is not supported, '
                  'please install Singularity {1} or later '
                  '(see https://brainvisa.info/).'
                  .format(
                      singularity_raw_version(),
                      '.'.join(str(i) for i in MINIMUM_SINGULARITY_VERSION),
                  )
                  , file=sys.stderr)
    return retval


def setup(type, distro, branch, system, name, base_directory, image,
          output, vm_memory, vm_disk_size, verbose, force):
    """
    Singularity specific part of setup command
    """
    raise NotImplementedError('setup is not implemented for Singularity')
