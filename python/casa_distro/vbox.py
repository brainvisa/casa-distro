# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function

from subprocess import check_call

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
        print('Create Linux 64 bits virtual machine',
              file=verbose, flush=True)
    check_call(['VBoxManage', 'createvm', 
                '--name', image_name, 
                '--ostype', 'Ubuntu_64',
                '--register'])
    if verbose:
        print('Set memory to', memory, 'MiB and allow booting on DVD',
              file=verbose, flush=True)
    check_call(['VBoxManage', 'modifyvm', image_name,
                '--memory', memory,
                #'--vram', '64',
                '--boot1', 'dvd',
                '--nic1', 'nat'])
    if verbose:
        print('Create a', disk_size, 'MiB system disk in', output,
              file=verbose, flush=True)
    check_call(['VBoxManage', 'createmedium',
                '--filename', output,
                '--size', disk_size,
                '--format', 'VDI',
                '--variant', 'Standard'])
    if verbose:
        print('Create a SATA controller in the VM',
              file=verbose, flush=True)
    check_call(['VBoxManage', 'storagectl', image_name,
                '--name', '%s_SATA' % image_name,
                '--add', 'sata'])
    if verbose:
        print('Attach the system disk to the machine',
              file=verbose, flush=True)
    check_call(['VBoxManage', 'storageattach', image_name,
                '--storagectl', '%s_SATA' % image_name,
                '--medium', output,
                '--port', '1',
                '--type', 'hdd'])
    if verbose:
        print('Attach', iso, 'to the DVD',
              file=verbose, flush=True)
    check_call(['VBoxManage', 'storageattach', image_name,
                '--storagectl', '%s_SATA' % image_name,
                '--port', '0',
                '--type', 'dvddrive',
                '--medium', iso])
    if verbose:
        print('Start the new virtual machine',
              file=verbose, flush=True)
    check_call(['VBoxManage', 'startvm', image_name])
