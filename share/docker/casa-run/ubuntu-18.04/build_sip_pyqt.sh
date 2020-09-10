#! /bin/bash

set -e
set -x

SIP_VERSION=4.19.24
PYQT_VERSION=5.15.0
PREFIX=/usr/local/sip-$SIP_VERSION
BUILD=/tmp/sipbuild

# Assign default values
: ${PY:=3.6m} ${PY_S:=3.6}
# : ${PY:=2.7} ${PY_S:=2.7}

QMAKE=/usr/lib/qt5/bin/qmake

mkdir "$BUILD"

PYQT=PyQt5-${PYQT_VERSION}
PYQT_WEBENGINE=PyQtWebEngine-${PYQT_VERSION}
DL_URL_SIP="https://www.riverbankcomputing.com/static/Downloads/sip/${SIP_VERSION}/sip-${SIP_VERSION}.tar.gz"
DL_URL_PYQT="https://files.pythonhosted.org/packages/8c/90/82c62bbbadcca98e8c6fa84f1a638de1ed1c89e85368241e9cc43fcbc320/${PYQT}.tar.gz"
DL_URL_PYQT_WEBENGINE="https://files.pythonhosted.org/packages/0d/8d/aece7598d2959f66f09fcced6487dd7727f44ad867fc09978c5aeeaf1d29/${PYQT_WEBENGINE}.tar.gz"

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
"python${PY_S}" configure.py -b "$PREFIX/bin" -d "$PREFIX/lib/python${PY_S}/dist-packages" -e "$PREFIX/include/python${PY}" -v "$PREFIX/share/sip" ${SIP_OPTS}
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
"python${PY_S}" configure.py --confirm-license --sip-incdir="$PREFIX/include/python${PY}" -b "$PREFIX/bin" -d "$PREFIX/lib/python${PY_S}/dist-packages" --designer-plugindir="$PREFIX/lib/qt5/plugins/designer" --qml-plugindir="$PREFIX/lib/qt5/plugins/PyQt5" -v "$PREFIX/share/sip/PyQt5" --qmake="${QMAKE}" ${PYQT_OPTS}
make -j$(nproc)
sudo make install


# build / install PyQtWebEngine

cd "$BUILD"
tar -zxf "$PYQT_WEBENGINE.tar.gz"
cd "$PYQT_WEBENGINE"
"python${PY_S}" configure.py --sip-incdir="$PREFIX/include/python$PY" -d "$PREFIX/lib/python${PY_S}/dist-packages/PyQt5" --sip="$PREFIX/bin/sip" -v "$PREFIX/share/sip/PyQt5" --qmake="${QMAKE}" -a "$PREFIX/share/pyqt5/data/qsci" --pyqt-sipdir="$PREFIX/share/sip/PyQt5"
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
