import tempfile
import unittest
import logging
from tea.logger import configure_logging


DATE = r"\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2}.\d{3}"


class TestLogger(unittest.TestCase):
    def setUp(self):
        self.output_filename = tempfile.mktemp()
        configure_logging(self.output_filename, level=logging.DEBUG)
        self.logger = logging.getLogger(__name__)
        self.output_test_file = open(self.output_filename)

    def tearDown(self):
        self.output_test_file.close()
        # TODO: You cannot delete open file on windows, and the file
        # remains open
        # because the logging is holding it.
        # os.remove(self.output_filename)

    def test_debug(self):
        self.logger.debug("Debug message #01")
        regexp = DATE + r"\s+ DEBUG: Debug message #01 \[[\w\.]+:\d{2,3}\]"
        self.assertRegex(self.output_test_file.readline(), regexp)

    def test_info(self):
        self.logger.info("Info message #02")
        regexp = DATE + r"\s+ INFO: Info message #02 \[[\w\.]+:\d{2,3}\]"
        self.assertRegex(self.output_test_file.readline(), regexp)

    def test_warning(self):
        self.logger.warning("Warning message #03")
        regexp = DATE + r"\s+ WARNING: Warning message #03 \[[\w\.]+:\d{2,3}\]"
        self.assertRegex(self.output_test_file.readline(), regexp)

    def test_error(self):
        self.logger.error("Error message #04")
        regexp = DATE + r"\s+ ERROR: Error message #04 \[[\w\.]+:\d{2,3}\]"
        self.assertRegex(self.output_test_file.readline(), regexp)

    def test_critical(self):
        self.logger.critical("Critical message #06")
        regexp = (
            DATE + r"\s+ CRITICAL: Critical message #06 \[[\w\.]+:\d{2,3}\]"
        )
        self.assertRegex(self.output_test_file.readline(), regexp)

    def test_exception(self):
        try:
            raise Exception("Error")
        except Exception:
            self.logger.exception("Exception #08")
        regexp = DATE + r"\s+ ERROR: Exception #08 \[[\w\.]+:\d{2,3}\]"
        self.assertRegex(self.output_test_file.readline(), regexp)
        traceback = self.output_test_file.read().strip()
        self.assertTrue(
            traceback.startswith("Traceback (most recent call last):")
        )
        self.assertTrue(traceback.endswith("Exception: Error"))
