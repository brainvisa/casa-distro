# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

import glob
import os
import os.path as osp
import re
import shutil
import subprocess
import tempfile
import time
import uuid

import casa_distro.six as six
from .log import boolean_value

try:
    import configparser
except ImportError:
    # configparser is only used in admin commands, we can work with user
    # commands without it
    configparser = None

from .thirdparty import install_thirdparty_software


def vbox_manage_command(cmd_options):
    '''
    Return the command to be executed with subprocess.*call()
    to run VBoxManage (or VBoxManage.exe) command.
    '''
    if os.name == 'nt':
        from casa_distro.environment import find_in_path

        executable = find_in_path('VBoxManage.exe')
        if executable is None:
            executable = '\\Program Files\\Oracle\\VirtualBox\\VBoxManage.exe'
    else:
        executable = 'VBoxManage'
    return [executable] + cmd_options


def vbox_manage(cmd_options, output=False):
    '''
    Call VBoxManage executable with subprocess.check_call if
    output=False (the default), or with subprocess.check_output
    if output=True.
    '''
    cmd = vbox_manage_command(cmd_options)
    if output:
        return subprocess.check_output(cmd)
    else:
        subprocess.check_call(cmd)


_re_vbox_list_vms = re.compile(r'^"([^"]+)"\s+\{(.*)\}$')


def vbox_list_vms(running=False):
    '''
    Iterate over VMs defined in VirtualBox and yield their name.
    If running is True, consider only VMs that are currently running.
    '''
    global _re_vbox_list_vms

    if running:
        cmd = 'runningvms'
    else:
        cmd = 'vms'
    output = vbox_manage(['list', cmd], output=True).decode('utf8')
    for i in output.split('\n'):
        m = _re_vbox_list_vms.match(i)
        if m:
            yield m.group(1)


def create_image(base, base_metadata,
                 output, metadata,
                 image_builder,
                 memory='8192',
                 video_memory='50',
                 disk_size='131072',
                 gui='no',
                 cleanup='yes',
                 verbose=None):

    gui = boolean_value(gui)
    type = metadata['type']
    name = metadata['name']
    vdi = output[:-3] + 'vdi'
    if type == 'system':
        vm = VBoxMachine(name)
        if vm.exists():
            msg = None
            vbox_manage(['export', name, '-o', output, '--ovf20'])
        else:
            # Create a machine in VirtualBox, set some parameters and start it.
            if verbose:
                six.print_('Create Linux 64 bits virtual machine',
                           file=verbose, flush=True)
            vbox_manage(['createvm',
                         '--name', name,
                         '--ostype', 'Ubuntu_64',
                         '--register'])
            if verbose:
                six.print_('Set memory to', memory,
                           'MiB and allow booting on DVD',
                           file=verbose, flush=True)
            vbox_manage(['modifyvm', name,
                         '--memory', memory,
                         '--vram', video_memory,
                         '--boot1', 'dvd',
                         '--nic1', 'nat'])
            if verbose:
                six.print_('Create a', disk_size, 'MiB system disk in', vdi,
                           file=verbose, flush=True)
                vbox_manage(['createmedium',
                             '--filename', vdi,
                             '--size', disk_size,
                             '--format', 'VDI',
                             '--variant', 'Standard'])
            if verbose:
                six.print_('Create a SATA controller in the VM',
                           file=verbose, flush=True)
            vbox_manage(['storagectl', name,
                         '--name', '%s_SATA' % name,
                         '--add', 'sata'])
            if verbose:
                six.print_('Attach the system disk to the machine',
                           file=verbose, flush=True)
            vbox_manage(['storageattach', name,
                         '--storagectl', '%s_SATA' % name,
                         '--medium', vdi,
                         '--port', '1',
                         '--type', 'hdd'])
            if verbose:
                six.print_('Attach', base, 'to the DVD',
                           file=verbose, flush=True)
            vbox_manage(['storageattach', name,
                         '--storagectl', '%s_SATA' % name,
                         '--port', '0',
                         '--type', 'dvddrive',
                         '--medium', base])
            if verbose:
                six.print_('Start the new virtual machine',
                           file=verbose, flush=True)
            vbox_manage(['startvm', name])

            msg = '''VirtualBox machine created. Now, perform the following
            steps:

            1)  Perform Ubuntu minimal installation with an autologin account
                named "brainvisa" and with password "brainvisa"

            2)  Remove unneeded packages to minimize the system:

                    sudo apt update
                    sudo apt install aptitude zerofree
                    # Mark unneeded packages as auto-installed with Aptitude
                    sudo -E apt-get -o APT::Autoremove::SuggestsImportant=0 \\
                        -o APT::Autoremove::RecommendsImportant=0 autoremove
                    sudo apt upgrade

            3)  Add brainvisa user to group vboxsf for access to shared folders

                    sudo addgroup brainvisa vboxsf

            4)  Set the timezone to UTC:
                    sudo timedatectl set-timezone UTC

            5)  Disable automatic software update in "Update" tab of Software &
                Updates properties. Otherwise installation may fail because
                installation database is locked. Also, disable release upgrade
                prompts (Show new distribution releases: Never).

            6)  Disable screen saver.

            7)  Set root password to "brainvisa" (this is necessary to
                automatically connect to the VM to perform post-install)

            8)  Download and install VirtualBox guest additions
                (virtualbox-guest-utils and virtualbox-guest-x11)

            9)  Free disk space by cleaning configuration files and cache
                directories (can be huge, e.g. /var/lib/snapd) as well as APT
                cache files

                sudo aptitude purge ?config-files
                sudo apt clean
                sudo rm -rf /var/lib/apt/lists/*

            9) Add the keyboard selection widget to the bottom panel, and make
               sure to activate the English keyboard before exiting the VM.

            10) Shut down the VM.

            11) Follow the instructions in the vm.compress_disk_image()
                function in vbox.py to drastically reduce the size of the
                resulting image.

            12) Check and adjust the VM in VirualBox (enable 3D acceleration,
                enable RTC in UTC, check processors and memory)

            13) restart the casa_distro_admin create_base_image command to
                export the VM to OVA format

            14) You can manually remove the VM and its associated files from
                VirtualBox.
            '''
        return (str(uuid.uuid4()), msg)
    elif type in ('run', 'dev'):
        if base:
            vbox_import_image(base, name,
                              verbose=verbose)
        vbox = VBoxMachine(name)
        vbox.image_version = metadata['image_version']
        vbox.install(image_builder=image_builder,
                     verbose=verbose,
                     gui=gui)
        vbox.stop(verbose=verbose)
        vm.compress_disk_image()
        vbox.export(output=output, verbose=verbose)
        vbox.remove(delete=True, verbose=verbose)

        return (vbox.image_id, None)

    else:
        raise NotImplementedError('Creation of image of type {0} is not yet '
                                  'implemented for VirtualBox'.format(type))


def create_user_image(base_image,
                      dev_config,
                      version,
                      output,
                      force,
                      base_directory,
                      verbose,
                      install_thirdparty='all',
                      cleanup=True):
    install_dir = osp.join(dev_config['directory'], 'install')
    vm_name = osp.splitext(osp.basename(output))[0]
    vm = VBoxMachine(vm_name)
    if vm.exists():
        raise RuntimeError(
            "VirtualBox already has a VM named {0}. Use the following "
            "command to remove it : VBoxManage unregistervm '{0}'. Add the "
            "-delete option to remove associated files (be sure of what you "
            "do). If it is running, you can switch it off with : VBoxManage "
            "controlvm '{0}' poweroff".format(vm_name))
    vbox_import_image(base_image, vm_name, verbose=verbose)
    vm.start_and_wait(verbose=verbose)

    # Copy all VirtualBox specific files in home directory except Desktop
    # that contains only shortcuts that are managed below
    copy_to_home = osp.join(osp.dirname(osp.dirname(osp.dirname(__file__))),
                            'image-recipes', 'vbox', 'home')
    for i in os.listdir(copy_to_home):
        if i == 'Desktop':
            continue
        vm.copy_user(osp.join(copy_to_home, i), '/home/brainvisa')

    vm.run_root('apt update && apt install -y dbus-x11')

    if verbose:
        six.print_('Copying', install_dir, 'to /casa/install in VM',
                   file=verbose, flush=True)
    vm.run_user('mkdir /casa/install')
    vm.copy_user(install_dir, '/casa')
    vm.run_user("/bin/sed -i '$a if [ -e /casa/install/bin/bv_env.sh ]\\; "
                "then source /casa/install/bin/bv_env.sh /casa/install\\; fi' "
                "/home/brainvisa/.bashrc")
    vm.run_user('echo "{\\"image_id\\": \\"%s\\"}" > /casa/image_id'
                % vm.image_id)

    temps = install_thirdparty_software(install_thirdparty, vm)
    for d in temps:
        shutil.rmtree(d)

    # Copy desktop shortcut files after finding the appropriate share directory
    # containing icon files. Replace '{install_dir}' in icon Path by
    # appropriate value.
    tmp = tempfile.mkdtemp()
    try:
        d = osp.join(copy_to_home, 'Desktop')
        for i in os.listdir(d):
            c = configparser.ConfigParser()
            c.optionxform = str
            with open(osp.join(d, i)) as desktop_file:
                c.read_file(desktop_file)
            icon = glob.glob(c['Desktop Entry']['Icon'].format(
                install_dir=install_dir))
            if icon:
                icon = icon[0]
                c['Desktop Entry']['Icon'] = icon.replace(install_dir,
                                                          '/casa/install')
            f = osp.join(tmp, i)
            with open(f, 'w') as desktop_file:
                c.write(desktop_file)
            vm.copy_user(f, '/home/brainvisa/Desktop')
            # Desktop files must be made "trusted" to activate them
            cmd = ('chmod +x "/home/brainvisa/Desktop/{filename}" && '
                   'dbus-launch gio set "/home/brainvisa/Desktop/{filename}" '
                   'metadata::trusted true').format(filename=i)
            vm.run_user(cmd)
    finally:
        shutil.rmtree(tmp)

    # [2023-09-05-Nicolas SOUEDET] - The following issue may be fixed now
    # because desktop shortcut target files are now installed before
    # programatic creation and validation. Must be confirmed during
    # next release 5.2.0.
    # Desktop icons must be validated manually. Therefore, automatic saving
    # of the image is disabled until a solution is found.
    print()
    print('''Virtual machine is ready. Please activate desktop icons by
right-clicking on them and selecting "allow launching". Then press return
to save the OVA image.''')
    input('Press <return> when ready to export VirtualBox machine.')
    vm.stop(verbose=verbose)
    vm.compress_disk_image()
    vm.export(output=output, verbose=verbose)
    # vm.remove(delete=True, verbose=verbose)
    return (vm.image_id, None)


class VBoxMachine:

    '''
    Class to interact with an existing VirtualBox machine.
    This machine is supposed to be based on a casa_distro system image.
    '''

    def __init__(self, name):
        '''
        Create an interface to a VirtualBox VM.
        name is the identifier of the VM in VirtualBox.
        '''
        self.name = name
        self.user = 'brainvisa'
        self.user_password = 'brainvisa'
        self.root_password = 'brainvisa'
        self.tmp_dir = '/tmp/casa_distro'
        # identify image/build with a unique identifier
        self.image_id = str(uuid.uuid4())

    def exists(self):
        '''
        Check if a VM named self.name is defined in VirtualBox
        '''
        return self.name in vbox_list_vms()

    def running(self):
        '''
        Check if a VM named self.name is currently running in VirtualBox
        '''
        return self.name in vbox_list_vms(running=True)

    def vm_info(self):
        '''
        Return information about the VM.
        This is the result of the command :
        "VBoxManage showvminfo --machinereadable"
        that is parsed and put in a dictionary.
        '''
        output = vbox_manage(['showvminfo', '--machinereadable', self.name],
                             output=True).decode()
        result = {}
        for line in output.split('\n'):
            line = line.strip()
            if line:
                lst = line.split('=', 1)
                if len(lst) == 2:
                    key, value = lst
                    if key and key[0] == '"' and key[-1] == '"':
                        key = key[1:-1]
                    if value:
                        if value[0] == '"':
                            if value[-1] == '"':
                                value = value[1:-1]
                        else:
                            try:
                                value = int(value)
                            except ValueError:
                                pass
                    result[key] = value
        return result

    def start(self, gui=False):
        '''
        Switch the VM on. If gui=False (the default) the VM is started
        headless (i.e. without opening a window).
        '''
        if gui:
            type = 'gui'
        else:
            type = 'headless'
        vbox_manage(['startvm', self.name, '--type', type])

    def start_and_wait(self, wait=5, attempts=50, verbose=None, gui=False):
        '''
        Start the VM and wait for it to be ready to receive commands
        with run_user() or run_root().
        '''
        info = self.vm_info()
        if info['VMState'] == 'poweroff':
            if verbose:
                six.print_('Starting', self.name,
                           'and waiting for it to be ready',
                           file=verbose, flush=True)
            self.start(gui=gui)
            command = self._run_user_command('echo')
            for i in range(attempts):
                time.sleep(wait)
                if subprocess.call(command) == 0:
                    # Create temporary directory
                    self.run_root(
                        'if [ ! -e "{0}" ]; then mkdir "{0}"; fi'.format(
                            self.tmp_dir))
                    return True
        return False

    def stop(self, wait=5, attempts=50, verbose=None):
        '''
        Stop a running VM
        '''
        if self.running():
            if verbose:
                six.print_('Stopping', self.name,
                           file=verbose, flush=True)
            vbox_manage(['controlvm', self.name, 'acpipowerbutton'])
            for i in range(attempts):
                if not self.running():
                    break
                time.sleep(wait)
            else:
                raise RuntimeError('Failed to stop VM {0}'.format(self.name))

    def remove(self, delete=False, verbose=None):
        '''
        Remove a VM from VirtualBox, delete parameter allows to control the
        deletion of associated files.
        '''
        if self.exists():
            self.stop(verbose=verbose)
            if verbose:
                six.print_(('Delete' if delete else 'Unregister'), 'VM',
                           self.name, file=verbose, flush=True)
            cmd = ['unregistervm', self.name]
            if delete:
                cmd.append('--delete')
            vbox_manage(cmd)

    def _run_user_command(self, command):
        '''
        Return a command usable with subprocess module to run a shell
        command in VM as self.user
        '''
        return vbox_manage_command([
            'guestcontrol', '--username', self.user, '--password',
            self.user_password, self.name, 'run', '--', '/bin/sh', '-c',
            command])

    def run_user(self, command):
        '''
        Run a shell command in VM as self.user
        '''
        subprocess.check_call(self._run_user_command(command))

    def run_root(self, command):
        '''
        Run a shell command in VM as root
        '''
        vbox_manage(['guestcontrol', '--username', 'root',
                     '--password', self.root_password, self.name, 'run', '--',
                     '/bin/sh', '-c', 'umask 0022 && ' + command])

    def copy_root(self, source_file, dest_dir, preserve_symlinks=True,
                  preserve_ext_symlinks=True):
        '''
        Copy a file in VM as root
        '''
        # There is a problem with the mode of the files copied with
        # VBoxManage copyto as root. Therefore, the copy is done on
        # a temporary location and then copied at their final location
        # without preserving the mode.
        if osp.isdir(source_file):
            f = os.path.basename(source_file)
            # Force Linux path even if executing Python on Windows
            dest = '{}/{}'.format(self.tmp_dir, f)
            self.run_root('mkdir "{}"'.format(dest))
            vbox_manage(['guestcontrol', '--username', 'root',
                         '--password', self.root_password, self.name, 'copyto',
                         '--recursive', source_file, dest])
            self.run_root('cp -r --no-preserve=mode "{tmp}/{f}" "{dest}/{f}" '
                          '&& rm -r "{tmp}/{f}"'.format(tmp=self.tmp_dir,
                                                        f=f,
                                                        dest=dest_dir))
        else:
            vbox_manage(['guestcontrol', '--username', 'root',
                         '--password', self.root_password, self.name, 'copyto',
                         '--target-directory', self.tmp_dir + os.sep,
                         source_file])
            f = os.path.basename(source_file)
            self.run_root('cp --no-preserve=mode "{tmp}/{f}" "{dest}/{f}" '
                          '&& rm "{tmp}/{f}"'.format(tmp=self.tmp_dir,
                                                     f=f,
                                                     dest=dest_dir))

    def copy_user(self, source, dest_dir):
        '''
        Copy a file or a directory in VM as self.user
        '''
        if osp.isdir(source):
            # Some directories (in particular install directory) cannot be
            # directly copied by "VBoxManage guestcontrol copyto" command.
            # I think this is because there are too many files/directories
            # in it. Therefore, directories are copied through "tar"
            tmp = tempfile.mkdtemp()
            dir, base = osp.split(source)
            tar = osp.join(tmp, base + '.tar')
            if osp.basename(dest_dir) == '':
                dest_dir = osp.dirname(dest_dir)  # strip trailing slashes
            dest_tar = osp.join(dest_dir, base + '.tar')
            try:
                subprocess.call(['ls', '-l', tmp])
                subprocess.check_call(
                    ['tar', '-cf', tar, '--directory', dir, base])

                vbox_manage(['guestcontrol',
                             '--username', self.user,
                             '--password', self.user_password,
                             self.name,
                             'copyto', tar, dest_tar])
                vbox_manage(['guestcontrol',
                             '--username', self.user,
                             '--password', self.user_password,
                             self.name,
                             'run', '--', '/bin/tar', '-xf', dest_tar,
                             '--directory', dest_dir])
                vbox_manage(['guestcontrol',
                             '--username', self.user,
                             '--password', self.user_password,
                             self.name,
                             'rm', dest_tar])
            finally:
                shutil.rmtree(tmp)
        else:
            vbox_manage(['guestcontrol', '--username', self.user,
                        '--password', self.user_password, self.name,
                         'copyto', '--target-directory', dest_dir + os.sep,
                         source])

    def symlink(self, target, link_name):
        self.run_root('ln -s "{}" "{}"'.format(target, link_name))

    def environment(self, environment_dict):
        tmp = tempfile.NamedTemporaryFile(mode='w+')
        for variable, value in environment_dict.items():
            print('export {}="{}"'.format(variable, value), file=tmp)
        tmp.flush()
        self.copy_root(tmp.name, '/tmp')
        dest_tmp = '/tmp/{}'.format(osp.basename(tmp.name))
        self.run_root(('sed -n w/etc/profile.d/casa_distro.sh {tmp} &&'
                       ' rm {tmp}').format(tmp=dest_tmp))

    def extract_tar(self, source_file, dest_dir):
        self.copy_root(source_file, '/tmp')
        tar_tmp = '/tmp/{}'.format(osp.basename(source_file))
        self.run_root((
            'if [ ! -d "{dest_dir}" ]; then mkdir -p "{dest_dir}"; fi && '
            'tar -C {dest_dir} -xf "{tar_tmp}" && '
            'rm "{tar_tmp}"'
        ).format(tar_tmp=tar_tmp, dest_dir=dest_dir))

    def install_casa_distro(self, dest):
        """This is a no op because we do not use casa_distro with VirtualBox"""
        pass

    def install(self,
                image_builder,
                verbose=None,
                gui=False):
        """Install dependencies of casa-{image_type} image

        This method looks for a
        image-recipes/casa-{image_type}/{system}/vbox.py file and executes the
        install(base_dir, vbox, verbose) command that must be defined in this
        file.

        base_dir is the directory containing the vbox.py file
        vbox is the instance of VBoxMachine (i.e. self)
        verbose is either None or a file where to write information about the
            installation process.
        """

        self.start_and_wait(verbose=verbose, gui=gui)

        for step in image_builder.steps:
            if verbose:
                print('Performing:', step.__doc__, file=verbose)
            step(base_dir=image_builder.build_dir,
                 builder=self)

    def export(self, output, verbose=None):
        """Export VM to OVA format"""

        if verbose:
            six.print_('Exporting', self.name, 'to', output,
                       file=verbose, flush=True)
        vbox_manage(['export', self.name, '-o', output, '--ovf20'])

    def compress_disk_image(self):
        # Maybe we could automate this whole process with VBoxManage commands,
        # but that would be fragile and we do not run it often...
        print()
        print('''\
The virtual machine is ready, but it contains a lot of wasted disk space
used by deleted temporary files. Please follow these instructions to
minimize the size of the resulting image:

1. Set up a utility VM with the zerofree package installed, e.g. a casa-system
   VM or a (l)ubuntu live ISO
2. In the parameters of that VM, add the disk of {name} as a secondary hard
   disk
3. Boot the utility VM, and run this command:

       zerofree -v /dev/<hard_drive_of_{name}>

4. Shut down the utility VM.
5. Remove the disk of {name} from the configuration of the utility VM

When this is done, please press Return to save the OVA image.'''
              .format(name=self.name))
        input('Press <return> when ready to export VirtualBox machine.')


def vbox_import_image(image, vbox_machine, verbose=None):
    if verbose:
        six.print_('Importing', image, 'to', vbox_machine,
                   file=verbose, flush=True)
    vbox_manage(['import', image, '--vsys', '0', '--vmname', vbox_machine])


def vbox_import_vdi(image, vbox_machine, output,
                    verbose=None,
                    memory='8192',
                    disk_size='131072'):
    if verbose:
        six.print_('Copying', image, 'to', output,
                   file=verbose, flush=True)
    parent = osp.dirname(output)
    if not osp.exists(parent):
        os.makedirs(parent)
    if osp.exists(output):
        os.remove(output)
    vbox_manage(['clonemedium',
                 image, output,
                 '--format', 'VDI',
                 '--variant', 'Standard'])

    if verbose:
        six.print_('Create Linux 64 bits virtual machine',
                   file=verbose, flush=True)
    vbox_manage(['createvm',
                 '--name', vbox_machine,
                 '--ostype', 'Ubuntu_64',
                 '--register'])
    if verbose:
        six.print_('Set memory to', memory, 'MiB and allow booting on DVD',
                   file=verbose, flush=True)
    vbox_manage(['modifyvm', vbox_machine,
                 '--memory', memory,
                 '--boot1', 'dvd',
                 '--nic1', 'nat'])
    if verbose:
        six.print_('Create a SATA controller in the VM',
                   file=verbose, flush=True)
    vbox_manage(['storagectl', vbox_machine,
                 '--name', '%s_SATA' % vbox_machine,
                 '--add', 'sata'])
    if verbose:
        six.print_('Attach the system disk to the machine',
                   file=verbose, flush=True)
    vbox_manage(['storageattach', vbox_machine,
                 '--storagectl', '%s_SATA' % vbox_machine,
                 '--medium', output,
                 '--port', '1',
                 '--type', 'hdd'])


def convert_image(source, metadata, output, convert_from, verbose=None):
    raise NotImplementedError(
        'Currently converting to vbox images is not implemented.')
