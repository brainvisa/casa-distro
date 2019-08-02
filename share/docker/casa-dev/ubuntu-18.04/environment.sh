# Directory containing all files used to configure a build directory (svn passwords, bv_maker.cfg, etc.)
if [ -z "$CASA_CONF" ]; then
    export CASA_CONF=/casa/conf
fi
# Directory containing source code
if [ -z "$CASA_SRC" ]; then
    export CASA_SRC=/casa/src
fi
# Directory containing all files that are necessary only for building (source tree, build dir, etc.)
if [ -z "$CASA_BUILD" ]; then
    export CASA_BUILD=/casa/build
fi
# Installation directory
if [ -z "$CASA_INSTALL" ]; then
    export CASA_INSTALL=/casa/install
fi
# Installation directory
if [ -z "$CASA_PACK" ]; then
    export CASA_PACK=/casa/pack
fi
# Tests data directory
if [ -z "$CASA_TESTS" ]; then
    export CASA_TESTS=/casa/tests
fi
# Custom projects
if [ -z "$CASA_CUSTOM_SRC" ]; then
    export CASA_CUSTOM_SRC=/casa/custom/src
fi
if [ -z "$CASA_CUSTOM_BUILD" ]; then
    export CASA_CUSTOM_BUILD=/casa/custom/build
fi

# Set variable to make bv_maker use /casa/conf/bv_maker.cfg by default
if [ -z "$BRAINVISA_BVMAKER_CFG" ]; then
    export BRAINVISA_BVMAKER_CFG="$CASA_CONF/bv_maker.cfg"
fi

export PATH=${PATH}:/usr/local/bin:/casa/brainvisa-cmake/bin
if [ -f "${CASA_BUILD}/bin/bv_env.sh" ]; then
    OLD_CWD=$(pwd)
    cd ${CASA_BUILD}/bin
    PATH=.:"$PATH"
    . ./bv_env.sh
    cd ${OLD_CWD}
    unset OLD_CWD
fi
