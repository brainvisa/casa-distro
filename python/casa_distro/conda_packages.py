from itertools import chain
import json
import os
import pathlib
import re
import subprocess
import sys
import tarfile
import tempfile

from brainvisa_cmake.brainvisa_projects import packages_definition
from brainvisa_cmake.utils import get_components_info

dependencies_translation = {
   'redis': ['redis-py'],
}
packages_metadata = {
    'brainvisa-base': {
        'depends': [
            'sysroot-conda_2_28-x86_64',
            "{{ pin_compatible('sysroot_linux-64', max_pin='x.x') }}",
            "{{ pin_compatible('libstdcxx-ng', min_pin='x.x', max_pin='x') }}",
            "{{ pin_compatible('libgcc-ng', min_pin='x.x', max_pin='x') }}",
            'font-ttf-noto-emoji',
            'lsb-release',
            'matplotlib 3.4.3',
            'mesa',
            'pyqt',
            'qtconsole',
            'xorg-libx11',
            'pydantic >=1.9',
            'redis-py >=4.2',
            'nipype',
            'dipy',
            'pycryptodome',
            'cryptography',
            'html2text',
            'openpyxl',
            'paramiko',
            'pillow',
            'requests',
            'six',
            'sqlalchemy',
            'traits',
            'xmltodict',
            'yaml',
            'joblib',
            'configobj',
            'mpi4py',
            'nibabel',
            'pyparsing',
            'pydot',
            'pydicom',
            'cython',
            'xlrd',
            'xlwt',
            'pandas',
            'lark',
            'pyzmq',
            'ipython',
            'nbsphinx',
            'sphinx-gallery',
            'numpy',
            'fastcluster',
            'h5py',
            'scipy',
            'scikit-image',
            'pyopengl',
            'plotly',
            'pcl',
            'celery',
            'pycryptodome',
            'gdk-pixbuf',
            'libgfortran5',
            'cairo',
            'dcmtk',
            'libgfortran5',
            'mesalib',
            'libglib',
            'libglu',
            'libgomp',
            'hdf5',
            'libjpeg-turbo',
            'jxrlib',
            'libllvm14',
            'netcdf4',
            'openjpeg',
            'libpng',
            'qwt',
            'libsigcpp<3',
            'libsvm',
            'libtiff',
            'libxml2',
            'zstd',
            'libnetcdf',
            'draco',
            'pyqtwebkit'
        ]
    },
}


def generate_repository(repository, distro, distro_version,
                        build_number=0, build=None):
    if build is None:
       build = str(build_number)
    components_info = get_components_info()
    distro_info = packages_definition[distro]
    packages = {distro} | distro_info['all_packages']

    def package_version(package):
        version = None
        if package in extended_packages_definition:
            version = extended_packages_definition[package].get('version')
            if version is None:
                version = components_info.get(package, {}).get('version')
            if version is None:
              version = distro_version
        if version is None:
          o = subprocess.check_output(['conda', 'list', '-f', '--json', package])
          l = json.loads(o)
          if l:
              version = l[0].get('version')
        return version
    
    def pin_compatible(package,
        min_pin="x.x.x.x.x.x",
        max_pin="x",
    ):
        from conda_build.jinja_context import apply_pin_expressions
        version = package_version(package)
        spec = apply_pin_expressions(version, min_pin=min_pin, max_pin=max_pin)
        return f'{package} {spec}'
    
    repository = pathlib.Path(repository)
    repository.mkdir(exist_ok=True)
    l64 = repository / 'linux-64'
    l64.mkdir(exist_ok=True)

    extended_packages_definition = packages_definition.copy()
    extend_packages = []
    for component in packages:
        component_info = components_info.get(component)
        if component_info:
            for n, d in component_info.get('alternative_depends', {}).items():
                version = component_info['version']
                alternative_package = f'{component}-{n}'
                extend_packages.append(alternative_package)
                extended_packages_definition[alternative_package] = {
                    'version': version,
                    'depends': [
                        f'{component}=={version}',
                    ] + d
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
            for d in component_info.get('depends', []):
                l = d.split(None, 1)
                if len(l) == 1:
                   p = l[0]
                   v = None
                else:
                   p,v = l
                t = dependencies_translation.get(p)
                if t is None:
                    component_depends.append(d)
                else:
                    for i in t:
                        if v:
                            component_depends.append(f'{i} {v}')
                        else:
                            component_depends.append(i)
            

        depends = []
        for p in package_info.get('packages', ()):
            v = package_version(p)
            depends.append(f'{p}=={v}')
        for d in chain(component_depends, package_info.get('depends', []), metadata.get('depends', [])):
          m = re.match('^{{(.*)}}', d)
          if m:
            d = eval(m.group(1))
          depends.append(d)

        # Open the tar.bz2 archive for writing
        with tarfile.open(l64 / f'{package}-{version}.tar.bz2', mode='w:bz2') as tar:
          # Create a temporary directory for hosting package content
          with tempfile.TemporaryDirectory() as tmp_str:
            tmp = pathlib.Path(tmp_str)
            info = tmp / 'info'
            info.mkdir()
            index = {
              'name': package,
              'version': version,
              'build': build,
              'build_number': build_number,
              'depends': depends,
            }
            about = package_info.get('about')
            if about:
               index['about'] = about
            with open(info / 'index.json', 'w') as f:
              json.dump(index, f, indent=4)
            
            if component_info:
                # Package is a component, run make to install its files
                env = os.environ.copy()
                env['BRAINVISA_INSTALL_PREFIX'] = str(tmp)
                subprocess.check_call(['make', f'install-{package}'],
                                      env=env, cwd=env['CASA_BUILD'])
                # Do not install doc until doc generation works with Conda
                # subprocess.check_call(['make', f'install-{package}-doc'],
                #                       env=env, cwd=env['CASA_BUILD'])


            # List all files in temporary directory
            with open(info / 'files', 'w') as f:
                for base in tmp.iterdir():
                  if base.name == 'info':
                      continue
                  stack = [base]
                  while stack:
                      item = stack.pop()
                      if item.is_dir():
                          stack.extend(item.iterdir())
                      else:
                          print(str(item.relative_to(tmp)), file=f)
            
            # Copy the content of tmp directory in archive
            for base in tmp.iterdir():
              tar.add(base, base.name)
    subprocess.check_call(['conda', 'index', str(repository)])


if __name__ == '__main__':
    repository = pathlib.Path(sys.argv[1])
    distro = sys.argv[2]
    distro_version = sys.argv[3]

    conda = os.environ.get('CONDA_PREFIX')
    if not conda:
        print('Variable CONDA_PREFIX is not defined. Is your development environment activated ?', file=sys.stderr)
        sys.exit(1)
    if repository.exists() and next(repository.iterdir(), None):
        # repository exists and is not empty
        print(f'Please delete directory {repository}.', file=sys.stderr)
        sys.exit(1)

    generate_repository(repository, distro, distro_version)
