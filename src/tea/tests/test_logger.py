__author__    = 'Viktor Kerkez <viktor.kerkez@gmail.com>'
__date__      = '20 January 2010'
__copyright__ = 'Copyright (c) 2009 Viktor Kerkez'

import re
import tempfile
import unittest
import logging
from tea.logger import configure_logging


DATE = r'\d{4}.\d{2}.\d{2} \d{2}:\d{2}:\d{2}.\d{3}'


class TestLogger(unittest.TestCase):
    def setUp(self):
        self.output_filename = tempfile.mktemp()
        configure_logging(self.output_filename, level='VERBOSE')
        self.logger = logging.getLogger(__name__)
        self.output_test_file = file(self.output_filename)
    
    def tearDown(self):
        self.output_test_file.close()
        # FIXME: You cannot delete open file on windows, and the file remains open
        # because the logging is holding it.
        #os.remove(self.output_filename)
    
    def test_debug(self):
        self.logger.debug('Debug message #01')
        regexp = DATE + r'\s+ DEBUG: Debug message #01 \[[\w\.]+:\d{2,3}\]'
        #print self.output_test_file.readline()
        self.assert_(re.match(regexp, self.output_test_file.readline()))

    def test_info(self):
        self.logger.info('Info message #02')
        regexp = DATE + r'\s+ INFO: Info message #02 \[[\w\.]+:\d{2,3}\]' 
        self.assert_(re.match(regexp, self.output_test_file.readline()))

    def test_warning(self):
        self.logger.warning('Warning message #03')
        regexp = DATE + r'\s+ WARNING: Warning message #03 \[[\w\.]+:\d{2,3}\]'
        self.assert_(re.match(regexp, self.output_test_file.readline()))

    def test_error(self):
        self.logger.error('Error message #04')
        regexp = DATE + r'\s+ ERROR: Error message #04 \[[\w\.]+:\d{2,3}\]'
        self.assert_(re.match(regexp, self.output_test_file.readline()))

    def test_fatal(self):
        self.logger.fatal('Fatal message #06')
        regexp = DATE + r'\s+ ERROR_FATAL: Fatal message #06 \[[\w\.]+:\d{2,3}\]'
        self.assert_(re.match(regexp, self.output_test_file.readline()))
        
    def test_verbose(self):
        self.logger.verbose('Verbose message #07')
        regexp = DATE + r'\s+ VERBOSE: Verbose message #07 \[[\w\.]+:\d{2,3}\]'
        self.assert_(re.match(regexp, self.output_test_file.readline()))
    
    def test_exception(self):
        self.logger.exception('Exception #08')
        regexp = DATE + r'\s+ ERROR: Exception #08 \[[\w\.]+:\d{2,3}\]'
        self.assert_(re.match(regexp, self.output_test_file.readline()))  
        self.assertEqual(self.output_test_file.readline(), 'None\n')
