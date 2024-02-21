import os
import pathlib
import shutil
import subprocess
import sys

def extract_mesalib(dest_dir):
    dest_dir = pathlib.Path(dest_dir)
    subprocess.check_call(['mamba', 'install', 'mesalib', '-y'])
    try:
        conda = pathlib.Path(os.environ['CONDA_PREFIX'])
        files = sorted((conda / "pkgs").glob("mesalib-*/info/files"))[-1]
        with open(files) as f:
            for line in f:
                file = line.strip()
                src = conda / file
                dest = dest_dir / file
                print(dest, flush=True)
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dest)
    finally:
        subprocess.check_call(['mamba', 'uninstall', 'mesalib', '-y'])

if __name__ == '__main__':
    extract_mesalib(sys.argv[1])
