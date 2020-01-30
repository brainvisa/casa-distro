# Install system dependencies for image cati/casa-dev:ubuntu-16.04

set -e # stop the script on error

set -x # display command before running them
if [ `id -u` -eq 0 ]; then
    SUDO=
else
    SUDO=sudo
fi

. /casa/environment.sh

# install Pycluster
cd /tmp
wget http://bonsai.hgc.jp/~mdehoon/software/cluster/Pycluster-1.52.tar.gz
tar xfz Pycluster-1.52.tar.gz
cd Pycluster-1.52
python setup.py build
$SUDO python setup.py install
# install in python3
python3 setup.py build
$SUDO python3 setup.py install
cd ..
rm -r Pycluster-1.52 Pycluster-1.52.tar.gz

# Install Qt Installer Framework (prebuilt on Mandriva 2008)
cd /tmp
wget http://brainvisa.info/static/qt_installer-1.6.tar.gz
cd /usr/local
$SUDO tar xfz /tmp/qt_installer-1.6.tar.gz
$SUDO ln -s qt_installer-1.6 qt_installer
cd /usr/local/bin
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

# cmake does not work with clang whenever Qt5 is invoked.
# workaround here:
# https://stackoverflow.com/questions/38027292/configure-a-qt5-5-7-application-for-android-with-cmake/40256862#40256862
sed 's/^\(set_property.*INTERFACE_COMPILE_FEATURES.*\)$/#\ \1/' < /usr/lib/x86_64-linux-gnu/cmake/Qt5Core/Qt5CoreConfigExtras.cmake > /tmp/Qt5CoreConfigExtras.cmake
$SUDO cp -f /tmp/Qt5CoreConfigExtras.cmake /usr/lib/x86_64-linux-gnu/cmake/Qt5Core/Qt5CoreConfigExtras.cmake

# reinstall an older sip and PyQt5 from sources because of a bug in sip 4.19
# and virtual C++ inheritance
$SUDO bash /tmp/build_sip_pyqt.sh

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
              
$SUDO chmod +x /usr/local/bin/svn
$SUDO chmod +x /usr/local/bin/svn /usr/local/bin/askpass-bioproj.sh
$SUDO git config --system core.askPass /usr/local/bin/askpass-bioproj.sh

# allow attach gdb to a process
echo "kernel.yama.ptrace_scope = 0" > /etc/sysctl.d/10-ptrace.conf

# Install a version of brainvisa-cmake
/usr/bin/git clone https://github.com/brainvisa/brainvisa-cmake.git $CASA_SRC/development/brainvisa-cmake/master
mkdir /tmp/brainvisa-cmake
cd /tmp/brainvisa-cmake
cmake -DCMAKE_INSTALL_PREFIX=/casa/brainvisa-cmake $CASA_SRC/development/brainvisa-cmake/master
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

$SUDO sed -i 's%"$@"%. /usr/local/bin/init-casa-env\n"$@"%g' /usr/local/bin/entrypoint

ldconfig
