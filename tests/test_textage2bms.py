import io
import sys
import types
import unittest
from contextlib import redirect_stdout
from unittest.mock import MagicMock, patch

# Stub optional runtime dependencies so tests can run without browser libs.
selenium = types.ModuleType('selenium')
webdriver_mod = types.ModuleType('selenium.webdriver')
chrome_mod = types.ModuleType('selenium.webdriver.chrome')
chrome_options_mod = types.ModuleType('selenium.webdriver.chrome.options')
firefox_mod = types.ModuleType('selenium.webdriver.firefox')
firefox_options_mod = types.ModuleType('selenium.webdriver.firefox.options')
pyquery_mod = types.ModuleType('pyquery')


class DummyOptions:
    def add_argument(self, _arg):
        pass


chrome_options_mod.Options = DummyOptions
firefox_options_mod.Options = DummyOptions
webdriver_mod.Chrome = lambda *args, **kwargs: None
webdriver_mod.Firefox = lambda *args, **kwargs: None
selenium.webdriver = webdriver_mod
pyquery_mod.PyQuery = lambda *args, **kwargs: None

sys.modules.setdefault('selenium', selenium)
sys.modules.setdefault('selenium.webdriver', webdriver_mod)
sys.modules.setdefault('selenium.webdriver.chrome', chrome_mod)
sys.modules.setdefault('selenium.webdriver.chrome.options', chrome_options_mod)
sys.modules.setdefault('selenium.webdriver.firefox', firefox_mod)
sys.modules.setdefault('selenium.webdriver.firefox.options', firefox_options_mod)
sys.modules.setdefault('pyquery', pyquery_mod)

import textage2bms


class TestTextage2Bms(unittest.TestCase):
    def test_build_headers_reads_expected_scripts(self):
        driver = MagicMock()
        values = {
            'return genre': 'GENRE',
            'return title': 'TITLE',
            'return artist': 'ARTIST',
            'return bpm': '150',
        }
        driver.execute_script.side_effect = lambda script: values[script]

        headers = textage2bms.build_headers(driver)

        self.assertEqual(headers['#GENRE'], 'GENRE')
        self.assertEqual(headers['#TITLE'], 'TITLE')
        self.assertEqual(headers['#ARTIST'], 'ARTIST')
        self.assertEqual(headers['#BPM'], '150')
        self.assertEqual(headers['#WAV02'], 'out.wav')
        self.assertEqual(driver.execute_script.call_count, 4)

    def test_print_main_data_field_skips_empty_channels(self):
        sections = [
            [1, {
                '11': [False, True],
                '12': [False, False],
                '02': 0.5,
            }]
        ]

        buf = io.StringIO()
        with redirect_stdout(buf):
            textage2bms.print_main_data_field(sections)

        out = buf.getvalue()
        self.assertIn('#00111:00AA', out)
        self.assertIn('#00102:0.5', out)
        self.assertNotIn('#00112:', out)

    def test_main_runs_pipeline_and_quits_driver(self):
        driver = MagicMock()
        driver.page_source = '<html></html>'

        with patch.object(textage2bms, 'argv', ['textage2bms.py', 'https://example.com']), \
             patch.object(textage2bms, 'get_driver', return_value=driver), \
             patch.object(textage2bms, 'pq', return_value='DOC') as pq_mock, \
             patch.object(textage2bms, 'build_headers', return_value={'#TITLE': 'T'}) as build_headers_mock, \
             patch.object(textage2bms, 'get_sections', return_value=[[1, {}]]) as get_sections_mock, \
             patch.object(textage2bms, 'print_header_field') as print_header_field_mock, \
             patch.object(textage2bms, 'print_main_data_field') as print_main_data_field_mock:
            textage2bms.main()

        driver.get.assert_called_once_with('https://example.com')
        pq_mock.assert_called_once_with('<html></html>')
        build_headers_mock.assert_called_once_with(driver)
        get_sections_mock.assert_called_once_with('DOC')
        print_header_field_mock.assert_called_once_with({'#TITLE': 'T'})
        print_main_data_field_mock.assert_called_once_with([[1, {}]])
        driver.quit.assert_called_once()

    def test_main_quits_driver_on_error(self):
        driver = MagicMock()
        driver.page_source = '<html></html>'

        with patch.object(textage2bms, 'argv', ['textage2bms.py', 'https://example.com']), \
             patch.object(textage2bms, 'get_driver', return_value=driver), \
             patch.object(textage2bms, 'pq', return_value='DOC'), \
             patch.object(textage2bms, 'build_headers', return_value={'#TITLE': 'T'}), \
             patch.object(textage2bms, 'get_sections', return_value=[[1, {}]]), \
             patch.object(textage2bms, 'print_header_field', side_effect=RuntimeError('boom')):
            with self.assertRaises(RuntimeError):
                textage2bms.main()

        driver.quit.assert_called_once()

    def test_main_requires_url_argument(self):
        with patch.object(textage2bms, 'argv', ['textage2bms.py']):
            with self.assertRaises(SystemExit):
                textage2bms.main()


if __name__ == '__main__':
    unittest.main()
