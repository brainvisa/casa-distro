# Directory containing all files used to configure a build directory (svn passwords, bv_maker.cfg, etc.)
if [ -z "$CASA_CONF" ]; then
    export CASA_CONF=/casa/host/conf
fi
# Directory containing source code
if [ -z "$CASA_SRC" ]; then
    export CASA_SRC=/casa/host/src
fi
# Directory containing all files that are necessary only for building (source tree, build dir, etc.)
if [ -z "$CASA_BUILD" ]; then
    export CASA_BUILD=/casa/host/build
fi
# Installation directory
if [ -z "$CASA_INSTALL" ]; then
    export CASA_INSTALL=/casa/host/install
fi
# Installation directory
if [ -z "$CASA_PACK" ]; then
    export CASA_PACK=/casa/host/pack
fi
# Tests data directory
if [ -z "$CASA_TESTS" ]; then
    export CASA_TESTS=/casa/host/tests
fi

# Set variable to make bv_maker use /casa/host/conf/bv_maker.cfg by default
if [ -z "$BRAINVISA_BVMAKER_CFG" ]; then
    export BRAINVISA_BVMAKER_CFG="$CASA_CONF/bv_maker.cfg"
fi

PATH=${CASA_BUILD}/bin:${PATH}:/usr/local/bin:/casa/brainvisa-cmake/bin
LD_LIBRARY_PATH=/casa/host/lib:${LD_LIBRARY_PATH}
export PATH LD_LIBRARY_PATH
if [ -f "${CASA_BUILD}/bin/bv_env.sh" ]; then
    . "${CASA_BUILD}/bin/bv_env.sh"
fi
