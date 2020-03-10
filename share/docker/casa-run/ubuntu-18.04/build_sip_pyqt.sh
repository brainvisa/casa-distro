#! /bin/bash

set -e
set -x

SIP_VERSION=4.19.15
PYQT_VERSION=5.12.1
PRE_4_19=
PRE_4_18=
PREFIX=/usr/local/sip-$SIP_VERSION
BUILD=/tmp/sipbuild
PATCH_FILE=ftp://ftp.cea.fr/pub/dsv/anatomist/3rdparty/1.0.0/sources/pyqt_patch

PY3=3.6m
PY3_S=3.6
QMAKE=/usr/lib/qt5/bin/qmake

mkdir "$BUILD"
cd "$BUILD"
if [ -z "$PRE_4_19" ]; then
    DL_URL_SIP="https://www.riverbankcomputing.com/static/Downloads/sip/${SIP_VERSION}/sip-${SIP_VERSION}.tar.gz"
    PYQT=PyQt5_gpl-${PYQT_VERSION}
    DL_URL_PYQT="https://www.riverbankcomputing.com/static/Downloads/PyQt5/${PYQT_VERSION}/${PYQT}.tar.gz"
    PYQT_WEBENGINE=PyQtWebEngine_gpl-${PYQT_VERSION}
    DL_URL_PYQT_WEBENGINE="https://www.riverbankcomputing.com/static/Downloads/PyQtWebEngine/${PYQT_VERSION}/PyQtWebEngine_gpl-${PYQT_VERSION}.tar.gz"
else
    DL_URL_SIP="https://sourceforge.net/projects/pyqt/files/sip/${SIP_VERSION}/sip-${SIP_VERSION}.tar.gz"
    PYQT=PyQt-gpl-${PYQT_VERSION}
    DL_URL_PYQT="https://sourceforge.net/projects/pyqt/files/PyQt5/PyQt-${PYQT_VERSION}/${PYQT}.tar.gz"
    if [ -n "$PRE_4_18" ]; then
        wget $PATCH_FILE
    fi
fi

# download sources

wget "$DL_URL_SIP"
wget "$DL_URL_PYQT"
if [ -n "$DL_URL_PYQT_WEBENGINE" ]; then
    wget "$DL_URL_PYQT_WEBENGINE"
fi

# build / install sip

tar xf sip-${SIP_VERSION}.tar.gz
cd sip-${SIP_VERSION}
SIP_OPTS=
PYQT_OPTS=
if [ -z "$PRE_4_19" ]; then
    SIP_OPTS="--sip-module PyQt5.sip"
#     PYQT_OPTS="--sip-module PyQt5.sip"
fi

if [ -n "$DO_PYTHON2" ]; then
    python configure.py -b "$PREFIX/bin" -d "$PREFIX/lib/python2.7/dist-packages" -e "$PREFIX/include/python2.7" -v "$PREFIX/share/sip" ${SIP_OPTS}
    make -j$(nproc)
    sudo make install
fi

if [ -n "$DO_PYTHON3" ]; then
    [ -n "$DO_PYTHON2" ] && make clean
    python3 configure.py -b "$PREFIX/bin" -d "$PREFIX/lib/python${PY3_S}/dist-packages" -e "$PREFIX/include/python${PY3}" -v "$PREFIX/share/sip" ${SIP_OPTS}
    make -j$(nproc)
    sudo make install
fi
cd ..

export PATH="$PREFIX/bin:$PATH"
OLD_PPATH="$PYTHONPATH"
export PYTHONPATH="$PREFIX/lib/python2.7/dist-packages:$PYTHONPATH"
hash sip

# build / install PyQt5

tar xf "${PYQT}.tar.gz"
cd "$PYQT"
if [ -n "$PRE_4_18" ]; then
    patch -p1 < ../pyqt_patch
fi

if [ -n "$DO_PYTHON2" ]; then
    python configure.py --confirm-license --sip-incdir="$PREFIX/include/python2.7" -b "$PREFIX/bin" -d "$PREFIX/lib/python2.7/dist-packages" --designer-plugindir="$PREFIX/lib/qt5/plugins/designer" --qml-plugindir="$PREFIX/lib/qt5/plugins/PyQt5" -v "$PREFIX/share/sip/PyQt5" --qmake="${QMAKE}" ${PYQT_OPTS}
    make -j$(nproc)
    sudo make install
fi

if [ -n "$DO_PYTHON3" ]; then
    [ -n "$DO_PYTHON2" ] && make clean
    python3 configure.py --confirm-license --sip-incdir="$PREFIX/include/python${PY3}" -b "$PREFIX/bin" -d "$PREFIX/lib/python${PY3_S}/dist-packages" --designer-plugindir="$PREFIX/lib/qt5/plugins/designer" --qml-plugindir="$PREFIX/lib/qt5/plugins/PyQt5" -v "$PREFIX/share/sip/PyQt5" --qmake="${QMAKE}" ${PYQT_OPTS}
    make -j$(nproc)
    sudo make install
fi
cd ..

# build / install PyQtWebEngine

if [ -n "$PYQT_WEBENGINE" ]; then
    tar xf "$PYQT_WEBENGINE.tar.gz"
    cd "$PYQT_WEBENGINE"

    if [ -n "$DO_PYTHON2" ]; then
        python configure.py --sip-incdir="$PREFIX/include/python2.7" -d "$PREFIX/lib/python2.7/dist-packages/PyQt5" --sip="$PREFIX/bin/sip" -v "$PREFIX/share/sip/PyQt5" --qmake="${QMAKE}" -a "$PREFIX/share/pyqt5/data/qsci" --pyqt-sipdir="$PREFIX/share/sip/PyQt5"
        make -j$(nproc)
        sudo make install
    fi

    if [ -n "$DO_PYTHON3" ]; then
        [ -n "$DO_PYTHON2" ] && make clean
        python3 configure.py --sip-incdir="$PREFIX/include/python$PY3" -d "$PREFIX/lib/python${PY3_S}/dist-packages/PyQt5" --sip="$PREFIX/bin/sip" -v "$PREFIX/share/sip/PyQt5" --qmake="${QMAKE}" -a "$PREFIX/share/pyqt5/data/qsci" --pyqt-sipdir="$PREFIX/share/sip/PyQt5"
        make -j$(nproc)
        sudo make install
    fi
    cd ..
fi

cd ..

rm -rf "$BUILD"

# symlinks

sudo ln -s sip-${SIP_VERSION} "$PREFIX/../sip"
if [ -n "$DO_PYTHON2" ]; then
    cd /usr/local/lib/python2.7/dist-packages
    sudo ln -s ../../../sip/lib/python2.7/dist-packages/* .
    sudo ln -s PyQt5/sip.so .
fi
if [ -n "$DO_PYTHON3" ]; then
    cd /usr/local/lib/python${PY3_S}/dist-packages
    sudo ln -s ../../../sip/lib/python${PY3_S}/dist-packages/* .
    sudo ln -s PyQt5/sip.so .
fi

cd "$PREFIX/../bin"
sudo ln -s ../sip/bin/* .
