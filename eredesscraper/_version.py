from os.path import dirname, isdir, join
import os
import re
import subprocess
from pathlib import Path

version_re = re.compile('^Version: (.+)$', re.M)


def get_version():
    # This program is placed into the public domain.

    """
    Gets the current version number.
    If in a git repository, it is the current git tag.
    Otherwise, it is the one contained in the PKG-INFO file.
    To use this script, simply import it in your setup.py file
    and use the results of get_version() as your package version:
        from version import *
        setup(
            ...
            version=get_version(),
            ...
        )
    """

    global version

    # Paths for package structure
    d = Path(dirname(__file__))
    src = d.parent
    root = d.parent

    try:
        pkg = [p for p in src.iterdir() if p.is_dir() and 'egg-info' in p.name]
    except ValueError:
        pkg = None
        pass

    if isdir(join(root, '.git')):
        # Get the version using "git describe".
        cmd = 'git describe --tags --match [0-9]*'.split()
        try:
            version = subprocess.check_output(cmd).decode().strip()
        except subprocess.CalledProcessError:
            print('Unable to get version number from git tags')
            exit(1)

        # PEP 386 compatibility
        if '-' in version:
            version = '.post'.join(version.split('-')[:2])

        # Don't declare a version "dirty" merely because a time stamp has
        # changed. If it is dirty, append a ".dev1" suffix to indicate a
        # development revision after the release.
        with open(os.devnull, 'w') as fd_devnull:
            subprocess.call(['git', 'status'],
                            stdout=fd_devnull, stderr=fd_devnull)

        cmd = 'git diff-index --name-only HEAD'.split()
        try:
            dirty = subprocess.check_output(cmd).decode().strip()
        except subprocess.CalledProcessError:
            print('Unable to get git index status')
            exit(1)

        if dirty != '':
            version += '.dev1'

    elif pkg:
        try:
            # Extract the version from the PKG-INFO file.
            with open(join(pkg[0], 'PKG-INFO')) as f:
                version = version_re.search(f.read()).group(1)
        except (IOError, AttributeError):
            print('Unable to find version number in PKG-INFO file')
            exit(1)

    # Fallback to a hard-coded version number of installed package
    else:
        output = subprocess.check_output(['pip', 'show', 'eredesscraper'])
        for elem in output.decode("utf-8").replace("\r", "").split("\n"):
            if "version" in elem.lower():
                version = elem.split(":")[-1].strip()
                break
    return version


if __name__ == '__main__':
    print(get_version())