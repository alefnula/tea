__author__ = 'Viktor Kerkez <alefnula@gmail.com>'
__date__ = '20 October 2010'
__copyright__ = 'Copyright (c) 2010 Viktor Kerkez'

import io
import os
from setuptools import setup, find_packages


# If version file exists, this happens during the installation phase,
# read the version from the version file.
# If the version file does not exist, this is during the build phase,
# read the version from TRAVIS_TAG and create a version file for packaging.
VERSION_FILE = 'VERSION'
if os.path.isfile(VERSION_FILE):
    with io.open(VERSION_FILE, 'r', encoding='utf-8') as f:
        version = f.read()
else:
    version = os.environ.get('TRAVIS_TAG', '0.0.0')
    with io.open(VERSION_FILE, 'w', encoding='utf-8') as f:
        f.write(version)


setup(
    name='tea',
    version=version,
    description='Set of utility python modules.',
    long_description=io.open('README.rst', 'r', encoding='utf-8').read(),
    platforms=['Windows', 'POSIX', 'MacOSX'],
    author='Viktor Kerkez',
    author_email='alefnula@gmail.com',
    maintainer='Viktor Kerkez',
    maintainer_email='alefnula@gmail.com',
    url='https://github.com/alefnula/tea',
    license='BSD',
    packages=find_packages(),
    install_requires=io.open('requirements.txt').read().splitlines(),
    scripts=[],
)
