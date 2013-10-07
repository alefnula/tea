__author__ = 'Viktor Kerkez <alefnula@gmail.com>'
__date__ = '20 October 2010'
__copyright__ = 'Copyright (c) 2010 Viktor Kerkez'

import io
from distutils.core import setup

setup(
    name='tea',
    version='0.0.5',
    description='Set of utility python modules.',
    long_description=io.open('README.rst', 'r', encoding='utf-8').read(),
    platforms=['Windows', 'POSIX', 'MacOSX'],
    author='Viktor Kerkez',
    author_email='alefnula@gmail.com',
    maintainer='Viktor Kerkez',
    maintainer_email='alefnula@gmail.com',
    url='https://github.com/alefnula/tea',
    license='BSD',
    packages=[
        'tea',
        'tea.commander',
        'tea.console',
        'tea.cron',
        'tea.ds',
        'tea.logger',
        'tea.msg',
        'tea.parsing',
        'tea.process',
        'tea.scm',
        'tea.shutil',
        'tea.system',
        'tea.tests',
        'tea.tornado',
        'tea.utils',
    ],
    package_dir={'': 'src'},
    scripts=[
    ]
)
