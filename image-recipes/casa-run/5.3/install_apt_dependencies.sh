#! /bin/bash
#
# Install dependencies for image casa-run-5.1. This image must
# contain all run-time dependencies that are needed to run BrainVISA when
# installed using 'make install-runtime' (see the Release images).
#
# This image supports a Python 3 / Qt 5 build of BrainVISA.
#
# NOTE: This script is run during the creation of the Singularity and
# VirtualBox casa-run image. Make sure not to include anything specific to a
# given virtualization/containerization engine  in this file.

set -e  # stop the script on error
set -x  # display commands before running them

if [ $(id -u) -eq 0 ]; then
    SUDO=
else
    SUDO=sudo
fi

# Defines the build_dependencies bash array variable, which is used at the
# bottom of this script (see below). The build_dependencies.sh file is expected
# to be found in the same directory as this script.
. "$(dirname -- "$0")"/build_dependencies.sh


###############################################################################
# Install dependencies of this script and configure repositories
###############################################################################

export DEBIAN_FRONTEND=noninteractive

$SUDO apt-get -o Acquire::Retries=3 update

# The Docker images of ubuntu are "minimized", i.e. files that are meant for
# interactive use (man pages, documentation, and translations) are not
# included. While we may not really need them in the casa-run images, the man
# pages are really useful to have in the casa-dev image, but we cannot really
# defer calling "unminimize" until then, because it runs a full "apt-get
# upgrade", which risks causing discrepancy in package versions between
# casa-run und casa-dev. Therefore, the best place to run it is right now.
if type unminimize >/dev/null 2>&1; then
    # unminimize is meant for interactive use, hopefully piping from "yes" does
    # the trick...
    yes | $SUDO unminimize
fi

# Packages that are needed later by this script
early_dependencies=(
    ca-certificates  # needed by wget to download over https
    gnupg  # needed by apt-key
    libglu1-mesa  # dependency of virtualgl
    libxtst6  # dependency of virtualgl
    libxv1  # dependency of virtualgl
    wget
)
$SUDO apt-get -o Acquire::Retries=5 install --no-install-recommends -y \
      ${early_dependencies[@]}


# These files allow to configure the NeuroDebian repository in a similar way as
# the method described on http://neuro.debian.net/, without requiring insecure
# HTTP connection or network access to the sometimes unreliable key servers.
#
# If NeuroDebian update their repository or key, we may need to update these
# files. (use 'apt-key export' to write neurodebian-key.gpg).
$SUDO cp /build/neurodebian.sources.list \
         /etc/apt/sources.list.d/neurodebian.sources.list
$SUDO apt-key add /build/neurodebian-key.gpg


###############################################################################
# Install runtime dependencies with apt-get
###############################################################################

$SUDO apt-get -o Acquire::Retries=3 update


# Runtime dependencies of FSL
fsl_runtime_dependencies=(
    bc
    dc
    libopenblas-base
    tcsh
)

# Runtime dependencies of MATLAB
matlab_runtime_dependencies=(
    lsb-core
    libxext6
    libxt6
    libxmu6
)

# Generally useful packages
generally_useful_packages=(
    ca-certificates
    curl
    file
    ipython3  # for interactive Python use
    jupyter-notebook  # for interactive Python use
    less
    lsb-release
    python3-pip
    python3-setuptools  # needed for most source installs with python3-pip
    ssh-client  # notably useful for Git repositories over SSH
    sudo
    tree
    unzip
    wget
    xz-utils
    lxterminal
    gpicview
    vim
    mousepad
    nano
    openjdk-11-jre # java is used by some external tools (populse mri_conv...)
    openjdk-11-jre-headless
    jarwrapper
    java-common
    java-wrappers
    fonts-noto-color-emoji
)

# Dependencies of headless Anatomist
headless_anatomist_dependencies=(
    mesa-utils
    x11-utils
    xvfb
)

cd /tmp
wget https://sourceforge.net/projects/virtualgl/files/2.6.5/virtualgl_2.6.5_amd64.deb
$SUDO dpkg -i virtualgl_2.6.5_amd64.deb
rm -f /tmp/virtualgl_2.6.5_amd64.deb

# Runtime dependencies of PIP-installed packages (to be reviewed regularly)
pip_packages_runtime_dependencies=(
    python3-click  # dependency of nipype
    python3-isodate  # dependency of nipype
    # python3-nibabel  # too old for dipy 1.4.1, thus installed with pip
    python3-prov  # dependency of nipype
    # python3-rdflib  # too old for nipype 1.6.1, thus installed with pip
    python3-simplejson  # dependency of nipype
    python3-tqdm  # dependency of dipy
)

# Python packages needed at runtime by BrainVISA
brainvisa_python_runtime_dependencies=(
    python-is-python3

    python3-crypto
    python3-cryptography  # needed by populse_mia
    python3-html2text
    python3-mysqldb
    python3-openpyxl
    python3-paramiko
    python3-pil  # used in anatomist, morphologist, nuclear_imaging, snapbase
    python3-requests
    python3-six
    python3-sqlalchemy
    python3-traits
    python3-xmltodict
    python3-yaml
    python3-joblib
    python3-configobj
    python3-mpi4py
    # python3-nipype  # not packaged in APT -> use PIP
    python3-nibabel
    python3-pyparsing
    python3-pydot
    python3-pydicom

    cython3
    python3-xlrd
    python3-xlwt
    python3-pandas
    python3-lark

    # The following dependencies are installed with pip for various reasons,
    # see install_pip_dependencies.sh.
    #
    # TODO: when upgrading the base system (i.e. switching to Ubuntu 20.04),
    # check that they work when installed with apt.
    #
    python3-zmq
    python3-ipython
    python3-jupyter-client
    python3-qtconsole
    python3-nbsphinx
    python3-sphinx-gallery

    python3-pkgconfig  # TODO: check if necessary for h5py installation
    python3-numpy
    # python3-dipy  # not packaged in APT -> use pip
    python3-fastcluster
    python3-h5py
    python3-matplotlib
    python3-scipy
    python3-skimage
    python3-sklearn

    python3-sip
    python3-pyqt5
    python3-pyqt5.qtmultimedia
    python3-pyqt5.qtopengl
    python3-pyqt5.qtsvg
    python3-pyqt5.qtwebkit
    python3-pyqt5.qtsql
    python3-pyqt5.qtwebsockets
    python3-pyqt5.qtxmlpatterns

    python3-plotly
)


# Dynamic libraries needed at runtime by BrainVISA
#
# This list is generated **automatically** with the list-shared-libs-paths.sh
# script. In order to generate this list, run the following command in a
# casa-dev container where the whole BrainVISA tree has been compiled:
#
# <casa-distro>/share/list-shared-lib-packages.sh /casa/build /usr/local
#
# Please DO NOT add other packages to this list, so that it can be wiped and
# regenerated easily. If other libraries are needed, consider creating a new
# variable to store them.
brainvisa_shared_library_dependencies=(
    libdcmtk15
    libgfortran5
    libgl1
    libglu1-mesa
    libgomp1
    libjpeg-turbo8
    libminc2-5.2.0
    libnetcdf18
    libopenjp2-7
    libpython3.8
    libqt5core5a
    libqt5gui5
    libqt5multimedia5
    libqt5network5
    libqt5opengl5
    libqt5sql5
    libqt5widgets5
    libqwt-qt5-6
    libsigc++-2.0-0v5
    libstdc++6
    libsvm3
    libtiff5
    libxml2
)

# Programs and data that BrainVISA depends on at runtime
brainvisa_misc_runtime_dependencies=(
    lftp
    sqlite3
    xbitmaps
)

# Other dependencies of BrainVISA (please indicate the installation reason for
# each dependency).
brainvisa_other_dependencies=(
    # libjxr is needed for openslide (MIRCen's fork with CZI support)
    libjxr0
    # To avoid the "QSqlDatabase: QSQLITE driver not loaded" warning that is
    # displayed at the start of each executable.
    libqt5sql5-sqlite
    # mcverter command of mriconvert has a dependency on libpng. This makes it
    # difficult to be mounted and used from a host directory when there is a
    # version mismatch for that library.
    mriconvert
    # dcmtk commandlines (including dcmdjpeg)
    dcmtk
)

# Dependencies that are needed for running BrainVISA tests in casa-run
brainvisa_test_dependencies=(
    cmake  # BrainVISA tests are driven by ctest
)

###############################################################################
# Install build dependencies that are necessary for install_pip_dependencies.sh
# and install_compiled_dependencies.sh
###############################################################################

# The build_dependencies bash array variable is defined in build_dependencies.sh, which is sourced at the top of this script.


# Hopefully, using a large value for Acquire::Retries can solve the infamous
# 101st package issue (fetching more than 100 packages in a single apt-get
# invocation sometimes fails in NeuroSpin, probably due to flaky firewall
# rules).
$SUDO apt-get -o Acquire::Retries=20 install --no-install-recommends -y \
    ${fsl_runtime_dependencies[@]} \
    ${matlab_runtime_dependencies[@]} \
    ${generally_useful_packages[@]} \
    ${headless_anatomist_dependencies[@]} \
    ${brainvisa_misc_runtime_dependencies[@]} \
    ${brainvisa_other_dependencies[@]} \
    ${brainvisa_test_dependencies[@]} \
    ${pip_packages_runtime_dependencies[@]} \
    ${brainvisa_python_runtime_dependencies[@]} \
    ${brainvisa_shared_library_dependencies[@]} \
    ${build_dependencies[@]}

###############################################################################
# Free disk space by removing APT caches
###############################################################################

$SUDO apt-get clean

if [ -z "$APT_NO_LIST_CLEANUP" ]; then
    # delete all the apt list files since they're big and get stale quickly
    $SUDO rm -rf /var/lib/apt/lists/*
fi
