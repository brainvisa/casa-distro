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

    def start_and_wait(self, wait=5, attempts=20, verbose=None, gui=False):
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

        self.start_and_wait(verbose=verbose, gui=gui)

        if verbose:
            six.print_('Creating /casa and', self.tmp_dir, 'in', self.vm,
                    file=verbose, flush=True)
        self.run_root('if [ ! -e "{0}" ]; then mkdir "{0}"; fi'.format(self.tmp_dir))
        self.run_root('if [ ! -e /casa ]; then mkdir /casa && /bin/chown {0}:{0} /casa; fi'.format(self.user))

        if verbose:
            six.print_('Copying files in', self.vm,
                       file=verbose, flush=True)
        for f in ('install_apt_dependencies.sh',
                  'neurodebian.sources.list',
                  'neurodebian-key.gpg',
                  'install_pip_dependencies.sh',
                  'install_compiled_dependencies.sh',
                  'build_netcdf.sh',
                  'build_sip_pyqt.sh',
                  'cleanup_build_dependencies.sh'):
            self.copy_root(osp.join(casa_run_docker, f), '/tmp')

        if verbose:
            six.print_('Copying entrypoint in', self.vm,
                    file=verbose, flush=True)
        self.copy_root(osp.join(casa_run_docker, 'entrypoint'),
                                '/usr/local/bin/')
        self.run_root('chmod a+rx /usr/local/bin/entrypoint')
        self.run_root('chmod +x /tmp/*.sh')

        if verbose:
            six.print_('Running install_apt_dependencies.sh',
                    file=verbose, flush=True)
        self.run_root('/tmp/install_apt_dependencies.sh')
        if verbose:
            six.print_('Running install_pip_dependencies.sh',
                    file=verbose, flush=True)
        self.run_root('/tmp/install_pip_dependencies.sh')
        if verbose:
            six.print_('Running install_compiled_dependencies.sh',
                    file=verbose, flush=True)
        self.run_root('/tmp/install_compiled_dependencies.sh')

        if verbose:
            six.print_('Running cleanup_build_dependencies.sh',
                    file=verbose, flush=True)
        self.run_root('/tmp/cleanup_build_dependencies.sh')


        if verbose:
            six.print_('Cleanup files in', self.vm,
                    file=verbose, flush=True)
        self.run_root('rm -f /tmp/neurodebian-key.gpg '
                    '/tmp/neurodebian.sources.list '
                    '/tmp/install_apt_dependencies.sh '
                    '/tmp/install_pip_dependencies.sh '
                    '/tmp/install_compiled_dependencies.sh '
                    '/tmp/build_netcdf.sh '
                    '/tmp/build_sip_pyqt.sh '
                    '/tmp/cleanup_build_dependencies.sh')

    def install_dev(self, system='ubuntu-18.04', verbose=None, gui=False):
        """
        Install dependencies of casa-dev image
        See file share/docker/casa-dev/{system}/Dockerfile
        """
        
        share_dir = osp.join(osp.dirname(osp.dirname(osp.dirname(__file__))), 'share')
        casa_dev_docker = osp.join(share_dir, 'docker', 'casa-dev', system)
        
        self.start_and_wait(verbose=verbose, gui=gui)
        self.run_root('if [ ! -e "{0}" ]; then mkdir "{0}"; fi'.format(self.tmp_dir))

        if verbose:
            six.print_('Copying files in', self.vm,
                       file=verbose, flush=True)
        for f in ('install_apt_dev_dependencies.sh',
                  'install_pip_dev_dependencies.sh',
                  'install_compiled_dev_dependencies.sh',
                  'build_sip_pyqt.sh',
                  'install_casa_dev_components.sh'):
            self.copy_root(osp.realpath(osp.join(casa_dev_docker, f)), '/tmp')
        self.run_root('chmod +x /tmp/*.sh')

        self.copy_user(osp.join(casa_dev_docker, 'environment.sh'),
                       '/casa')
        self.run_user('chmod a+rx /casa/environment.sh')

        self.copy_user(osp.realpath(osp.join(casa_dev_docker, 'svn.secret')),
                       '/casa/conf')
        self.copy_root(osp.realpath(osp.join(casa_dev_docker, 'svn')),
                       '/usr/local/bin')
        self.run_root('chmod a+rx /usr/local/bin/svn')
        self.copy_root(osp.realpath(osp.join(casa_dev_docker, 'askpass-bioproj.sh')),
                       '/usr/local/bin')
        self.run_root('chmod a+rx /usr/local/bin/askpass-bioproj.sh')

        self.copy_user(osp.realpath(osp.join(casa_dev_docker, 'list-shared-libs-paths.sh')),
                       '/casa/')
        self.run_user('chmod a+rx /casa/list-shared-libs-paths.sh')

        if verbose:
            six.print_('Running install_apt_dev_dependencies.sh',
                    file=verbose, flush=True)
        self.run_root('/tmp/install_apt_dev_dependencies.sh')
        if verbose:
            six.print_('Running install_pip_dev_dependencies.sh',
                    file=verbose, flush=True)
        self.run_root('/tmp/install_pip_dev_dependencies.sh')
        if verbose:
            six.print_('Running install_compiled_dev_dependencies.sh',
                    file=verbose, flush=True)
        self.run_root('/tmp/install_compiled_dev_dependencies.sh')

        if verbose:
            six.print_('Running install_casa_dev_components.sh',
                    file=verbose, flush=True)
        self.run_root('/tmp/install_casa_dev_components.sh')


        if verbose:
            six.print_('Cleanup files in', self.vm,
                    file=verbose, flush=True)
        self.run_root('rm -f /casa/install_apt_dev_dependencies.sh '
                      '/casa/build_sip_pyqt.sh '
                      '/casa/install_pip_dev_dependencies.sh '
                      '/casa/install_compiled_dev_dependencies.sh '
                      '/casa/install_casa_dev_components.sh')

def vbox_import_image(system_image, vbox_machine, output,
                      verbose=None,
                      memory='8192',
                      disk_size='131072'):
    if verbose:
        six.print_('Copying', system_image, 'to', output,
              file=verbose, flush=True)
    parent = osp.dirname(output)
    if not osp.exists(parent):
        os.makedirs(parent)
    if osp.exists(output):
        os.remove(output)
    subprocess.check_call(['VBoxManage', 'clonemedium',
                           system_image, output,
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
