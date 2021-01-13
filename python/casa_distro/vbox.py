# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

import os
import os.path as osp
import re
import shutil
import subprocess
import tempfile
import time

import casa_distro.six as six


def vbox_manage_command(cmd_options):
    '''
    Return the command to be executed with subprocess.*call()
    to run VBoxManage (or VBoxManage.exe) command.
    '''
    # TODO: Not implemented for Windows
    return ['VBoxManage'] + cmd_options


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
                 build_file,
                 cleanup,
                 memory,
                 disk_size,
                 gui,
                 verbose,
                 **kwargs):
    type = metadata['type']
    name = metadata['name']
    if type == 'system':
        # Create a machine in VirtualBox, set some parameters and start it.
        if verbose:
            six.print_('Create Linux 64 bits virtual machine',
                       file=verbose, flush=True)
        vbox_manage(['createvm',
                    '--name', name,
                     '--ostype', 'Ubuntu_64',
                     '--register'])
        if verbose:
            six.print_('Set memory to', memory, 'MiB and allow booting on DVD',
                       file=verbose, flush=True)
        vbox_manage(['modifyvm', name,
                    '--memory', memory,
                     '--boot1', 'dvd',
                     '--nic1', 'nat'])
        if verbose:
            six.print_('Create a', disk_size, 'MiB system disk in', output,
                       file=verbose, flush=True)
        vbox_manage(['createmedium',
                    '--filename', output,
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
                     '--medium', output,
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

        return '''VirtualBox machine created. Now, perform the following steps:
        1) Perform Ubuntu minimal installation with an autologin account named
        "brainvisa" and with password "brainvisa"

        2) Perform system updates and install packages required for kernel
        module creation :

                sudo apt update
                sudo apt upgrade
                sudo apt install gcc make perl

        3) Disable automatic software update in "Update" tab of Software &
        Updates properties. Otherwise installation may fail because
        installation database is locked.

        4) Set root password to "brainvisa" (this is necessary to automatically
        connect to the VM to perform post-install)

        5) Reboot the VM

        6) Download and install VirtualBox guest additions

        7) Shut down the VM

        8) Configure the VM in VirualBox (especially 3D acceleration,
        processors and memory)
        '''
    elif type in ('run', 'dev'):
        if base:
            vbox_import_image(base, name, output,
                              verbose=verbose,
                              memory=memory,
                              disk_size=disk_size)
        vbox = VBoxMachine(name)
        vbox.install(build_file=build_file,
                     verbose=verbose,
                     gui=gui)
    else:
        raise NotImplementedError('Creation of image of type {0} is not yet '
                                  'implemented for VirtualBox'.format(type))


def create_user_image(base_image,
                      dev_config,
                      version,
                      output,
                      base_directory,
                      verbose):
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
    vbox_import_image(base_image, vm_name, output, verbose=verbose)
    vm.start_and_wait(verbose=verbose)
    if verbose:
        six.print_('Copying', install_dir, 'to /casa/install in VM',
                   file=verbose, flush=True)
    vm.run_user('mkdir /casa/install')
    vm.copy_user(install_dir, '/casa')
    vm.run_user("/bin/sed -i '$a if [ -e /casa/install/bin/bv_env.sh ]\\; "
                "then source /casa/install/bin/bv_env.sh /casa/install\\; fi' "
                "/home/brainvisa/.bashrc")
    # vm.remove(verbose=verbose)


class VBoxMachine:

    '''
    Class to interact with an existing VirtualBox machine.
    This machine is suposed to be based on a casa_distro system image.
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
                key, value = line.split('=', 1)
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
                print('Starting', self.name, 'and waiting for it to be ready',
                      file=verbose, flush=True)
            self.start(gui=gui)
            command = self._run_user_command('echo')
            for i in range(attempts):
                time.sleep(wait)
                if subprocess.call(command) == 0:
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

    def remove(self, verbose=None):
        '''
        Remove a VM from VirtualBox without deleting the image file
        '''
        if self.exists():
            self.stop(verbose=verbose)
            if verbose:
                six.print_('Removing', self.name,
                           file=verbose, flush=True)

            vbox_manage(['unregistervm', self.name])

    def _run_user_command(self, command):
        '''
        Return a command useable with subprocess module to run a shell
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

    def copy_root(self, source_file, dest_dir):
        '''
        Copy a file in VM as root
        '''
        # There is a problem with the mode of the files copied with
        # VBoxManage copyto as root. Therefore, the copy is done on
        # a temporary location and then copied at their final location
        # without preserving the mode.
        if osp.isdir(source_file):
            dest = osp.join(self.tmp_dir, osp.basename(source_file))
            self.run_root('mkdir "{dest}"'.format(dest=dest))
            vbox_manage(['guestcontrol', '--username', 'root',
                         '--password', self.root_password, self.name, 'copyto',
                         '--recursive', source_file, dest])
            f = os.path.basename(source_file)
            self.run_root('cp -r --no-preserve=mode "{tmp}/{f}" "{dest}/{f}" '
                          '&& rm -r "{tmp}/{f}"'.format(tmp=self.tmp_dir,
                                                        f=f,
                                                        dest=dest_dir))
        else:
            vbox_manage(['guestcontrol', '--username', 'root',
                         '--password', self.root_password, self.name, 'copyto',
                         '--target-directory', self.tmp_dir, source_file])
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
                         'copyto', '--target-directory', dest_dir,
                         source])

    def install(self,
                build_file,
                verbose=None,
                gui=False):
        """Install dependencies of casa-{image_type} image

        This method look for a share/docker/casa-{image_type}/{system}/vbox.py
        file and execute the install(base_dir, vbox, verbose) command that must
        be defined in this file.

        base_dir is the directory containing the vbox.py file
        vbox is the instance of VBoxMachine (i.e. self)
        verbose is either None or a file where to write information about the
            installation process.
        """

        v = {}
        exec(compile(open(build_file, "rb").read(), build_file, 'exec'), v, v)
        if 'install' not in v:
            raise RuntimeError(
                'No install function defined in {0}'.format(build_file))
        install_function = v['install']

        self.start_and_wait(verbose=verbose, gui=gui)
        self.run_root(
            'if [ ! -e "{0}" ]; then mkdir "{0}"; fi'.format(self.tmp_dir))
        install_function(base_dir=osp.dirname(build_file),
                         builder=self,
                         verbose=verbose)


def vbox_import_image(image, vbox_machine, output,
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
