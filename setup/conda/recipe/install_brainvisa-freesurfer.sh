components="brainvisa_freesurfer"

export CASA=$RECIPE_DIR/../../../../..
export BRAINVISA_INSTALL_PREFIX="$PREFIX"
cd "$CASA/build"
for component in $components; do
    make install-$component
done

