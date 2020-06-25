# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function

import os
import os.path as osp
import shutil
import six
import subprocess
import time

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


def create_image(base, base_metadata, 
                 output, metadata,
                 build_file,
                 memory,
                 disk_size,
                 gui,
                 verbose,
                 **kwargs):
    type = metadata['type']
    if type == 'system':
        # Create a machine in VirtualBox, set some parameters and start it.
        name = metadata['name']
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

        3) Disable automatic software update in "Update" tab of Software & Updates
        properties. Otherwise installation may fail because installation
        database is locked.

        4) Set root password to "brainvisa" (this is necessary to automatically
        connect to the VM to perform post-install)
        
        5) Reboot the VM

        6) Download and install VirtualBox guest additions

        7) Shut down the VM

        8) Configure the VM in VirualBox (especially 3D acceleration, processors
        and memory)
    '''
    else:
        raise NotImplementedError('Creation of image of type {0} is not yet '
                                  'implemented for VirtualBox'.format(type))


def vbox_create_system(image_name, iso, output, verbose,
                       memory='8192',
                       disk_size='131072'):
    '''
    Create an machine in VirtualBox, set some parameters and start it.
    
    image_name: name of the image in VirtualBox (must not exist)
    iso: name of the *.iso file containing the Ubuntu image
    output: name of the *.vdi file that will contain the resulting image 
            (must not be used in VirtualBox devices)
    memory: memory allocated to the image (default = 8 GiB)
    disk_size: maximum system disk size (default = 128 GiB)
    '''
    if verbose:
        six.print_('Create Linux 64 bits virtual machine',
                   file=verbose, flush=True)
    vbox_manage(['createvm', 
                 '--name', image_name, 
                 '--ostype', 'Ubuntu_64',
                 '--register'])
    if verbose:
        six.print_('Set memory to', memory, 'MiB and allow booting on DVD',
                   file=verbose, flush=True)
    vbox_manage(['modifyvm', image_name,
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
    vbox_manage(['storagectl', image_name,
                 '--name', '%s_SATA' % image_name,
                 '--add', 'sata'])
    if verbose:
        six.print_('Attach the system disk to the machine',
                   file=verbose, flush=True)
    vbox_manage(['storageattach', image_name,
                 '--storagectl', '%s_SATA' % image_name,
                 '--medium', output,
                 '--port', '1',
                 '--type', 'hdd'])
    if verbose:
        six.print_('Attach', iso, 'to the DVD',
                   file=verbose, flush=True)
    vbox_manage(['storageattach', image_name,
                 '--storagectl', '%s_SATA' % image_name,
                 '--port', '0',
                 '--type', 'dvddrive',
                 '--medium', iso])
    if verbose:
        six.print_('Start the new virtual machine',
                   file=verbose, flush=True)
    vbox_manage(['startvm', image_name])
    
    return '''VirtualBox machine created. Now, perform the following steps:
    1) Perform Ubuntu minimal installation with an autologin account named 
       "brainvisa" and with password "brainvisa"
    
    2) Perform system updates and install packages required for kernel 
       module creation :
            
            sudo apt update
            sudo apt upgrade
            sudo apt install gcc make perl

    3) Disable automatic software update in "Update" tab of Software & Updates
       properties. Otherwise installation may fail because installation
       database is locked.

    4) Set root password to "brainvisa" (this is necessary to automatically
       connect to the VM to perform post-install)
    
    5) Reboot the VM

    6) Download and install VirtualBox guest additions

    7) Shut down the VM

    8) Configure the VM in VirualBox (especially 3D acceleration, processors
       and memory)
'''


class VBoxMachine:
    '''
    Class to interact with an existing VirtualBox machine.
    This machine is suposed to be based on a casa_distro system image.
    '''
    
    def __init__(self, vm):
        '''
        Create an interface to a VirtualBox VM.
        vm is the identifier of the VM in VirtualBox.
        '''
        self.vm = vm
        self.user = 'brainvisa'
        self.user_password = 'brainvisa'
        self.root_password = 'brainvisa'
        self.tmp_dir = '/tmp/casa_distro'
    
                
    def vm_info(self):
        '''
        Return information about the VM.
        This is the result of the command : 
        "VBoxManage showvminfo --machinereadable"
        that is parsed and put in a dictionary.
        '''
        output = vbox_manage(['showvminfo', '--machinereadable', self.vm],
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
        vbox_manage(['startvm', self.vm, '--type', type])


    def start_and_wait(self, wait=5, attempts=50, verbose=None, gui=False):
        '''
        Start the VM and wait for it to be ready to receive commands
        with run_user() or run_root().
        '''
        info = self.vm_info()
        if info['VMState'] == 'poweroff':
            if verbose:
                six.print_('Starting', self.vm, 'and waiting for it to be ready',
                           file=verbose, flush=True)
            self.start(gui=gui)
            command = self._run_user_command('echo')
            for i in range(attempts):
                time.sleep(wait)
                if subprocess.call(command) == 0:
                    return True
        return False

            
    def _run_user_command(self, command):
        '''
        Return a command useable with subprocess module to run a shell
        command in VM as self.user
        '''
        return vbox_manage_command([
            'guestcontrol', '--username', self.user, '--password',
            self.user_password, self.vm, 'run', '--', '/bin/sh', '-c',
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
                     '--password', self.root_password, self.vm, 'run', '--', 
                     '/bin/sh', '-c', 'umask 0022 && ' + command])


    def copy_root(self, source_file, dest_dir):
        '''
        Copy a file in VM as root
        '''
        vbox_manage(['guestcontrol', '--username', 'root',
                     '--password', self.root_password, self.vm, 'copyto',
                     '--target-directory', self.tmp_dir, source_file])
        f=os.path.basename(source_file)
        self.run_root('cp --no-preserve=mode "{tmp}/{f}" "{dest}/{f}" && rm "{tmp}/{f}"'.format(
            tmp=self.tmp_dir, 
            f=f,
            dest=dest_dir))

    def copy_user(self, source_file, dest_dir):
        '''
        Copy a file in VM as self.user
        '''
        vbox_manage(['guestcontrol', '--username', self.user, 
                     '--password', self.user_password, self.vm, 
                     'copyto', '--target-directory', dest_dir, 
                     source_file])

    def install(self, image_type,
                system='ubuntu-18.04', 
                verbose=None, 
                gui=False):
        """
        Install dependencies of casa-{image_type} image
        This method look for a share/docker/casa-{image_type}/{system}/vbox.py file
        and execute the install(base_dir, vbox, verbose) command that must
        be defined in this file.
        
        base_dir is the directory containing the vbox.py file
        vbox is the instance of VBoxMachine (i.e. self)
        verbose is either None or a file where to write information about the
            installation process.
        """
        
        share_dir = osp.join(osp.dirname(osp.dirname(osp.dirname(__file__))), 
                             'share')
        casa_docker = osp.join(share_dir, 'docker', 'casa-%s' % image_type, system)

        install_file = osp.join(casa_docker, 'vbox.py')
        if not osp.exists(install_file):
            raise RuntimeError('VirtualBox install file missing: %s' % install_file)
        
        v = {}       
        exec(compile(open(install_file, "rb").read(), install_file, 'exec'), v, v)
        if 'install' not in v:
            raise RuntimeError('No install function defined in %s' % install_file)
        install_function = v['install']
        
        self.start_and_wait(verbose=verbose, gui=gui)
        install_function(base_dir=casa_docker,
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


def setup(type, distro, branch, system, name, base_directory, image,
          output, vm_memory, vm_disk_size, verbose, force):
    """
    VirtualBox specific part of setup command
    """
    raise NotImplementedError('setup is not implemented for VirtualBox')
    #if output:
        #vm_name = vm_name.format(image_name=image_name)
        #output = osp.expanduser(osp.expandvars(output.format(vm_name=vm_name)))
        #if os.path.exists(output):
            #raise ValueError('File %s already exists, please remove it and retry' % output)
        #vbox_import_image(image=source_image,
                           #vbox_machine=vm_name,
                           #output=output,
                           #memory=vm_memory,
                           #disk_size=vm_disk_size)
        #VBoxManage sharedfolder add test --name casa --hostpath ~/casa_distro/brainvisa/bug_fix_ubuntu-18.04 --automount
