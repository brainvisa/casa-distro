# Casaconda
Experimental project to test BrainVISA compilation using a build environment setup using Conda.

## Setup of a build environment using Conda

### From scratch

Install OpenGL dev packages
```
sudo apt install libglu1-mesa-dev
```

Select a directory
```
casaconda=/somewhere
```

Download project with config (and source list)
```
git clone https://github.com/sapetnioc/casaconda "$casaconda"
```

Download sources and setup conda directory
```
"$casaconda/setup_dev"
```

Build everything
```
"$casaconda/bv_env" bv_maker
```

At the time of this writing, documentation building is failing.

### Build a repository for Anatomist

It is necessary to have a complete build environment since the packaging scripts only do packages with `make install...` commands.

Install Conda build
```
"$casaconda/conda/bin/mamba" install -y conda-build
```

Run the package creation recipe
```
"$casaconda/conda/bin/mamba" build ~/casaconda/recipe
```

Publish the resulting repository
```
rsync -a --delete "$casaconda/conda/conda-bld/" brainvisa@brainvisa.info:/var/www/html/brainvisa.info_download/conda/
```

### Install Anatomist from a repository

One can use the repository located in `https://brainvisa.info/download/conda` but it can be replaced by a local directory too, for instance: `file:///home/me/casaconda/conda/conda-bld`.

Install OpenGL libraries (tested on Ubuntu/Windows-WSL2)
```
sudo apt install libgl1-mesa-glx libopengl
```

Select an install directory:
```
conda=/tmp/conda
```

Install Conda. I recommend installing a version that incorporates Mamba (a really much faster C++ implementation for resolving package dependencies) and that defaults to conda-forge (a very well-maintained community package repository with no legal constraints on use).
```
cd /tmp
wget https://github.com/conda-forge/miniforge/releases/latest/download/Mambaforge-Linux-x86_64.sh
sh Mambaforge-Linux-x86_64.sh -ubp "$conda"
rm Mambaforge-Linux-x86_64.sh
```

Install Anatomist. It is possible to substitute the repository located in `https://brainvisa.info/download/conda` by a local directory, for instance: `file:///home/me/casaconda/conda/conda-bld`.

```
"$conda/bin/mamba" install -c https://brainvisa.info/download/conda -y anatomist
```


Activate the conda repository and use Anatomist, Aims or whatever:
```
. "$conda/bin/activate"
anatomist
```
