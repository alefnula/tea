__author__    = 'Viktor Kerkez <alefnula@gmail.com>'
__date__      = '20 October 2010'
__copyright__ = 'Copyright (c) 2010 Viktor Kerkez'

import os
import glob
from distutils.core import setup

setup(name='tea',
      version='0.0.1',
      description='tea python library',
      long_description='Set of usefull commonly used python modules.',
      platforms=['Windows', 'POSIX', 'MacOS'],
      author='Viktor Kerkez',
      author_email='alefnula@gmail.com',
      maintainer='Viktor Kerkez',
      maintainer_email='alefnula@gmail.com',
      url='https://bitbucket.org/alefnula/tea',
      license='GPLv3',
      packages=[
          'tea',
          'tea.commander',
          'tea.console',
          'tea.logger',
          'tea.process',
          'tea.scm',
          'tea.shutil',
          'tea.system',
          'tea.utils',
      ],
      package_dir={'' : 'src'},
      scripts=[
      ],
)
