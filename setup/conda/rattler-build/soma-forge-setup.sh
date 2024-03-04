export CASA_SRC="$CONDA_PREFIX/src"

if [ ! -e "$CASA_SRC" ]; then
    mkdir --parents "$CASA_SRC"
    # Temporarily force "conda" branches of some projects
    git -C "$CASA_SRC" clone --branch conda https://github.com/brainvisa/casa-distro
    git -C "$CASA_SRC" clone https://github.com/brainvisa/brainvisa-cmake
fi

if [ ! -e "$CONDA_PREFIX/conf" ]; then
    mkdir "$CONDA_PREFIX/conf"
fi
if [ ! -e "$CONDA_PREFIX/conf/bv_maker.cfg" ]; then
    ln -s ../src/casa-distro/setup/conda/bv_maker.cfg "$CONDA_PREFIX/conf/bv_maker.cfg"
fi

if [ ! -e "$CONDA_PREFIX/mesalib" ]; then
    # For the compilation of OpenGL packages, it is necessary to have include files
    # and dynamic libraries from mesalib packages. However, this package must not
    # be installed otherwise any software using Qt and OpenGL will crash. Therefore,
    # the content of the mesalib package is extracted here and put in "$CONDA/mesalib"
    # directory to be used during compilation but not during execution.
    "$CONDA_PREFIX/bin/mamba" run python "$CONDA_PREFIX/src/casa-distro/setup/conda/extract_mesalib.py" "$CONDA_PREFIX/mesalib"
fi

# if [ ! -e "$CASA/brainvisa-forge" ]; then
#     cd "$CASA_DISTRO_SRC/setup/conda/rattler-build"
#     for d in *; do
#         rattler-build build -r $d --output-dir "$CASA/brainvisa-forge"
#     done
#     conda config --env --add channels "$CASA/brainvisa-forge"
# fi