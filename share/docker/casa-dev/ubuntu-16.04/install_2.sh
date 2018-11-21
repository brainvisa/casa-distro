# Install system dependencies for image cati/casa-dev:ubuntu-16.04

set -e # stop the script on error

set -x # display command before running them
if [ `id -u` -eq 0 ]; then
    SUDO=
else
    SUDO=sudo
fi

. /casa/environment.sh

# fix python command used in jupyter kernel
# note: the "official" way is to run: ipython3 kernel install, but here
# in docker it runs an interactive shell for an unknown reason.
# So we go back to manual patching
sed -e 's/  "python",/  "python3",/' < /usr/local/share/jupyter/kernels/python3/kernel.json > /tmp/kernel3.json
$SUDO cp /tmp/kernel3.json /usr/local/share/jupyter/kernels/python3/kernel.json


# install Pycluster
cd /tmp
wget http://bonsai.hgc.jp/~mdehoon/software/cluster/Pycluster-1.52.tar.gz
tar xfz Pycluster-1.52.tar.gz
cd Pycluster-1.52
python setup.py build
$SUDO python setup.py install
cd ..
rm -r Pycluster-1.52 Pycluster-1.52.tar.gz

# Install Qt Installer Framework (prebuilt on Mandriva 2008)
cd /tmp
wget http://brainvisa.info/static/qt_installer-1.6.tar.gz
cd /usr/local
$SUDO tar xfz /tmp/qt_installer-1.6.tar.gz
$SUDO ln -s qt_installer-1.6 qt_installer
cd /usr/local/bin \
$SUDO ln -s ../qt_installer/bin/* .
rm /tmp/qt_installer-1.6.tar.gz

cd /tmp
wget https://codeplexarchive.blob.core.windows.net/archive/projects/jxrlib/jxrlib.zip
mkdir jxrlib
cd jxrlib
# Unzip returns 1 in case of warning : temporarily disable stop on error
set +e
unzip ../jxrlib.zip
set -e
cd sourceCode/jxrlib
DIR_INSTALL=/usr/local SHARED=1 $SUDO make -j4 install
cd /tmp
rm -R jxrlib jxrlib.zip

cd /tmp
git clone https://github.com/MIRCen/openslide.git
cd openslide
$SUDO libtoolize --force
$SUDO aclocal 
$SUDO autoheader
$SUDO automake --force-missing --add-missing
$SUDO autoconf
$SUDO ./configure
$SUDO make -j4 install
cd /tmp
$SUDO rm -R openslide

# install a version of netcdf with fewer dependencies
$SUDO bash /tmp/build_netcdf.sh
rm /tmp/build_netcdf.sh

# install libXp, used by some external software (SPM...)
cd /tmp
wget https://mirror.umd.edu/ubuntu/pool/main/libx/libxp/libxp_1.0.2.orig.tar.gz
tar xf libxp_1.0.2.orig.tar.gz
cd libXp-1.0.2
./configure
make -j4
$SUDO make -j4 install
cd /tmp
rm -R libxp_1.0.2.orig.tar.gz libXp-1.0.2

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
              
chmod +x /usr/local/bin/svn

# allow attach gdb to a process
echo "kernel.yama.ptrace_scope = 0" > /etc/sysctl.d/10-ptrace.conf

# Install a version of brainvisa-cmake
svn export https://bioproj.extra.cea.fr/neurosvn/brainvisa/development/brainvisa-cmake/branches/bug_fix $CASA_SRC/development/brainvisa-cmake/bug_fix
mkdir /tmp/brainvisa-cmake
cd /tmp/brainvisa-cmake
cmake -DCMAKE_INSTALL_PREFIX=/casa/brainvisa-cmake $CASA_SRC/development/brainvisa-cmake/bug_fix
make install
cd ..
rm -r /tmp/brainvisa-cmake

# Set casa environement variables initialization
$SUDO echo \
'export PATH=${PATH}:/casa/brainvisa-cmake/bin\n'\
'if [ -f "${CASA_BUILD}/bin/bv_env.sh" ]; then\n'\
'    OLD_CWD=$(pwd)\n'\
'    cd ${CASA_BUILD}/bin\n'\
'    PATH=.:"$PATH"\n'\
'    . ./bv_env.sh\n'\
'    cd ${OLD_CWD}\n'\
'    unset OLD_CWD\n'\
'fi' > /usr/local/bin/init-casa-env

$SUDO chmod +x /usr/local/bin/svn /usr/local/bin/askpass-bioproj.sh
$SUDO git config --system core.askPass /usr/local/bin/askpass-bioproj.sh

ldconfig
