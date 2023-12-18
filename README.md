# casa-distro
Unified development environment for BrainVISA projects.

## Test Conda packages

```
CONDA=/tmp/somewhere
wget https://github.com/conda-forge/miniforge/releases/latest/download/Mambaforge-Linux-x86_64.sh
sh Mambaforge-Linux-x86_64.sh -b -p "$CONDA"
. "$CONDA/bin/activate"
mamba install -c https://brainvisa.info/download/conda brainvisa
```

## Setup Conda development environment

All compilation dependencies are taken from conda-forge repository except low level OpenGL library that must be installed on the host system. On Debian based distro (such as Ubuntu) this can be done by installing `libglu1-mesa-dev` package with `apt install` command.

The up to date setup process is contained in [a shell script that is stored on GitHub](https://raw.githubusercontent.com/brainvisa/casa-distro/conda/setup/conda/setup) and requires two parameters:
- `{dir}`: the path of the development directory that is to be created and setup.
- `{package}`: the name of a predefined set of software components. This package name is passed to brainvisa-cmake to select components. It can be any package defined in brainvisa-cmake but here are the most useful:
  - brainvisa-dev: all components whose sources are publicly available.
  - brainvisa: components included in BrainVISA distribution.
  - brainvisa-cea: components deployed in Neurospin, MirCEN and SHFJ labs.
  - brainvisa-cati: components used internally by CATI members.
  - brainvisa-web: components necessary to build brainvisa.info web site.

The following command (where `{dir}` and `{package}` must be replaced) can be used in a shell to directly download and execute the setup script:

```shell
sh <(curl -s https://raw.githubusercontent.com/brainvisa/casa-distro/conda/setup/conda/setup) {dir} {package}
```
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

Once the development environment is activated, all commands from build tree are in `PATH` and can be used directly, including `bv_maker`. However, some projects are still using the `conda` branch that makes the `bv_maker sources` fail. Therefore, until all is merged in master branch, it is necessary to run separatly `bv_maker source` from other commands such as `bv_maker configure build`.

## Build and publish Conda packages

Conda packages are build using brainvisa-cmake component and packages (packages were called component groups in former version of brainvisa-cmake). A single brainvisa-cmake package must be selected to create a full repository with this package an all dependent packages and components. In this repository, two kind of conda packages are created:

- each brainvisa-cmake components has a conda package with its own version
- each branvisa-cmake package that is not a component uses a repository global distro version

The repository directory is created with the following commands where:
- *`{repository_path}`* is the path of a non existant (or empty) directory where packages and index files will be put.
- *`{package}`* is the name of the top-level package to install. For instance `brainvisa` or `brainvisa-cea`.
- *`{global_version}`* is the version used for all packages not corresponding to a brainvsa-cmake component.

```
# Make sure compilation is up to date. To date doc is not taken into account.
bv_maker configure build
python -m casa_distro.conda_packages {repository_path} {package} {global_version}
```



This creates a full Conda repository in the directory `{repository_path}`. This directory can be used directly with `conda install` or `mamba install` with the `-c` option.

Publishing the repository on the web can be simply done by exposing the repository directory on a server. For publishing on the still experimental server `https://brainvisa.info/download/conda`, one can use: 

```
# Do not forget the trailing / on the repository path
rsync -a --progress --delete {repository_path}/ brainvisa@brainvisa.info:/var/www/html/brainvisa.info_download/conda/
```

## Documentation

* on github, master branch: https://brainvisa.github.io/casa-distro/
* Stable version: see http://brainvisa.info/casa-distro/

## Contributing

This repository uses [pre-commit](https://pre-commit.com/) to ensure that all committed code follows minimal quality standards. Please install it and configure it to run as part of ``git commit`` by running ``pre-commit install`` in your local repository:

```shell
python3 -m venv venv  # use Python 3.6 or more recent
pip install -U pip
pip install pre-commit
pre-commit install  # set up the hook (to run pre-commit during 'git commit')
```


## Licence
This project is distributed under [CeCILL-B licence](http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html)
