components="capsul populse_db soma-base soma-io soma-workflow casa-distro"

export CASA=$RECIPE_DIR/../../../../..
export BRAINVISA_INSTALL_PREFIX="$PREFIX"
cd "$CASA/build"
for component in $components; do
    make install-$component
done

