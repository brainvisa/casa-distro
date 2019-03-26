#!/bin/bash

SIP_VERSION=4.19.15
PYQT_VERSION=5.12.1
PRE_4_19=
PRE_4_18=
PREFIX=/usr/local/sip-$SIP_VERSION
BUILD=/tmp/sipbuild
PATCH_FILE=ftp://ftp.cea.fr/pub/dsv/anatomist/3rdparty/1.0.0/sources/pyqt_patch
if [ -f /proc/cpuinfo ]; then
    NCPU=$(cat /proc/cpuinfo | fgrep processor| wc)
    for c in $NCPU; do NCPU=$c; break; done
else
    NCPU=4
fi
SUDO=

if [ ! -d "$BUILD" ]; then mkdir -p "$BUILD"; fi
cd "$BUILD"
if [ -z "$PRE_4_19" ]; then
    DL_URL_SIP="https://www.riverbankcomputing.com/static/Downloads/sip/${SIP_VERSION}/sip-${SIP_VERSION}.tar.gz"
    PYQT=PyQt5_gpl-${PYQT_VERSION}
    DL_URL_PYQT="https://www.riverbankcomputing.com/static/Downloads/PyQt5/${PYQT_VERSION}/${PYQT}.tar.gz"
else
    DL_URL_SIP="https://sourceforge.net/projects/pyqt/files/sip/${SIP_VERSION}/sip-${SIP_VERSION}.tar.gz"
    PYQT=PyQt-gpl-${PYQT_VERSION}
    DL_URL_PYQT="https://sourceforge.net/projects/pyqt/files/PyQt5/PyQt-${PYQT_VERSION}/${PYQT}.tar.gz"
    if [ -n "$PRE_4_18" ]; then
        wget $PATCH_FILE
    fi
fi
wget "$DL_URL_SIP"
wget "$DL_URL_PYQT"

tar xf sip-${SIP_VERSION}.tar.gz
cd sip-${SIP_VERSION}
SIP_OPTS=
PYQT_OPTS=
if [ -z "$PRE_4_19" ]; then
    SIP_OPTS="--sip-module PyQt5.sip"
#     PYQT_OPTS="--sip-module PyQt5.sip"
fi
python configure.py -b "$PREFIX/bin" -d "$PREFIX/lib/python2.7/dist-packages" -e "$PREFIX/include/python2.7" -v "$PREFIX/share/sip" ${SIP_OPTS}
make -j$NCPU
${SUDO} make install

make clean
python3 configure.py -b "$PREFIX/bin" -d "$PREFIX/lib/python3.6/dist-packages" -e "$PREFIX/include/python3.6m" -v "$PREFIX/share/sip" ${SIP_OPTS}
make -j$NCPU
${SUDO} make install
cd ..

export PATH="$PREFIX/bin:$PATH"
OLD_PPATH="$PYTHONPATH"
export PYTHONPATH="$PREFIX/lib/python2.7/dist-packages:$PYTHONPATH"
hash sip

tar xf "${PYQT}.tar.gz"
cd "$PYQT"
if [ -n "$PRE_4_18" ]; then
    patch -p1 < ../pyqt_patch
fi
python configure.py --confirm-license --sip-incdir="$PREFIX/include/python2.7" -b "$PREFIX/bin" -d "$PREFIX/lib/python2.7/dist-packages" --designer-plugindir="$PREFIX/lib/qt5/plugins/designer" --qml-plugindir="$PREFIX/lib/qt5/plugins/PyQt5" -v "$PREFIX/share/sip/PyQt5" --qmake="/usr/lib/qt5/bin/qmake" ${PYQT_OPTS}
make -j$NCPU
${SUDO} make install

make clean
python3 configure.py --confirm-license --sip-incdir="$PREFIX/include/python3.6m" -b "$PREFIX/bin" -d "$PREFIX/lib/python3.6/dist-packages" --designer-plugindir="$PREFIX/lib/qt5/plugins/designer" --qml-plugindir="$PREFIX/lib/qt5/plugins/PyQt5" -v "$PREFIX/share/sip/PyQt5" --qmake="/usr/lib/qt5/bin/qmake" ${PYQT_OPTS}
make -j$NCPU
${SUDO} make install
cd ../..

rm -rf "$BUILD"

${SUDO} ln -s sip-${SIP_VERSION} "$PREFIX/../sip"
cd /usr/local/lib/python2.7/dist-packages
${SUDO} ln -s ../../../sip/lib/python2.7/dist-packages/* .
cd /usr/local/lib/python3.6/dist-packages
${SUDO} ln -s ../../../sip/lib/python3.6/dist-packages/* .
cd "$PREFIX/../bin"
${SUDO} ln -s ../sip/bin/* .

