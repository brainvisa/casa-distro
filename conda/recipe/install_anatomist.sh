components="anatomist-free anatomist-gpl"

export CASA=$RECIPE_DIR/..
export BRAINVISA_INSTALL_PREFIX="$PREFIX"
cd "$CASA/build"
for component in $components; do
    "$CASA/bv_env" make install-$component
done
