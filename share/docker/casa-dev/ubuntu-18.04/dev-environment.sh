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

PATH=${PATH}:/usr/local/bin
PATH=${PATH}:/casa/host/bootstrap/brainvisa-cmake/bin
PATH=${PATH}:/casa/bootstrap/brainvisa-cmake
LD_LIBRARY_PATH=/casa/host/lib:${LD_LIBRARY_PATH}
export PATH LD_LIBRARY_PATH
if [ -f "${CASA_BUILD}/bin/bv_env.sh" ] \
   && [ -f "${CASA_BUILD}/bin/bv_env" ]; then
    # need to update the path to help bv_env.sh to find out its installation
    PATH="${CASA_BUILD}/bin:${PATH}"
    . "${CASA_BUILD}/bin/bv_env.sh"
    branch="$CASA_BRANCH"
    if [ "$branch" = "bug_fix" ]; then
        branch="master"
    fi
    if [ -d "/casa/host/src/development/casa-distro/$branch/cbin" ]; then
        export PATH="/casa/host/src/development/casa-distro/$branch/cbin:$PATH"
    fi
    unset branch
fi
