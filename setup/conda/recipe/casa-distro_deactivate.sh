for i in "$CONDA_PREFIX/../build/bin/bv_unenv.sh" "$CONDA_PREFIX/../src/brainvisa-cmake/bin/bv_unenv.sh" "$CONDA_PREFIX/../src/development/brainvisa-cmake/*/bin/bv_unenv.sh"; do
    if [ -e "$i" ]; then
        bv_unenv_sh="$i"
        break
    fi
done
if [ -n "$bv_unenv_sh" ]; then
    . "$bv_unenv_sh"
fi
