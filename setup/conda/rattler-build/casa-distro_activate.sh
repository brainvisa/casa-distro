for i in "$CONDA_PREFIX/build/bin/bv_env.sh" "$CONDA_PREFIX/src/brainvisa-cmake/bin/bv_env.sh" "$CONDA_PREFIX/src/development/brainvisa-cmake/*/bin/bv_env.sh"; do
    if [ -e "$i" ]; then
        bv_env_sh="$i"
        break
    fi
done
if [ -n "$bv_env_sh" ]; then
    . "$bv_env_sh"
fi
