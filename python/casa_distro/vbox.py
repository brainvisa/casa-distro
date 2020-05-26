# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function

import os
import os.path as osp
import shutil
import six
import subprocess
import time

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
    subprocess.check_call(['VBoxManage', 'createvm', 
                '--name', image_name, 
                '--ostype', 'Ubuntu_64',
                '--register'])
    if verbose:
        six.print_('Set memory to', memory, 'MiB and allow booting on DVD',
                   file=verbose, flush=True)
    subprocess.check_call(['VBoxManage', 'modifyvm', image_name,
                '--memory', memory,
                #'--vram', '64',
                '--boot1', 'dvd',
                '--nic1', 'nat'])
    if verbose:
        six.print_('Create a', disk_size, 'MiB system disk in', output,
                   file=verbose, flush=True)
    subprocess.check_call(['VBoxManage', 'createmedium',
                '--filename', output,
                '--size', disk_size,
                '--format', 'VDI',
                '--variant', 'Standard'])
    if verbose:
        six.print_('Create a SATA controller in the VM',
                   file=verbose, flush=True)
    subprocess.check_call(['VBoxManage', 'storagectl', image_name,
                '--name', '%s_SATA' % image_name,
                '--add', 'sata'])
    if verbose:
        six.print_('Attach the system disk to the machine',
                   file=verbose, flush=True)
    subprocess.check_call(['VBoxManage', 'storageattach', image_name,
                '--storagectl', '%s_SATA' % image_name,
                '--medium', output,
                '--port', '1',
                '--type', 'hdd'])
    if verbose:
        six.print_('Attach', iso, 'to the DVD',
                   file=verbose, flush=True)
    subprocess.check_call(['VBoxManage', 'storageattach', image_name,
                '--storagectl', '%s_SATA' % image_name,
                '--port', '0',
                '--type', 'dvddrive',
                '--medium', iso])
    if verbose:
        six.print_('Start the new virtual machine',
                   file=verbose, flush=True)
    subprocess.check_call(['VBoxManage', 'startvm', image_name])


class VBoxMachine:
    def __init__(self, vm):
        self.vm = vm
        self.user = 'brainvisa'
        self.user_password = 'brainvisa'
        self.root_password = 'brainvisa'
        self.tmp_dir = '/tmp/casa_distro'
        
    def vm_info(self):
        output = subprocess.check_output(['VBoxManage', 'showvminfo', '--machinereadable', self.vm]).decode()
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
        if gui:
            type = 'gui'
        else:
            type = 'headless'
        subprocess.check_call(['VBoxManage', 'startvm', self.vm, '--type', type])

    def start_and_wait(self, wait=5, attempts=40, verbose=None, gui=False):
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
        return ['VBoxManage', 'guestcontrol', '--username', self.user, '--password',
                self.user_password, self.vm, 'run', '--', '/bin/sh', '-c', command]
    
    def run_user(self, command):
        subprocess.check_call(self._run_user_command(command))


    def run_root(self, command):
        subprocess.check_call(['VBoxManage', 'guestcontrol', '--username', 'root',
                    '--password', self.root_password, self.vm, 'run', '--', 
                    '/bin/sh', '-c', 'umask 0022 && ' + command])


    def copy_root(self, source_file, dest_dir):
        subprocess.check_call(['VBoxManage', 'guestcontrol', '--username', 'root',
                    '--password', self.root_password, self.vm, 'copyto',
                    '--target-directory', self.tmp_dir, source_file])
        f=os.path.basename(source_file)
        self.run_root('cp --no-preserve=mode "{tmp}/{f}" "{dest}/{f}" && rm "{tmp}/{f}"'.format(
            tmp=self.tmp_dir, 
            f=f,
            dest=dest_dir))

    def copy_user(self, source_file, dest_dir):
        subprocess.check_call(['VBoxManage', 'guestcontrol', '--username', self.user, '--password', self.user_password, self.vm, 'copyto', '--target-directory', dest_dir, source_file])

    def install_run(self, system='ubuntu-18.04', verbose=None, gui=False):
        """
        Install dependencies of casa-run image
        See file share/docker/casa-run/{system}/Dockerfile
        """
        
        share_dir = osp.join(osp.dirname(osp.dirname(osp.dirname(__file__))), 'share')
        casa_run_docker = osp.join(share_dir, 'docker', 'casa-run', system)

        install_file = osp.join(casa_run_docker, 'vbox.py')
        if not osp.exists(install_file):
            raise RuntimeError('VirtualBox install file missing: %s' % install_file)
        
        v = {}       
        exec(compile(open(install_file, "rb").read(), install_file, 'exec'), v, v)
        if 'install' not in v:
            raise RuntimeError('No install function defined in %s' % install_file)
        install_function = v['install']
        
        self.start_and_wait(verbose=verbose, gui=gui)
        install_function(base_dir=casa_run_docker,
                         vbox=self,
                         verbose=verbose)
        

    def install_dev(self, system='ubuntu-18.04', verbose=None, gui=False):
        """
        Install dependencies of casa-dev image
        See file share/docker/casa-dev/{system}/Dockerfile
        """
        
        share_dir = osp.join(osp.dirname(osp.dirname(osp.dirname(__file__))), 'share')
        casa_dev_docker = osp.join(share_dir, 'docker', 'casa-dev', system)
        
        install_file = osp.join(casa_dev_docker, 'vbox.py')
        if not osp.exists(install_file):
            raise RuntimeError('VirtualBox install file missing: %s' % install_file)
        
        v = {}       
        exec(compile(open(install_file, "rb").read(), install_file, 'exec'), v, v)
        if 'install' not in v:
            raise RuntimeError('No install function defined in %s' % install_file)
        install_function = v['install']
        
        self.start_and_wait(verbose=verbose, gui=gui)
        install_function(base_dir=casa_dev_docker,
                         vbox=self,
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
    subprocess.check_call(['VBoxManage', 'clonemedium',
                           image, output,
                           '--format', 'VDI',
                           '--variant', 'Standard'])
    
    if verbose:
        six.print_('Create Linux 64 bits virtual machine',
                   file=verbose, flush=True)
    subprocess.check_call(['VBoxManage', 'createvm', 
                '--name', vbox_machine, 
                '--ostype', 'Ubuntu_64',
                '--register'])
    if verbose:
        six.print_('Set memory to', memory, 'MiB and allow booting on DVD',
                   file=verbose, flush=True)
    subprocess.check_call(['VBoxManage', 'modifyvm', vbox_machine,
                '--memory', memory,
                #'--vram', '64',
                '--boot1', 'dvd',
                '--nic1', 'nat'])
    if verbose:
        six.print_('Create a SATA controller in the VM',
                   file=verbose, flush=True)
    subprocess.check_call(['VBoxManage', 'storagectl', vbox_machine,
                '--name', '%s_SATA' % vbox_machine,
                '--add', 'sata'])
    if verbose:
        six.print_('Attach the system disk to the machine',
                   file=verbose, flush=True)
    subprocess.check_call(['VBoxManage', 'storageattach', vbox_machine,
                '--storagectl', '%s_SATA' % vbox_machine,
                '--medium', output,
                '--port', '1',
                '--type', 'hdd'])


def vbox_create_casa_run(system_image, vbox_machine, output,
        
                         verbose=None,
                         memory='8192',
                         disk_size='131072'):
    #vbox_clone_system(system_image, vbox_machine, output,
                      #verbose=verbose,
                      #memory=memory,
                      #disk_size=disk_size)
    vbox = VBoxMachine(vbox_machine)
    vbox.install_run()


if __name__ == '__main__':
    import sys
    
    
    vbox_create_casa_run(system_image='/home/yc176684/casa_distro/casa-ubuntu-18.04.4-desktop-amd64.vdi',
                         vbox_machine='casa-run',
                         output='/home/yc176684/casa_distro/casa-run.vdi',
                         verbose=sys.stdout)
