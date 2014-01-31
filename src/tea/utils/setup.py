from __future__ import print_function

__author__ = 'Viktor Kerkez <alefnula@gmail.com>'
__date__ = '01 January 2009'
__copyright__ = 'Copyright (c) 2009 Viktor Kerkez'

import os
import sys
import glob
import optparse

from tea import shell
from tea.utils import compress
from tea.process import execute_and_report as er


def setup(module, target='zip', output_path=None, data_dir=None):
    dist = os.path.abspath('dist')
    try:
        if target == 'zip':
            assert er('setup.py', 'install', '--no-compile',
                      '--install-lib',     os.path.join(dist, 'lib'),
                      '--install-scripts', os.path.join(dist),
                      *(['--install-data',    os.path.join(dist, data_dir)]
                        if data_dir is not None else []))
            with shell.goto(dist) as ok:
                assert ok
                assert compress.mkzip('%s.zip' % module,
                                      glob.glob(os.path.join('lib', '*')))
                assert shell.remove('lib')
        elif target == 'exe':
            assert er('setup.py', 'install', '--no-compile',
                      '--install-lib',     os.path.join(dist, 'lib', 'python'),
                      '--install-scripts', os.path.join(dist, 'scripts'),
                      *(['--install-data',    os.path.join(dist, data_dir)]
                        if data_dir is not None else []))
            with shell.goto(dist) as ok:
                assert ok

                modules = list(filter(os.path.exists,
                                      ['lib', 'scripts'] + (
                                          [data_dir] if data_dir is not None
                                          else [])))
                assert compress.seven_zip('%s.exe' % module, modules,
                                          self_extracting=True)
                # Cleanup
                for module in modules:
                    assert shell.remove(module)
        if output_path is not None:
            output_path = os.path.abspath(output_path)
            if output_path != dist:
                if not os.path.isdir(output_path):
                    assert shell.mkdir(output_path)
                for filename in shell.search(dist, '*'):
                    output = os.path.join(output_path,
                                          filename.replace(dist, '', 1)
                                                  .strip('\\/'))
                    assert shell.move(filename, output)
        return 0
    except AssertionError as e:
        print(e)
        return 1
    finally:
        # Cleanup
        if output_path != dist:
            shell.remove(dist)
        if os.path.isdir('build'):
            shell.remove('build')


def create_parser():
    parser = optparse.OptionParser(
        usage='python -m tea.utils.setup [options] MODULE_NAME')
    parser.add_option('-e', '--zip', action='store_const', dest='target',
                      const='zip', help='build egg file and scripts',
                      default='zip')
    parser.add_option('-x', '--exe', action='store_const', dest='target',
                      const='exe', help='build self extracting executable',
                      default='zip')
    parser.add_option('-o', '--output-path', action='store', type='string',
                      dest='output_path', help='destination directory',
                      default=None)
    parser.add_option('-d', '--data-dir', action='store', type='string',
                      dest='data_dir', help='data dir relative path',
                      default=None)
    return parser


def main(args):
    parser = create_parser()
    options, args = parser.parse_args(args)
    if len(args) != 1:
        parser.print_help()
        return 1
    else:
        module = args[0]
        return setup(module, options.target, options.output_path,
                     options.data_dir)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
