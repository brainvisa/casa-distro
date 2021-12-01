#! /bin/bash

set -e
set -x

SIP_VERSION=4.19.25
# changing the version here requires to change the download URLs below for PyQt and PyQtWebEngine since they are different for each release on PyPi
PREFIX=/usr/local/sip-$SIP_VERSION
BUILD=/tmp/sipbuild

# Assign default values
: ${PY:=3.8m} ${PY_S:=3.8}
# : ${PY:=2.7} ${PY_S:=2.7}

QMAKE=/usr/bin/qmake

if [ -e "$BUILD" ]; then
    rm -r "$BUILD"
fi
mkdir "$BUILD"

PYQT=PyQt5-5.15.5
PYQT_WEBENGINE=PyQtWebEngine-5.15.5
DL_URL_SIP="http://brainvisa.info/download/casa-distro/third-parties/sip-${SIP_VERSION}.tar.gz"
DL_URL_PYQT="http://brainvisa.info/download/casa-distro/third-parties/${PYQT}.tar.gz"
DL_URL_PYQT_WEBENGINE="http://brainvisa.info/download/casa-distro/third-parties/${PYQT_WEBENGINE}.tar.gz"

# download sources

cd "$BUILD"
wget "$DL_URL_SIP"
wget "$DL_URL_PYQT"
wget "$DL_URL_PYQT_WEBENGINE"


# build / install sip

cd "$BUILD"
tar -zxf sip-${SIP_VERSION}.tar.gz
cd sip-${SIP_VERSION}
PYQT_OPTS=
SIP_OPTS="--sip-module PyQt5.sip"
"python${PY_S}" configure.py -b "$PREFIX/bin" -d "$PREFIX/lib/python${PY_S}/dist-packages" -e "$PREFIX/include/python${PY}" -v "$PREFIX/share/sip" --stubsdir="$PREFIX/lib/python${PY_S}/dist-packages" ${SIP_OPTS}
make -j$(nproc)
sudo make install


PATH=$PREFIX/bin:$PATH
PYTHONPATH=$PREFIX/lib/python${PY_S}/dist-packages${PYTHONPATH+:}${PYTHONPATH}
export PATH PYTHONPATH
hash sip

# build / install PyQt5

cd "$BUILD"
tar -zxf "${PYQT}.tar.gz"
cd "$PYQT"
"python${PY_S}" configure.py --confirm-license --sip-incdir="$PREFIX/include/python${PY}" -b "$PREFIX/bin" -d "$PREFIX/lib/python${PY_S}/dist-packages" --designer-plugindir="$PREFIX/lib/qt5/plugins/designer" --qml-plugindir="$PREFIX/lib/qt5/plugins/PyQt5" -v "$PREFIX/share/sip/PyQt5" --qmake="${QMAKE}" --stubsdir="$PREFIX/lib/python${PY_S}/dist-packages/PyQt5" ${PYQT_OPTS}
make -j$(nproc)
sudo make install


# build / install PyQtWebEngine

cd "$BUILD"
tar -zxf "$PYQT_WEBENGINE.tar.gz"
cd "$PYQT_WEBENGINE"
"python${PY_S}" configure.py --sip-incdir="$PREFIX/include/python$PY" -d "$PREFIX/lib/python${PY_S}/dist-packages/PyQt5" --sip="$PREFIX/bin/sip" -v "$PREFIX/share/sip/PyQt5" --qmake="${QMAKE}" -a "$PREFIX/share/pyqt5/data/qsci" --pyqt-sipdir="$PREFIX/share/sip/PyQt5" --stubsdir="$PREFIX/lib/python${PY_S}/dist-packages/PyQt5"
make -j$(nproc)
sudo make install


# symlinks

cd "$PREFIX/../bin"
sudo ln -sfn sip-${SIP_VERSION} "$PREFIX/../sip"
sudo ln -sf -t . ../sip/bin/*

cd "/usr/local/lib/python${PY_S}/dist-packages"
sudo ln -s "../../../sip/lib/python${PY_S}/dist-packages/"* .
sudo ln -s PyQt5/sip.so .

rm -rf "$BUILD"
