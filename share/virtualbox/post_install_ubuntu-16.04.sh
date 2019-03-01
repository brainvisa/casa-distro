set -x
SRC_IMAGE=ubuntu-16.04-brainvisa
DST_IMAGE=brainvisa-dev
ROOT_PASSWORD=brainvisa
USER=brainvisa
USER_PASSWORD=brainvisa

VBoxManage clonevm $SRC_IMAGE --name $DST_IMAGE --register
VBoxManage startvm $DST_IMAGE

# TODO Wait for the VM to be started

VBoxManage guestcontrol --username root --password "$ROOT_PASSWORD" $DST_IMAGE mkdir /casa
VBoxManage guestcontrol --username root --password "$ROOT_PASSWORD" $DST_IMAGE run -- /bin/chown $USER:$USER /casa

VBoxManage guestcontrol --username root --password "$ROOT_PASSWORD" $DST_IMAGE copyto --target-directory /usr/local/lib ../docker/casa-test/ubuntu-16.04/libGL.so.1
VBoxManage guestcontrol --username root --password "$ROOT_PASSWORD" $DST_IMAGE copyto --target-directory /usr/local/lib ../docker/casa-test/ubuntu-16.04/libglapi.so.0
VBoxManage guestcontrol --username root --password "$ROOT_PASSWORD" $DST_IMAGE copyto --target-directory /usr/local/bin ../docker/casa-test/ubuntu-16.04/entrypoint
VBoxManage guestcontrol --username root --password "$ROOT_PASSWORD" $DST_IMAGE copyto --target-directory /usr/local/bin ../scripts/askpass-bioproj.sh
VBoxManage guestcontrol --username root --password "$ROOT_PASSWORD" $DST_IMAGE copyto --target-directory /usr/local/bin ../scripts/svn

VBoxManage guestcontrol --username "$USER" --password "$USER_PASSWORD" $DST_IMAGE copyto --target-directory /casa ../docker/casa-dev/ubuntu-16.04/environment.sh

VBoxManage guestcontrol --username root --password "$ROOT_PASSWORD" $DST_IMAGE copyto --target-directory /tmp ../../share/docker/casa-test/ubuntu-16.04/install.sh 
VBoxManage guestcontrol --username root --password "$ROOT_PASSWORD" $DST_IMAGE run -- /bin/sh /tmp/install.sh
VBoxManage guestcontrol --username root --password "$ROOT_PASSWORD" $DST_IMAGE rm /tmp/install.sh 

VBoxManage guestcontrol --username root --password "$ROOT_PASSWORD" $DST_IMAGE copyto --target-directory /tmp ../docker/casa-dev/ubuntu-16.04/install_1.sh 
VBoxManage guestcontrol --username root --password "$ROOT_PASSWORD" $DST_IMAGE run -- /bin/sh /tmp/install_1.sh
VBoxManage guestcontrol --username root --password "$ROOT_PASSWORD" $DST_IMAGE rm /tmp/install_1.sh 

VBoxManage guestcontrol --username root --password "$ROOT_PASSWORD" $DST_IMAGE copyto --target-directory /tmp ../docker/casa-dev/ubuntu-16.04/build_netcdf.sh
VBoxManage guestcontrol --username root --password "$ROOT_PASSWORD" $DST_IMAGE copyto --target-directory /tmp ../docker/casa-dev/ubuntu-16.04/install_2.sh 
VBoxManage guestcontrol --username root --password "$ROOT_PASSWORD" $DST_IMAGE run -- /bin/sh /tmp/install_2.sh
VBoxManage guestcontrol --username root --password "$ROOT_PASSWORD" $DST_IMAGE rm /tmp/install_2.sh 
VBoxManage guestcontrol --username root --password "$ROOT_PASSWORD" $DST_IMAGE rm /tmp/build_netcdf.sh

VBoxManage guestcontrol --username $USER --password "$USER_PASSWORD" $DST_IMAGE copyto -R --target-directory /casa /casa/src
VBoxManage guestcontrol --username $USER --password "$USER_PASSWORD" $DST_IMAGE copyto -R --target-directory /casa /casa/build
