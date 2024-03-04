# casa-distro
Unified development environment for BrainVISA projects.

## Test Conda packages

```
CONDA=/tmp/somewhere
wget https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh
sh Miniforge3-Linux-x86_64.sh -b -p "$CONDA"
. "$CONDA/bin/activate"
mamba install -c https://brainvisa.info/download/conda brainvisa
```

## Setup Conda development environment

All compilation dependencies are taken from conda-forge repository.

Al the necessary steps to setup a Conda based developement environment are contained in the package `brainvisa-forge` that can be installed:

```shell
# Install a conda environment that integrates mamba and points to conda-forge by default
CONDA=/tmp/somewhere
wget https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh
sh Miniforge3-Linux-x86_64.sh -b -p "$CONDA"

# Adds BrainVISA repository to the environment
"$CONDA/bin/mamba" run conda config --env --add channels https://brainvisa.info/download/conda
# Install brainvisa-forge
"$CONDA/bin/mamba" install brainvisa-forge
```

Now you may want to edit `$CONDA/conf/bv_maker.cfg` select the brainvisa-cmake pakage and branch you want to compile (by default package is `brainvisa`and branch is `master`). You can also edit `$CONDA/conf/bv_maker.cfg` but be aware that it is a symbolic link to a version in casa-distro sources. If you modify it you should replace the symlink by a real copy of the file first.

Then you can activate the environment and run `bv_maker` as described in the following steps.

## Use a Conda development environment

The usage of a Conda based casa-distro environment uses the activation/deactiavtion system shipped with Conda. In order to "enter" the developpment environment (that means mainly setting environment variables such as PATH, etc.), on can use:

```
. {dir}/conda/bin/activate
```

It is possible de "go back" to the initial environment with the following command:

```
conda deactivate
```

## Software building

Once the development environment is activated, all commands from build tree are in `PATH` and can be used directly, including `bv_maker`. During the installation of `brainvisa-forge` package, source codes for casa-distro and brainvisa-cmake are downloades and put in the PATH. Therefore, `bv_maker` can be directly used when the environment is activated. This will launch the command from the source tree an create a build tree. Next calls to `bv_maker` will use the build tree version.

## Build and publish Conda packages

Conda packages are build using brainvisa-cmake component and packages (packages were called component groups in former version of brainvisa-cmake). A single brainvisa-cmake package must be selected to create a full repository with this package an all dependent packages and components. In this repository, two kind of conda packages are created:

- each brainvisa-cmake components has a conda package with its own version
- each branvisa-cmake package that is not a component uses a repository global distro version

The repository directory is created with the following commands where:
- *`{repository_path}`* is the path of a non existant (or empty) directory where packages and index files will be put.
- *`{package}`* is the name of the top-level package to install. For instance `brainvisa` or `brainvisa-cea`.
- *`{global_version}`* is the version used for all packages not corresponding to a brainvsa-cmake component.

```
# Make sure compilation is up to date.
bv_maker
python -m casa_distro.conda_packages {repository_path} {package} {global_version}
```

This creates a full Conda repository in the directory `{repository_path}`. This directory can be used directly with `conda install` or `mamba install` with the `-c` option.

Publishing the repository on the web can be simply done by exposing the repository directory on a server. For publishing on the still experimental server `https://brainvisa.info/download/conda`, one can use: 

```
# Do not forget the trailing / on the repository path
rsync -a --progress --delete {repository_path}/ brainvisa@brainvisa.info:/var/www/html/brainvisa.info_download/conda/
```

## Licence
This project is distributed under [CeCILL-B licence](http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html)
