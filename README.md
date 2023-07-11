[![travis](https://travis-ci.com/brainvisa/casa-distro.svg?branch=master)](https://travis-ci.com/brainvisa/casa-distro)
[![codecov](https://codecov.io/gh/brainvisa/casa-distro/branch/master/graph/badge.svg)](https://codecov.io/gh/brainvisa/casa-distro)

# casa-distro
Unified development environment for BrainVISA projects.

## Setup development environment

```shell
sh <(curl -s https://raw.githubusercontent.com/brainvisa/casa-distro/setup/conda/setup) /somewhere```
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
