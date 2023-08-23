components="morpho-deepsulci morphologist-ui morphologist-gpl morphologist-nonfree sulci-nonfree sulci-models-data"

export CASA=$RECIPE_DIR/../../../../..
export BRAINVISA_INSTALL_PREFIX="$PREFIX"
cd "$CASA/build"
for component in $components; do
    make install-$component
done

