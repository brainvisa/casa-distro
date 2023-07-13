# casa-distro
Unified development environment for BrainVISA projects.

## Setup development environment

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
