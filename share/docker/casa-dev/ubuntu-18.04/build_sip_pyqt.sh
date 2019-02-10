#!/bin/bash

SIP_VERSION=4.17
PYQT_VERSION=5.5.1
PREFIX=/usr/local/sip-4.17
BUILD=/tmp/sipbuild
PATCH_FILE=ftp://ftp.cea.fr/pub/dsv/anatomist/3rdparty/1.0.0/sources/pyqt_patch
NCPU=4
SUDO=

if [ ! -d "$BUILD" ]; then mkdir -p "$BUILD"; fi
cd "$BUILD"
wget https://sourceforge.net/projects/pyqt/files/sip/sip-${SIP_VERSION}/sip-${SIP_VERSION}.tar.gz
wget https://sourceforge.net/projects/pyqt/files/PyQt5/PyQt-${PYQT_VERSION}/PyQt-gpl-${PYQT_VERSION}.tar.gz
wget $PATCH_FILE

tar xf sip-${SIP_VERSION}.tar.gz
cd sip-${SIP_VERSION}
python configure.py -b "$PREFIX/bin" -d "$PREFIX/lib/python2.7/dist-packages" -e "$PREFIX/include/python2.7" -v "$PREFIX/share/sip"
make -j$NCPU
${SUDO} make install

make clean
python3 configure.py -b "$PREFIX/bin" -d "$PREFIX/lib/python3.6/dist-packages" -e "$PREFIX/include/python3.6m" -v "$PREFIX/share/sip"
make -j$NCPU
${SUDO} make install
cd ..

export PATH="$PREFIX/bin:$PATH"
OLD_PPATH="$PYTHONPATH"
export PYTHONPATH="$PREFIX/lib/python2.7/dist-packages:$PYTHONPATH"
hash sip

tar xf PyQt-gpl-${PYQT_VERSION}.tar.gz
cd PyQt-gpl-${PYQT_VERSION}
patch -p1 < ../pyqt_patch
python configure.py --confirm-license --sip-incdir="$PREFIX/include/python2.7" -b "$PREFIX/bin" -d "$PREFIX/lib/python2.7/dist-packages" --designer-plugindir="$PREFIX/lib/qt5/plugins/designer" --qml-plugindir="$PREFIX/lib/qt5/plugins/PyQt5" -v "$PREFIX/share/sip/PyQt5" --qmake="/usr/lib/qt5/bin/qmake"
make -j$NCPU
${SUDO} make install

make clean
python3 configure.py --confirm-license --sip-incdir="$PREFIX/include/python3.6m" -b "$PREFIX/bin" -d "$PREFIX/lib/python3.6/dist-packages" --designer-plugindir="$PREFIX/lib/qt5/plugins/designer" --qml-plugindir="$PREFIX/lib/qt5/plugins/PyQt5" -v "$PREFIX/share/sip/PyQt5" --qmake="/usr/lib/qt5/bin/qmake"
make -j$NCPU
${SUDO} make install
cd ../..

rm -rf "$BUILD"

${SUDO} ln -s sip-${SIP_VERSION} "$PREFIX/sip"
cd /usr/local/lib/python2.7/dist-packages
${SUDO} ln -s ../../../sip/lib/python2.7/dist-packages/* .
cd /usr/local/lib/python3.6/dist-packages
${SUDO} ln -s ../../../sip/lib/python3.6/dist-packages/* .

