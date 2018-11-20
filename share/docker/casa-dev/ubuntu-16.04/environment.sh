# Directory containing all files used to configure a build directory (svn passwords, bv_maker.cfg, etc.)
export CASA_CONF=/casa/conf
# Directory containing source code
export CASA_SRC=/casa/src
# Directory containing all files that are necessary only for building (source tree, build dir, etc.)
export CASA_BUILD=/casa/build
# Installation directory
export CASA_INSTALL=/casa/install
# Installation directory
export CASA_PACK=/casa/pack
# Tests data directory
export CASA_TESTS=/casa/tests
# Custom projects
export CASA_CUSTOM_SRC=/casa/custom/src
export CASA_CUSTOM_BUILD=/casa/custom/build

# Set variable to make bv_maker use /casa/conf/bv_maker.cfg by default
export BRAINVISA_BVMAKER_CFG="$CASA_CONF/bv_maker.cfg"

export PATH=${PATH}:/casa/brainvisa-cmake/bin
if [ -f "${CASA_BUILD}/bin/bv_env.sh" ]; then
    OLD_CWD=$(pwd)
    cd ${CASA_BUILD}/bin
    PATH=.:"$PATH"
    . ./bv_env.sh
    cd ${OLD_CWD}
    unset OLD_CWD
fi
