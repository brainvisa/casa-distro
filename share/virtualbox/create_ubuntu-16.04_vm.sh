set -x
IMAGE=ubuntu-16.04-brainvisa
IMAGE_DIR=$PWD/vbox

# Create new virtual machine with the ability to boot on a DVD
VBoxManage createvm --name $IMAGE --ostype Ubuntu_64 --register --basefolder $IMAGE_DIR
VBoxManage modifyvm $IMAGE --memory 1024 --boot1 dvd
VBoxManage modifyvm $IMAGE --nic1 nat
# Create 10Gb system disk
VBoxManage createhd --filename $IMAGE_DIR/$IMAGE.vdi --size 16384 --format VDI --variant Standard
# Create a SATA controller in the VM
VBoxManage storagectl $IMAGE --name "${IMAGE}_SATA" --add sata
# Attach the system disk to the machine
VBoxManage storageattach $IMAGE --storagectl ${IMAGE}_SATA --port 1 --type hdd --medium $IMAGE_DIR/$IMAGE.vdi
# Attach the Ubuntu image to the DVD
VBoxManage storageattach $IMAGE --storagectl ${IMAGE}_SATA --port 0 --type dvddrive --medium ubuntu-16.04.5-desktop-amd64.iso
# Forward VM port 22 (ssh) to host port 3022
# VBoxManage modifyvm $IMAGE --natpf1 "ssh,tcp,,3022,,22"
# Start VM
VBoxManage startvm $IMAGE
