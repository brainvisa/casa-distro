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

from . import six


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
        '''
        self.sections.setdefault('files', []).append(
            '%s %s' % (source_file,
                       dest_dir + '/' + osp.basename(source_file)))

    def copy_user(self, source_file, dest_dir):
        '''
        Copy a file in VM as self.user
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
        for i in ('bin', 'python', 'etc', 'share'):
            self.copy_root(osp.join(source, i), dest)
        self.run_root(("find %s -name __pycache__ -o -name '*\\.pyc' "
                       "-o -name '*~' -exec rm -Rf '{}' \\;") % dest)


def iter_images(base_directory):
    for filename in os.listdir(base_directory):
        if filename.endswith('.sif') or filename.endswith('.simg'):
            yield filename


def _singularity_build_command(cleanup=True, force=False, fakeroot=False):
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
                 cleanup,
                 force,
                 verbose, **kwargs):
    type = metadata['type']
    if type == 'system':
        shutil.copy(base, output)
    else:
        recipe = tempfile.NamedTemporaryFile(mode='wt')
        recipe.write('''Bootstrap: localimage
    From: {base}

%runscript
    export CASA_SYSTEM='{system}'
    export CASA_TYPE='{type}'
    export CASA_ENVIRONMENT='{name}'
    if [ -d /casa/setup ]; then
        /casa/casa-distro/bin/casa_distro setup_dev "$@"
    else
        . /usr/local/bin/entrypoint
    fi
'''.format(base=base,
           system=metadata['system'],
           type=type,
           name=metadata['name']))
        v = {}
        print('build_file:', build_file)
        exec(compile(open(build_file, "rb").read(), build_file, 'exec'), v, v)
        if 'install' not in v:
            raise RuntimeError(
                'No install function defined in %s' % build_file)
        install_function = v['install']

        recipe_builder = RecipeBuilder(output)
        install_function(base_dir=osp.dirname(build_file),
                         builder=recipe_builder,
                         verbose=verbose)
        recipe_builder.write(recipe)
        if verbose:
            print('---------- Singularity recipe ----------', file=verbose)
            print(open(recipe.name).read(), file=verbose)
            print('----------------------------------------', file=verbose)
            verbose.flush()
        build_command = _singularity_build_command(cleanup=cleanup,
                                                   force=force)
        if verbose:
            print('run create command:\n',
                  *(build_command + [output, recipe.name]))
        subprocess.check_call(build_command + [output, recipe.name])


def create_user_image(base_image,
                      dev_config,
                      output,
                      force,
                      base_directory,
                      verbose):
    from pprint import pprint
    pprint(dev_config)
    boom
    recipe = tempfile.NamedTemporaryFile(mode='wt')
    recipe.write('''Bootstrap: localimage
    From: {base_image}

%files
    {environment_directory}/install /casa/install

%runscript
    export CASA_SYSTEM='{system}'
    export CASA_TYPE='{type}'
    export CASA_ENVIRONMENT='{name}'
    export CASA_DISTRO='{distro}'
    if [ -d /casa/setup ]; then
        /casa/casa-distro/bin/casa_distro setup_user "$@"
    else
        /usr/local/bin/entrypoint /casa/install/bin/bv_env "$@"
    fi
'''.format(base_image=base_image,
           environment_directory=dev_config['directory'],
           system=dev_config['system'],
           type='user',
           name=dev_config['name'],
           distro=dev_config['distro']))
    recipe.flush()
    if verbose:
        print('---------- Singularity recipe ----------', file=verbose)
        print(open(recipe.name).read(), file=verbose)
        print('----------------------------------------', file=verbose)
        verbose.flush()
    build_command = _singularity_build_command(force=force, fakeroot=True)
    subprocess.check_call(build_command + [output, recipe.name])


_singularity_version = None


def singularity_major_version():
    return singularity_version()[0]


def singularity_version():
    global _singularity_version

    if _singularity_version is None:
        output = subprocess.check_output(
            ['singularity', '--version'], bufsize=-1).decode('utf-8')
        m = re.match(r'^([\d.]*).*$', output.split()[-1])
        if m:
            version = m.group(1)
            _singularity_version = [int(x) for x in version.split('.')]
        else:
            raise RuntimeError(
                'Cannot determine singularity numerical version : '
                'version string = "{0}"'.format(output))
    return _singularity_version


_singularity_run_help = None


def singularity_run_help():
    """
    Useful to get available commandline options, because they differ with
    versions and systems.
    """
    global _singularity_run_help

    if _singularity_run_help:
        return _singularity_run_help

    output = subprocess.check_output(['singularity', 'help',
                                      'run'], bufsize=-1).decode('utf-8')
    return output


def singularity_has_option(option):
    doc = singularity_run_help()
    return doc.find(' %s ' % option) >= 0 or doc.find('|%s ' % option) >= 0 \
        or doc.find(' %s|' % option) >= 0 or doc.find('|%s|') >= 0


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
    if singularity_has_option('--cleanenv'):
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
            config.setdefault('gui_env', {})
            config['gui_env']['XAUTHORITY'] = '/casa/Xauthority'

    # Make the host ssh-agent usable in the container
    if 'SSH_AUTH_SOCK' in os.environ:
        configured_env['SSH_AUTH_SOCK'] = '/casa/ssh_auth_sock'
        config['mounts']['/casa/ssh_auth_sock'] = '$SSH_AUTH_SOCK'

    home_mount = False
    host_homedir = os.path.realpath(os.path.expanduser('~'))
    for dest, source in config.get('mounts', {}).items():
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

    if singularity_version()[:3] == [3, 3, 0] and sys.platform == 'darwin':
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

    try:
        return subprocess.call(singularity, env=container_env)
    except KeyboardInterrupt:
        pass  # avoid displaying a stack trace
    finally:
        for temp in temps:
            if os.path.isdir(temp):
                shutil.rmtree(temp)
            else:
                os.unlink(temp)


def setup(type, distro, branch, system, name, base_directory, image,
          output, vm_memory, vm_disk_size, verbose, force):
    """
    Singularity specific part of setup command
    """
    raise NotImplementedError('setup is not implemented for Singularity')
