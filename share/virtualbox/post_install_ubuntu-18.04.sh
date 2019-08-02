set -x
OS=ubuntu-18.04
SRC_IMAGE=$OS-brainvisa
DST_IMAGE=brainvisa-dev
ROOT_PASSWORD=brainvisa
USER=brainvisa
USER_PASSWORD=brainvisa
tmp=`tempfile`

run_root() 
{
    VBoxManage guestcontrol --username root --password "$ROOT_PASSWORD" $DST_IMAGE run -- /bin/sh -c 'umask 0022 && '"$@"
}

run_user() 
{
    VBoxManage guestcontrol --username "$USER" --password "$USER_PASSWORD" $DST_IMAGE run -- /bin/sh -c "$@"
}

copyto_root()
{
    
    VBoxManage guestcontrol --username root --password "$ROOT_PASSWORD" $DST_IMAGE copyto --target-directory "$tmp" "$1"
    f=`basename $1`
    run_root 'cp --no-preserve=mode '"$tmp/$f"' '"$2/$f"' && rm '"$tmp/$f"
}

copyto_user()
{
    VBoxManage guestcontrol --username "$USER" --password "$USER_PASSWORD" $DST_IMAGE copyto --target-directory "$2" "$1"
}


VBoxManage clonevm $SRC_IMAGE --name $DST_IMAGE --register
VBoxManage startvm $DST_IMAGE

# TODO Wait for the VM to be started

run_root 'mkdir '"$tmp"
run_root 'mkdir /casa && /bin/chown '$USER:$USER' /casa'

copyto_root ../scripts/askpass-bioproj.sh /usr/local/bin
copyto_root ../scripts/svn /usr/local/bin

copyto_user ../docker/casa-dev/$OS/environment.sh /casa

copyto_root ../../share/docker/casa-test/$OS/install.sh /tmp
copyto_root ../../share/docker/casa-test/$OS/entrypoint /usr/local/bin 
run_root '/bin/sh /tmp/install.sh && rm /tmp/install.sh'

copyto_root ../docker/casa-dev/$OS/install_1.sh /tmp
run_root '/bin/sh /tmp/install_1.sh && rm /tmp/install_1.sh'

copyto_root ../docker/casa-dev/$OS/build_netcdf.sh /tmp
copyto_root ../docker/casa-dev/$OS/build_sip_pyqt.sh /tmp
copyto_root ../docker/casa-dev/$OS/install_2.sh  /tmp
run_root '/bin/sh /tmp/install_2.sh && rm /tmp/install_2.sh /tmp/build_netcdf.sh /tmp/build_sip_pyqt.sh'

here=$PWD
cd $HOME/casa_distro/brainvisa/bug_fix_$OS
tar cf /tmp/build.tar build
tar cf /tmp/src.tar src
cd $here
copyto_user /tmp/build.tar /tmp
run_root '/bin/rm -R /casa/build'
run_user 'cd /casa && tar xf /tmp/build.tar && rm /tmp/build.tar'
rm /tmp/build.tar
copyto_user /tmp/src.tar /tmp
run_root '/bin/rm -R /casa/src'
run_user 'cd /casa && tar xf /tmp/src.tar && rm /tmp/src.tar'
rm /tmp/src.tar

# run_root apt update
# run_root apt install ssh-server
