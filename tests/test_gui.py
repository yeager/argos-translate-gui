import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

import threading
import time
import unittest
from unittest.mock import Mock, patch

from argostranslategui import gui


class Language:
    def __init__(self, code):
        self.code = self.name = code
        self.get_translation = Mock(return_value=None)


class GUIRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = gui.QApplication.instance() or gui.QApplication([])

    def setUp(self):
        self.languages = [Language('en'), Language('fr'), Language('de')]
        self.loader = patch.object(gui.translate, 'load_installed_languages',
                                   side_effect=lambda: self.languages)
        self.loader.start()
        self.window = gui.GUIWindow()

    def tearDown(self):
        self.window.close()
        self.window.deleteLater()
        self.app.processEvents()
        self.loader.stop()

    def test_refresh_shrinking_languages_is_atomic(self):
        self.window.right_language_combo.setCurrentIndex(2)
        self.languages = self.languages[:1]
        with patch.object(self.window, 'translate', wraps=self.window.translate) as run:
            self.window.load_languages()
            self.assertEqual(run.call_count, 1)
        self.assertEqual(self.window.right_language_combo.currentIndex(), 0)

    def test_refresh_preserves_language_codes(self):
        self.window.left_language_combo.setCurrentIndex(2)
        self.languages.reverse()
        self.window.load_languages()
        self.assertEqual(self.window.left_language_combo.currentData(), 'de')
        self.assertEqual(self.window.right_language_combo.currentData(), 'fr')

    def test_invalid_selection_does_not_translate(self):
        self.window.left_language_combo.setCurrentIndex(-1)
        for language in self.languages:
            language.get_translation.reset_mock()
        self.window.translate()
        for language in self.languages:
            language.get_translation.assert_not_called()

    def wait_until(self, predicate):
        deadline = time.monotonic() + 3
        while not predicate() and time.monotonic() < deadline:
            self.app.processEvents()
            time.sleep(.005)
        self.assertTrue(predicate())

    def test_removal_discards_running_and_queued_results(self):
        self.check_obsolete_translation(remove_languages=True)

    def test_unsupported_pair_discards_running_and_queued_results(self):
        self.check_obsolete_translation(remove_languages=False)

    def check_obsolete_translation(self, remove_languages):
        release = threading.Event()
        started = threading.Event()
        calls = []

        def translate(text):
            calls.append(text)
            started.set()
            release.wait(3)
            return 'obsolete result'

        self.languages[0].get_translation.return_value = Mock(translate=translate)
        self.window.left_textEdit.setPlainText('first')
        try:
            self.assertTrue(started.wait(3))
            self.window.left_textEdit.setPlainText('second')
            self.assertIsNotNone(self.window.queued_translation)
            if remove_languages:
                self.languages = []
                self.window.load_languages()
            else:
                self.languages[0].get_translation.return_value = None
                self.window.translate()
            self.assertIsNone(self.window.queued_translation)
        finally:
            release.set()
            self.wait_until(lambda: self.window.worker_thread is None)
        self.assertEqual(calls, ['first'])
        self.assertEqual(self.window.right_textEdit.toPlainText(), '')

    def test_latest_translation_replaces_pending_work(self):
        release = threading.Event()
        started = threading.Event()
        calls = []

        def translate(text):
            calls.append(text)
            started.set()
            release.wait(3)
            return text.upper()

        self.languages[0].get_translation.return_value = Mock(translate=translate)
        self.window.left_textEdit.setPlainText('first')
        try:
            self.assertTrue(started.wait(3))
            self.window.left_textEdit.setPlainText('second')
            self.window.left_textEdit.setPlainText('latest')
        finally:
            release.set()
            self.wait_until(lambda: self.window.worker_thread is None)
        self.assertEqual(calls, ['first', 'latest'])
        self.assertEqual(self.window.right_textEdit.toPlainText(), 'LATEST')

    def test_failed_download_can_retry_and_succeed(self):
        operation = Mock(side_effect=[OSError('network unavailable'), None])
        button = gui.WorkerStatusButton('Download', operation)
        button.click()
        self.assertFalse(button.isEnabled())
        self.wait_until(lambda: button.status != button.Status.RUNNING)
        self.assertEqual(button.status, button.Status.FAILED)
        self.assertEqual(gui.QPushButton.text(button), 'Retry')
        self.assertIn('network unavailable', button.toolTip())
        self.assertTrue(button.isEnabled())
        button.click()
        self.wait_until(lambda: button.status != button.Status.RUNNING)
        self.assertEqual(button.status, button.Status.DONE)
        self.assertEqual(gui.QPushButton.text(button), '✓')
        self.assertEqual(operation.call_count, 2)
        button.deleteLater()

    def test_translation_failure_is_visible_and_recoverable(self):
        operation = Mock(side_effect=[RuntimeError('model failed'), 'recovered'])
        self.languages[0].get_translation.return_value = Mock(translate=operation)
        self.window.left_textEdit.setPlainText('first')
        self.wait_until(lambda: self.window.worker_thread is None)
        self.assertEqual(self.window.right_textEdit.toPlainText(),
                         'Translation failed: model failed')
        self.window.left_textEdit.setPlainText('retry')
        self.wait_until(lambda: self.window.worker_thread is None)
        self.assertEqual(self.window.right_textEdit.toPlainText(), 'recovered')

    def test_obsolete_translation_failure_does_not_overwrite_output(self):
        release = threading.Event()
        started = threading.Event()

        def translate(text):
            if text == 'first':
                started.set()
                release.wait(3)
                raise RuntimeError('obsolete failure')
            return 'latest result'

        self.languages[0].get_translation.return_value = Mock(translate=translate)
        self.window.left_textEdit.setPlainText('first')
        try:
            self.assertTrue(started.wait(3))
            self.window.left_textEdit.setPlainText('latest')
        finally:
            release.set()
            self.wait_until(lambda: self.window.worker_thread is None)
        self.assertEqual(self.window.right_textEdit.toPlainText(), 'latest result')

    def test_uninstall_emits_one_change_after_refresh(self):
        table = gui.PackagesTable.__new__(gui.PackagesTable)
        with patch.object(gui.package, 'get_installed_packages', return_value=[]):
            table.__init__(gui.PackagesTable.TableContent.INSTALLED, [])
        changed = Mock()
        table.packages_changed.connect(changed)
        with patch.object(gui.package, 'uninstall'), patch.object(table, 'populate') as populate:
            table.uninstall_package(object())
            populate.assert_called_once()
        changed.assert_called_once()
        table.deleteLater()


if __name__ == '__main__':
    unittest.main()
