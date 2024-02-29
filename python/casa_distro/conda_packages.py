from itertools import chain
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile
import yaml

from brainvisa_cmake.brainvisa_projects import packages_definition
from brainvisa_cmake.utils import get_components_info

dependencies_translation = {
    "redis": ["redis-py"],
}
packages_metadata = {
    "brainvisa-base": {
        "depends": {
            "conda-forge": [
                "{{ pin_compatible('libstdcxx-ng', min_pin='x.x', max_pin='x') }}",
                "{{ pin_compatible('libgcc-ng', min_pin='x.x', max_pin='x') }}",
                "font-ttf-noto-emoji",
                "lsb-release",
                "matplotlib 3.4.3",
                "mesa",
                "pyqt",
                "qtconsole",
                "xorg-libx11",
                "pydantic >=1.9",
                "redis-py >=4.2",
                "nipype",
                "dipy",
                "pycryptodome",
                "cryptography",
                "html2text",
                "openpyxl",
                "paramiko",
                "pillow",
                "requests",
                "six",
                "sqlalchemy",
                "traits",
                "xmltodict",
                "yaml",
                "joblib",
                "configobj",
                "mpi4py",
                "nibabel",
                "pyparsing",
                "pydot",
                "pydicom",
                "cython",
                "xlrd",
                "xlwt",
                "pandas",
                "lark",
                "pyzmq",
                "ipython",
                "nbsphinx",
                "sphinx-gallery",
                "numpy",
                "fastcluster",
                "h5py",
                "scipy",
                "scikit-image",
                "pyopengl",
                "plotly",
                "pcl",
                "celery",
                "pycryptodome",
                "gdk-pixbuf",
                "libgfortran5",
                "cairo",
                "dcmtk",
                "libgfortran5",
                "libglib",
                "libglu",
                "libgomp",
                "hdf5",
                "libjpeg-turbo",
                "jxrlib",
                "libllvm14",
                "netcdf4",
                "openjpeg",
                "libpng",
                "qwt",
                "libsigcpp<3",
                "libsvm",
                "libtiff",
                "libxml2",
                "zstd",
                "libnetcdf",
                "draco",
                "pyqtwebkit",
                "pyqtwebengine",
                "pytorch",
                "torchvision",
                "pywebp",
            ],
            "brainvisa-forge": [
                "brainvisa-virtualgl",
            ],
            "pip": [
                "pygltflib",
            ],
        }
    },
}


def generate_rattler_recipe(tmp, distro, distro_version, build_number=0, build=None):
    recipe = {
        "context": {
            "name": distro,
            "version": distro_version,
            # "build_environment": os.environ["CASA"],
        },
        "outputs": [],
    }

    components_info = get_components_info()
    distro_info = packages_definition[distro]
    packages = {distro} | distro_info["all_packages"]

    def package_version(package):
        version = None
        if package in extended_packages_definition:
            version = extended_packages_definition[package].get("version")
            if version is None:
                version = components_info.get(package, {}).get("version")
            if version is None:
                version = distro_version
        if version is None:
            o = subprocess.check_output(["conda", "list", "-f", "--json", package])
            l = json.loads(o)
            if l:
                version = l[0].get("version")
        return version

    def pin_compatible(
        package,
        min_pin="x.x.x.x.x.x",
        max_pin="x",
    ):
        from conda_build.jinja_context import apply_pin_expressions

        version = package_version(package)
        spec = apply_pin_expressions(version, min_pin=min_pin, max_pin=max_pin)
        return f"{package} {spec}"

    extended_packages_definition = packages_definition.copy()
    extend_packages = []
    for component in packages:
        component_info = components_info.get(component)
        if component_info:
            for n, d in component_info.get("alternative_depends", {}).items():
                version = component_info["version"]
                alternative_package = f"{component}-{n}"
                extend_packages.append(alternative_package)
                extended_packages_definition[alternative_package] = {
                    "version": version,
                    "depends": [
                        f"{component}=={version}",
                    ]
                    + d,
                }
    packages.update(extend_packages)

    # https://docs.conda.io/projects/conda-build/en/stable/resources/package-spec.html
    for package in packages:
        package_info = extended_packages_definition[package]
        metadata = packages_metadata.get(package, {})
        version = package_version(package)
        component_info = components_info.get(package)

        # Parse and resolve package dependencies
        component_depends = []
        if component_info:
            for d in component_info.get("depends", []):
                l = d.split(None, 1)
                if len(l) == 1:
                    p = l[0]
                    v = None
                else:
                    p, v = l
                t = dependencies_translation.get(p)
                if t is None:
                    component_depends.append(d)
                else:
                    for i in t:
                        if v:
                            component_depends.append(f"{i} {v}")
                        else:
                            component_depends.append(i)

        if package not in (
            "brainvisa-base",
            "brainvisa-cmake",
            "capsul",
            "casa-distro",
            "populse-db",
            "soma-base",
            "soma-io",
            "soma-workflow",
        ):
            depends = {f"brainvisa-base=={distro_version}"}
        else:
            depends = set()
        for p in package_info.get("packages", ()):
            v = package_version(p)
            depends.add(f"{p}=={v}")
        for d in chain(
            component_depends,
            package_info.get("depends", []),
            metadata.get("depends", {}).get("conda-forge", []),
            metadata.get("depends", {}).get("brainvisa-forge", []),
        ):
            m = re.match("^{{(.*)}}", d)
            if m:
                d = eval(m.group(1))
            depends.add(d)

        info = {
            "package": {
                "name": package,
                "version": version,
            },
            "requirements": {
                "run": list(depends),
            },
        }

        about = package_info.get("about")
        if about:
            about.pop("license", None)
            info["about"] = about

        if component_info:
            build_script = """CASA=$(dirname $(dirname $(dirname $CONDA_PYTHON_EXE)))
cd "$CASA/build"
unset CONDA_DEFAULT_ENV
unset CONDA_PREFIX
env BRAINVISA_INSTALL_PREFIX="$PREFIX" "$CASA/conda/bin/mamba" run make install-$PKG_NAME
env BRAINVISA_INSTALL_PREFIX="$PREFIX" "$CASA/conda/bin/mamba" run make install-$PKG_NAME-usrdoc
"""
        else:
            build_script = None

        # Write post install script if there are some
        # pip dependencies
        pip_dependencies = metadata.get("depends", {}).get("pip", [])
        if pip_dependencies:
            (tmp / "bin").mkdir(exist_ok=True)
            with open(tmp / "bin" / f".{package}-post-link.sh", "w") as f:
                print(
                    f'python -m pip install -q {" ".join(pip_dependencies)} '
                    '> "$PREFIX/.messages.txt"',
                    file=f,
                )
            if not build_script:
                build_script = ""
            build_script += """if [ ! -e "$PREFIX/bin" ]; then mkdir "$PREFIX/bin"; fi
cp "$RECIPE_DIR/bin/.$PKG_NAME-post-link.sh" "$PREFIX/bin/.$PKG_NAME-post-link.sh"
"""
        if build_script:
            info["build"] = {"script": build_script}
        recipe["outputs"].append(info)
    with open(tmp / "recipe.yaml", "w") as f:
        yaml.dump(recipe, f)


def generate_repository(repository, distro, distro_version, build_number=0, build=None):
    # Create a temporary directory for hosting package content
    with tempfile.TemporaryDirectory() as tmp_str:
        tmp = pathlib.Path(tmp_str)
        generate_rattler_recipe(tmp, distro, distro_version, build_number, build)
        with open(tmp / "build-component.sh", "w") as f:
            f.write(
                """CASA=$(dirname $(dirname $(dirname $CONDA_PYTHON_EXE)))
cd "$CASA/build"
unset CONDA_DEFAULT_ENV
unset CONDA_PREFIX
env BRAINVISA_INSTALL_PREFIX="$PREFIX" "$CASA/conda/bin/mamba" run make install-$PKG_NAME
env BRAINVISA_INSTALL_PREFIX="$PREFIX" "$CASA/conda/bin/mamba" run make install-$PKG_NAME-usrdoc
if [ -e "$RECIPE_DIR/bin/$PKG_NAME-post-link.sh" ]; then
  cp "$RECIPE_DIR/bin/$PKG_NAME-post-link.sh" "$PREFIX/bin/.$PKG_NAME-post-link.sh"
fi
"""
            )
        subprocess.check_call(
            ["rattler-build", "build", "--output-dir", repository, "-r", tmp_str]
        )


if __name__ == "__main__":
    repository = pathlib.Path(sys.argv[1])
    distro = sys.argv[2]
    distro_version = sys.argv[3]

    conda = os.environ.get("CONDA_PREFIX")
    if not conda:
        print(
            "Variable CONDA_PREFIX is not defined. Is your development environment activated ?",
            file=sys.stderr,
        )
        sys.exit(1)
    if repository.exists() and next(repository.iterdir(), None):
        # repository exists and is not empty
        print(f"Please delete directory {repository}.", file=sys.stderr)
        sys.exit(1)

    generate_repository(repository, distro, distro_version)
