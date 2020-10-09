# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

from distutils.spawn import find_executable
import json
import os
import os.path as osp
import sys
import re
import shutil
import subprocess
import tempfile


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


def iter_images(base_directory):
    for filename in os.listdir(base_directory):
        if filename.endswith('.sif') or filename.endswith('.simg'):
            yield filename


def _singularity_build_command():
    build_command = ['sudo']
    if 'SINGULARITY_TMPDIR' in os.environ:
        build_command += ['SINGULARITY_TMPDIR='
                          + os.environ['SINGULARITY_TMPDIR']]
    if 'TMPDIR' in os.environ:
        build_command += ['TMPDIR=' + os.environ['TMPDIR']]
    build_command += ['singularity', 'build', '--disable-cache']
    return build_command


def create_image(base, base_metadata,
                 output, metadata,
                 build_file,
                 cleanup,
                 verbose, **kwargs):
    type = metadata['type']
    if type == 'system':
        shutil.copy(base, output)
    else:
        recipe = tempfile.NamedTemporaryFile(mode='wt')
        recipe.write('''Bootstrap: localimage
    From: {base}

%runscript
    . /usr/local/bin/entrypoint
'''.format(base=base))
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
        build_command = _singularity_build_command()
        if not cleanup:
            build_command.append('--no-cleanup')
        if verbose:
            print('run create command:\n',
                  *(build_command + [output, recipe.name]))
        subprocess.check_call(build_command + [output, recipe.name])


def create_user_image(base_image,
                      dev_config,
                      output,
                      base_directory,
                      verbose):
    recipe = tempfile.NamedTemporaryFile(mode='wt')
    recipe.write('''Bootstrap: localimage
    From: {base_image}

%files
    {environment_directory}/host/install /casa/install

%runscript
    /usr/local/bin/entrypoint /casa/install/bin/bv_env "$@"

'''.format(base_image=base_image,
           environment_directory=dev_config['directory']))
    recipe.flush()
    if verbose:
        print('---------- Singularity recipe ----------', file=verbose)
        print(open(recipe.name).read(), file=verbose)
        print('----------------------------------------', file=verbose)
        verbose.flush()
    build_command = _singularity_build_command()
    subprocess.check_call(build_command + [output, recipe.name])


_singularity_version = None


def singularity_major_version():
    return singularity_version()[0]


def singularity_version():
    global _singularity_version

    if _singularity_version is None:
        output = subprocess.check_output(
            ['singularity', '--version']).decode('utf-8')
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
                                      'run']).decode('utf-8')
    return output


def singularity_has_option(option):
    doc = singularity_run_help()
    return doc.find(' %s ' % option) >= 0 or doc.find('|%s ' % option) >= 0


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

    casa_home_host_path = osp.join(config['directory'], 'host', 'home')

    if gui:
        xauthority = osp.expanduser('~/.Xauthority')
        # TODO: use "xauth extract" because ~/.Xauthority does not always exist
        if osp.exists(xauthority):
            shutil.copy(xauthority,
                        osp.join(casa_home_host_path, '.Xauthority'))

    home_mount = False
    host_homedir = os.path.expanduser('~')
    for dest, source in config.get('mounts', {}).items():
        source = source.format(**config)
        source = osp.expandvars(source)
        dest = dest.format(**config)
        dest = osp.expandvars(dest)
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

    configured_env = dict(config.get('env', {}))
    if gui:
        configured_env.update(config.get('gui_env', {}))
    if env is not None:
        configured_env.update(env)

    singularity_home = None

    # Creates environment with variables prefixed by SINGULARITYENV_
    # with --cleanenv only these variables are given to the container
    container_env = os.environ.copy()
    for name, value in configured_env.items():
        value = value.format(**config)
        value = osp.expandvars(value)
        if name == 'HOME':
            # Allow overriding HOME in configuration. Not recommended, as some
            # functions depend on HOME=/casa/home (e.g. automatic Xauthority).
            # Should we even allow that?
            singularity_home = value
        else:
            container_env['SINGULARITYENV_' + name] = value
    default_casa_home = '/casa/host/home'
    if singularity_home is None:
        singularity_home = default_casa_home

    if singularity_has_option('--home'):
        # In singularity >= 3.0 host home directory is mounted
        # and configured (e.g. in environment variables) if no
        # option is given.
        singularity += ['--home', singularity_home]
    else:
        container_env['SINGULARITYENV_HOME'] = singularity_home

    # The following code may prevent containers to run on some system
    # handle ~/.ssh
    # ssh_dir = osp.join(host_homedir, '.ssh')
    # if osp.isdir(ssh_dir):
    #     singularity += [
    #         '--bind',
    #         '%s:%s' % (ssh_dir, osp.join(singularity_home, '.ssh'))]

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

    if opengl == 'nv':
        if '--nv' not in container_options:
            container_options.append('--nv')
    elif opengl == 'software':
        # activate mesa path in entrypoint
        container_env['SINGULARITYENV_SOFTWARE_OPENGL'] = '1'
        # this variable avoids to use "funny" transparent visuals
        container_env['SINGULARITYENV_XLIB_SKIP_ARGB_VISUALS'] = '1'
    elif opengl == 'container':
        pass  # nothing to do
    else:
        raise ValueError('Invalid value for the opengl option')

    if 'SINGULARITYENV_PS1' not in container_env \
            and not [x for x in container_options if x.startswith('PS1=')]:
        # the prompt with singularity 3 is ugly and cannot be overriden in the
        # .bashrc of the container.
        ps1 = r'\[\033[33m\]\u@\h \$\[\033[0m\] '
        if singularity_has_option('--env'):
            container_options += ['--env', 'PS1=%s' % ps1]
        else:
            container_env['SINGULARITYENV_PS1'] = ps1
            if 'PS1' in container_env:
                del container_env['PS1']

    if singularity_version()[:3] == [3, 3, 0] and sys.platform == 'darwin':
        # the beta of singularity 3.3 for Mac doesn't pass envars in any way
        # (no --env option, --home doesn't work, SINGULARITYENV_something vars
        # are not transmitted). We work around this using a mount and a bash
        # script. Bidouille bidouille... ;)
        tmpdir = tempfile.mkdtemp(prefix='casa_singularity')
        script = osp.join(tmpdir, 'init.sh')
        forbidden = set(['HOME', 'SINGULARITYENV_HOME', 'PWD', 'PATH',
                         'LD_LIBRARY_PATH', 'PYTHONPATH'])
        with open(script, 'w') as f:
            print('#!/bin/bash\n', file=f)
            for var, value in container_env.items():
                if var not in forbidden:
                    if var.startswith('SINGULARITYENV_'):
                        print('export %s="%s"' % (var[15:], value), file=f)
                    else:
                        print('export %s="%s"' % (var, value), file=f)
            # --home does not work either
            print('export HOME=%s' % singularity_home, file=f)
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
            shutil.rmtree(temp)


def setup(type, distro, branch, system, name, base_directory, image,
          output, vm_memory, vm_disk_size, verbose, force):
    """
    Singularity specific part of setup command
    """
    raise NotImplementedError('setup is not implemented for Singularity')
