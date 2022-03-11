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

# Prevent Git from guessing user name and "email" (user@hostname) because that
# makes ugly commits that cannot always be traced back to the author/committer.
git config --system user.useConfigOnly true


# allow attach gdb to a process
echo "kernel.yama.ptrace_scope = 0" > /etc/sysctl.d/10-ptrace.conf

mkdir /casa/bootstrap
cat <<EOF > /casa/bootstrap/README.txt
This directory contains a version of brainvisa-cmake that can be used
for doing the first compilation in an empty dev environment. It is
placed last on the PATH in the image, so the version that is compiled as
part of a BrainVISA build tree will take precedence after the first
successful build.
EOF

# Install a version of brainvisa-cmake
git clone --depth=1 https://github.com/brainvisa/brainvisa-cmake.git \
    /tmp/brainvisa-cmake
cd /tmp/brainvisa-cmake
cmake -DCMAKE_INSTALL_PREFIX=/casa/bootstrap/brainvisa-cmake .
make -j$(nproc)
make install
cd /tmp
rm -rf /tmp/brainvisa-cmake
