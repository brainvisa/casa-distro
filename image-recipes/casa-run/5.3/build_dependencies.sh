# This bash script is sourced by both install_apt_dependencies.sh and
# cleanup_build_dependencies.sh.
#
# Every package that is on this list will be installed by
# install_apt_dependencies.sh, then removed in cleanup_build_dependencies.sh

build_dependencies=(
    # General build dependencies (notably useful for pip-compiled packages)
    g++
    gcc
    git
    libc-dev
    libpython3-dev
    make
    patch
    pkg-config

    # cmake is a build dependency but it should not be removed after
    # compilations,  because it is needed for running ctest tests.
    #
    # cmake

    # Build dependencies of MIRCen's fork of openslide
    autoconf
    automake
    libtool
    pkg-config  # needed for autoreconf
    libopenjp2-7-dev
    libtiff-dev
    libcairo2-dev
    libgdk-pixbuf2.0-dev
    libglib2.0-dev
    libxml2-dev
    libjxr-dev

    # Build dependencies of libXp
    # x11proto-print-dev  # does not exist in ubuntu 22.04
    # xutils-dev # for libXp / printproto

    # Build dependencies of SIP/PyQt
    libqt5svg5-dev  # qtconsole needs PyQt5.QtSvg
    libqt5opengl5-dev
    qttools5-dev
    qtmultimedia5-dev
    libqt5webchannel5-dev
    libqt5webkit5-dev
    libqt5webview5-dev
    libqt5x11extras5-dev
    libqt5xmlpatterns5-dev
    qtwebengine5-dev  # for PyQt
)
