# casa-distro
Unified development environment for BrainVISA projects.

## Setup Conda development environment

```shell
sh <(curl -s https://raw.githubusercontent.com/brainvisa/casa-distro/conda/setup/conda/setup) {dir} {package}
```

Where `{dir}` is the path of the development directory and `{package}` is the name of a predefined set of software components. These package name is passed to brainvisa-cmake to select components. It can be any 
package defined in brainvisa-cmake but here are the most useful:

- brainvisa-dev: all components whose sources are publicly available.
- brainvisa: components included in BrainVISA distribution.
- brainvisa-cea: components deployed in Neurospin, MirCEN and SHFJ labs.
- brainvisa-cati: components used internally by CATI members.
- brainvisa-web: components necessary to build brainvisa.info web site.

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

Conda packages are build using brainvisa-cmake component. Conda packages are defined in the `setup/conda/recipe/brainvisa.yaml` file. Each package can contain files of one or more brainvsa-cmake component. For each component files are copied using `make install` from build tree. Therefore, a full compilation with `bv_maker` must be done before creating packages. Package creation is done with the following command:

```
mamba build $CASA_SRC/casa-distro/setup/conda/recipe
```

This creates a full Conda repository in the directory `conda/conda-bld`. This directory can be used directly with `conda install` or `mamba install` with the `-c` option. Note, that `-c` requires URLs, therefore the directory must be absolute and prefixed with `file://`.

Publishing the repository on the web can be simply done by exposing the `conda-bld` files on a server. For publishing on the still experimental server `https://brainvisa.info/download/conda`, one can use: 

```
rsync -a --delete "$CONDA_PREFIX/conda-bld/" brainvisa@brainvisa.info:/var/www/html/brainvisa.info_download/conda/
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
