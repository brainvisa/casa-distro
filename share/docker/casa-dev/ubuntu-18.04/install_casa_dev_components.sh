#! /bin/sh
#
# NOTE: This script is used to create the casa-dev Docker/Singularity image,
# and also during the creation of the VirtualBox casa-dev image. Make sure not
# to include anything Docker-specific in this file.

set -e  # stop the script on error
set -x  # display commands before running them

. /casa/environment.sh

###############################################################################
# Install configuration elements that are specific to casa-dev
###############################################################################

# create casa directories for singularity compatibility
mkdir -p $CASA_CONF \
         $CASA_SRC \
         $CASA_CUSTOM_SRC \
         $CASA_BUILD \
         $CASA_CUSTOM_BUILD

chmod 777 $CASA_CONF \
          $CASA_SRC \
          $CASA_CUSTOM_SRC \
          $CASA_BUILD \
          $CASA_CUSTOM_BUILD

sudo chmod +x /usr/local/bin/svn /usr/local/bin/askpass-bioproj.sh
sudo git config --system core.askPass /usr/local/bin/askpass-bioproj.sh

# allow attach gdb to a process
echo "kernel.yama.ptrace_scope = 0" > /etc/sysctl.d/10-ptrace.conf

# Install a version of brainvisa-cmake
git clone https://github.com/brainvisa/brainvisa-cmake.git \
          "$CASA_SRC"/development/brainvisa-cmake/master
mkdir /tmp/brainvisa-cmake
cd /tmp/brainvisa-cmake
cmake -DCMAKE_INSTALL_PREFIX=/casa/brainvisa-cmake $CASA_SRC/development/brainvisa-cmake/master
make install
cd ..
rm -rf /tmp/brainvisa-cmake