__author__    = 'Viktor Kerkez <alefnula@gmail.com>'
__date__      = '01 January 2009'
__copyright__ = 'Copyright (c) 2009 Viktor Kerkez'

import os
import sys
import glob

from tea import shutil
from tea.logger import * #@UnusedWildImport
from tea.utils import compress
from tea.process import execute_and_report as er


def setup(module, output_type='egg'):
    if output_type == 'egg':
        result = er('setup.py', 'install', '--no-compile',
                    '--install-lib', os.path.join('INSTALL'))
        if result:
            result = compress.mkzip('%s.egg' % module, glob.glob('INSTALL/*')) 
    elif output_type == 'exe':
        result = er('setup.py', 'install', '--no-compile',
                    '--install-lib', os.path.join('INSTALL', 'lib', 'python'),
                    '--install-scripts', os.path.join('INSTALL', 'scripts'))
        if result:
            archiver = '7z'
            for pf in ('ProgramFiles', 'ProgramFiles(x86)', 'ProgramW6432'):
                executable = os.path.join(os.environ.get(pf, ''), '7-Zip', '7z.exe')
                if os.path.exists(executable):
                    archiver = executable
            os.chdir('INSTALL')
            modules = filter(os.path.exists, ['lib', 'scripts'])
            result = er(archiver, 'a', '-sfx', '../%s.exe' % module, *modules)
            os.chdir('..')
    # Cleanup
    if os.path.isdir('INSTALL'): shutil.remove('INSTALL')
    if os.path.isdir('build'):   shutil.remove('build')
    return result



def _usage(self):
    print '''
Usage: python -m tea.utils.setup MODULE_NAME [TYPE]

MODULE_NAME: Name of the output file with appropriate extension
TYPE:        Type of the generated output
             Available types:
                - exe: Self extracting executable
                - egg: Importable python egg [default]
'''
    return 1


def main(args):
    l = len(args)
    if l == 0:
        return _usage()
    elif l == 1:
        module      = args[0]
        output_type = 'egg'
    elif l == 2:
        module      = args[0]
        output_type = args[0].lower()
        if output_type not in ('exe', 'egg'):
            return _usage()
    else:
        return _usage()
    if setup(module, output_type):
        output_path = os.environ.get('OutputPath', None)
        if output_path:
            name = '%s.%s' % (module, output_type)
            outfile = os.path.join(output_path, name)
            if os.path.isfile(outfile):
                shutil.remove(outfile)
            if not shutil.move(name, outfile):
                return 1
        return 0
    return 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
