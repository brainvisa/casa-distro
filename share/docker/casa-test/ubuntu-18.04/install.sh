# Install system dependencies for image cati/casa-test:ubuntu-18.04
set -e
set -x

if [ `id -u` -eq 0 ]; then
    SUDO=
else
    SUDO=sudo
fi


# WARNING: it is necessary to call apt-get install for each packages to 
# avoid the 101th package issue
$SUDO apt-get update
DEBIAN_FRONTEND=noninteractive $SUDO apt-get upgrade -y
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install --no-install-recommends -y xvfb
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install --no-install-recommends -y libx11-xcb1
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install --no-install-recommends -y libfontconfig1
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install --no-install-recommends -y libdbus-1-3
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install --no-install-recommends -y sudo
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install --no-install-recommends -y libxrender1
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install --no-install-recommends -y libglib2.0-0
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install --no-install-recommends -y libxi6
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install --no-install-recommends -y wget
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install --no-install-recommends -y x11-utils
DEBIAN_FRONTEND=noninteractive $SUDO apt-get install --no-install-recommends -y mesa-utils
$SUDO apt-get clean
$SUDO rm -rf /var/lib/apt/lists/*
# delete all the apt list files since they're big and get stale quickly

cd /tmp
wget --no-check-certificate https://sourceforge.net/projects/virtualgl/files/2.6.1/virtualgl_2.6.1_amd64.deb
$SUDO dpkg -i virtualgl_2.6.1_amd64.deb
rm -f /tmp/virtualgl_2.6.1_amd64.deb

$SUDO ldconfig

# create casa directories for singularity compatibility            
$SUDO mkdir -p /casa/home \
               /casa/pack \
               /casa/install \
               /casa/tests

chmod 777 /casa \
          /casa/home \
          /casa/pack \
          /casa/install \
          /casa/tests
              
chmod +x /usr/local/bin/entrypoint
