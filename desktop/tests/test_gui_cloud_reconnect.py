"""Cloud GUI wiring without opening a real Windows window."""
import unittest
from unittest.mock import MagicMock, patch

try:
    from navix.gui import Panel
except ModuleNotFoundError as error:
    if error.name not in ('mcp', 'playwright', 'pyautogui', 'PIL'):
        raise
    Panel = None  # Full Windows CI installs these optional GUI dependencies.


class FakeVar:
    def __init__(self, value):
        self.value=value
    def get(self):
        return self.value


@unittest.skipIf(Panel is None, 'GUI dependencies unavailable in minimal test environment')
class CloudGuiTests(unittest.TestCase):
    def panel(self):
        panel=object.__new__(Panel)
        panel.browser_allowed=FakeVar(True)
        panel.desktop_allowed=FakeVar(False)
        panel.files_allowed=FakeVar(False)
        panel.commands_allowed=FakeVar(False)
        panel.duration_minutes=FakeVar('30')
        panel.session=MagicMock()
        panel.session.status.return_value={'active':True}
        panel.service=MagicMock()
        panel.service.ready=True
        panel.cloud_controller=MagicMock()
        panel._request_cloud_start=MagicMock()
        panel.show=MagicMock()
        panel.root=MagicMock()
        panel.language='pt-BR'
        return panel

    def test_connect_starts_local_and_cloud_without_new_pairing(self):
        panel=self.panel()
        Panel.connect(panel)
        panel.session.activate.assert_called_once_with(['browser'],minutes=30)
        panel.service.start.assert_called_once()
        panel._request_cloud_start.assert_called_once_with(manual=False)
        panel.cloud_controller.enroll.assert_not_called()

    def test_repair_checks_cloud_when_local_mcp_is_ready(self):
        panel=self.panel()
        Panel.repair(panel)
        panel._request_cloud_start.assert_called_once_with(manual=True)
        panel.service.close.assert_not_called()

    def test_repair_replaces_stopped_mcp_and_updates_cloud_reference(self):
        panel=self.panel()
        panel.service.ready=False
        panel.service.thread=None
        panel.browser=MagicMock()
        with patch('navix.gui.Service') as service_factory, \
             patch('navix.gui.Desktop'):
            Panel.repair(panel)
        self.assertIs(panel.cloud_controller.service,service_factory.return_value)
        service_factory.return_value.start.assert_called_once()
        panel._request_cloud_start.assert_called_once_with(manual=True)

    def test_pairing_dialog_displays_id_and_code_without_invisible_readonly_entry(self):
        panel=MagicMock()
        panel.COLORS=Panel.COLORS
        panel._cloud_pair_dialog=None
        data={'device_id':'device_1234567890','verification_code':'001234',
              'expires_at':1_900_000_000_000}
        with patch('navix.gui.tk.Toplevel'), patch('navix.gui.tk.Frame'), \
             patch('navix.gui.tk.Label') as label, \
             patch('navix.gui.tk.Entry') as entry, \
             patch('navix.gui.tk.StringVar'):
            Panel._cloud_code_dialog(panel,data)
        labels=[call.kwargs for call in label.call_args_list]
        self.assertTrue(any(item.get('text')==data['device_id'] and
                            item.get('fg')==Panel.COLORS['text'] for item in labels))
        self.assertTrue(any(item.get('text')==data['verification_code'] and
                            item.get('fg')==Panel.COLORS['text'] for item in labels))
        entry.assert_not_called()

    def test_copy_code_confirms_it_was_copied(self):
        panel=self.panel()
        feedback=MagicMock()
        Panel._copy_cloud_value(panel,'001234',feedback)
        panel.root.clipboard_clear.assert_called_once()
        panel.root.clipboard_append.assert_called_once_with('001234')
        self.assertIn('Copiado',feedback.set.call_args.args[0])


if __name__=='__main__':
    unittest.main()
