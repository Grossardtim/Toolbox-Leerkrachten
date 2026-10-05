import unittest
from unittest.mock import Mock, patch
from tools import start_local


class LocalStartupTests(unittest.TestCase):
    @patch('tools.start_local.webbrowser.open', return_value=True)
    @patch('tools.start_local.subprocess.Popen')
    @patch('tools.start_local.portal_ready', return_value=True)
    @patch('tools.start_local.port_in_use', return_value=True)
    def test_existing_portal_opens_without_duplicate_server(self, busy, ready, process, browser):
        with patch('sys.argv', ['start_local.py']):
            self.assertEqual(start_local.main(), 0)
        process.assert_not_called()
        browser.assert_called_once_with('http://127.0.0.1:8000/')

    @patch('tools.start_local.webbrowser.open')
    @patch('tools.start_local.subprocess.Popen')
    @patch('tools.start_local.portal_ready', return_value=False)
    @patch('tools.start_local.port_in_use', return_value=True)
    def test_unrelated_port_is_not_opened_or_killed(self, busy, ready, process, browser):
        with patch('sys.argv', ['start_local.py']):
            self.assertEqual(start_local.main(), 1)
        process.assert_not_called()
        browser.assert_not_called()

    @patch('tools.start_local.webbrowser.open', return_value=True)
    @patch('tools.start_local.portal_ready', side_effect=[False, True])
    @patch('tools.start_local.port_in_use', return_value=False)
    @patch('tools.start_local.time.sleep')
    def test_browser_opens_only_after_ready(self, sleep, busy, ready, browser):
        process = Mock()
        process.poll.side_effect = [None, None, 0]
        process.wait.return_value = 0
        with patch('sys.argv', ['start_local.py']), patch('tools.start_local.subprocess.Popen', return_value=process):
            self.assertEqual(start_local.main(), 0)
        self.assertEqual(ready.call_count, 2)
        browser.assert_called_once_with('http://127.0.0.1:8000/')
        process.terminate.assert_not_called()
