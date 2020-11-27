#! /bin/sh
#
# NOTE: This script is used to create the casa-dev Docker/Singularity image,
# and also during the creation of the VirtualBox casa-dev image. Make sure not
# to include anything Docker-specific in this file.

set -e  # stop the script on error
set -x  # display commands before running them

if [ -e /casa/dev-environment.sh ]; then
    . /casa/dev-environment.sh
fi

###############################################################################
# Install configuration elements that are specific to casa-dev
###############################################################################

sudo chmod +x /usr/local/bin/svn /usr/local/bin/askpass-bioproj.sh
sudo git config --system core.askPass /usr/local/bin/askpass-bioproj.sh
sudo git lfs install --system --skip-repo

# allow attach gdb to a process
echo "kernel.yama.ptrace_scope = 0" > /etc/sysctl.d/10-ptrace.conf

# Install a version of brainvisa-cmake
echo '!!!' $CASA_SRC
git clone https://github.com/brainvisa/brainvisa-cmake.git \
          "$CASA_SRC"/development/brainvisa-cmake/master
mkdir /tmp/brainvisa-cmake
cd /tmp/brainvisa-cmake
cmake -DCMAKE_INSTALL_PREFIX=/casa/brainvisa-cmake $CASA_SRC/development/brainvisa-cmake/master
make install
cd ..
rm -rf /tmp/brainvisa-cmake
