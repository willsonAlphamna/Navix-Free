import unittest
from unittest.mock import patch

from navix.cloud_controller import CloudController
from navix.cloud_pair import DeviceIdentity


class FakeSession:
    def __init__(self, active=True):
        self.active=active
    def status(self):
        return {'active':self.active}


class FakeService:
    def __init__(self):
        self.port=1750
        self.ready=True


class CloudControllerTests(unittest.TestCase):
    def setUp(self):
        self.session=FakeSession()
        self.service=FakeService()
        self.messages=[]
        self.controller=CloudController('unused',self.session,self.service,
            'wss://navixx.example/api/device/connect',
            on_status=self.messages.append)
        self.identity=DeviceIdentity('device_1234567890','a'*43)

    def test_new_local_port_is_used_without_repairing_device_identity(self):
        self.assertEqual(self.controller.port,1750)
        self.service.port=40645
        self.assertEqual(self.controller.port,40645)
        self.assertTrue(self.controller.ready)

    def test_unpaired_device_reports_actionable_state(self):
        with patch.object(self.controller.identity_store,'load',return_value=None):
            with self.assertRaises(PermissionError):
                self.controller.start()
        state=self.controller.status()
        self.assertEqual(state['state'],'unpaired')
        self.assertIn('Vincular',state['message'])

    def test_expired_local_session_never_starts_cloud(self):
        self.session.active=False
        with self.assertRaises(PermissionError):
            self.controller.start()
        self.assertEqual(self.controller.status()['state'],'local_expired')

    def test_server_not_ready_reports_local_starting(self):
        self.service.ready=False
        with self.assertRaises(PermissionError):
            self.controller.start()
        self.assertEqual(self.controller.status()['state'],'local_starting')

    def test_network_failure_has_no_secret_or_traceback(self):
        with patch.object(self.controller.identity_store,'load',return_value=self.identity), \
             patch('navix.cloud_controller.PairingHttpClient.status',
                   side_effect=OSError('secret=do-not-display')):
            with self.assertRaises(ConnectionError):
                self.controller.start()
        self.assertEqual(self.controller.status()['state'],'network_error')
        self.assertNotIn('do-not-display',self.controller.status()['message'])

    def test_stop_does_not_keep_connection_authorized(self):
        self.controller.stop()
        self.assertEqual(self.controller.status()['state'],'stopped')
        self.session.active=False
        with self.assertRaises(PermissionError):
            self.controller.start()


if __name__=='__main__':
    unittest.main()
