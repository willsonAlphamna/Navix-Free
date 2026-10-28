import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from navix.cloud import CloudSettings
from navix.cloud_pair import (DeviceIdentity, DeviceIdentityStore,
                              PairingHttpClient, _NoRedirect)


class FakeResponse:
    def __init__(self, payload):
        self.content=io.BytesIO(json.dumps(payload).encode('utf-8'))
    def __enter__(self):return self
    def __exit__(self, *args):pass
    def read(self, size):return self.content.read(size)


class FakeOpener:
    def __init__(self):
        self.requests=[]
    def open(self, request, timeout):
        self.requests.append((request,timeout))
        if '/api/pair/state' in request.full_url:
            return FakeResponse({'linked':True})
        body=json.loads(request.data)
        return FakeResponse({'deviceId':body['device_id'],'expiresAt':123456789})


class CloudPairTests(unittest.TestCase):
    def setUp(self):
        self.settings=CloudSettings(enabled=True,relay_url='wss://navixx.example/api/device/connect')
        self.identity=DeviceIdentity('device_abcdefgh1234','A'*43)
        self.opener=FakeOpener()

    def test_windows_dpapi_identity_roundtrip(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch('navix.tunnel_manager._dpapi', side_effect=lambda data, protect:data):
                store=DeviceIdentityStore(directory)
                first=store.ensure()
                self.assertEqual(store.load(),first)
                self.assertEqual(store.ensure(),first)
                self.assertNotIn(first.agent_secret, str(store.path))

    def test_rejects_invalid_identity(self):
        with self.assertRaises(ValueError):
            DeviceIdentity('short','a'*43).validate()
        with self.assertRaises(ValueError):
            DeviceIdentity('device_abcdefgh1234','123').validate()

    def test_starts_with_short_code_and_no_openai_key(self):
        client=PairingHttpClient(self.settings,self.opener)
        result=client.begin(self.identity)
        self.assertEqual(len(result['verification_code']),6)
        self.assertTrue(result['verification_code'].isdigit())
        req,timeout=self.opener.requests[0]
        self.assertEqual(timeout,12)
        self.assertTrue(req.full_url.startswith('https://navixx.example/api/pair/start'))
        body=json.loads(req.data)
        self.assertEqual(body['agent_secret'],self.identity.agent_secret)
        self.assertEqual(req.get_header('User-agent'),'NavixX-Desktop-Cloud/0.3.0')
        self.assertNotIn('Authorization',req.headers)
        self.assertNotIn(self.identity.agent_secret,req.full_url)

    def test_status_uses_private_header(self):
        client=PairingHttpClient(self.settings,self.opener)
        self.assertTrue(client.status(self.identity))
        req,_=self.opener.requests[0]
        self.assertEqual(req.get_header('X-navix-agent-token'),self.identity.agent_secret)
        self.assertNotIn(self.identity.agent_secret,req.full_url)

    def test_renew_uses_existing_device_secret_without_openai_api_key(self):
        client=PairingHttpClient(self.settings,self.opener)
        result=client.renew(self.identity)
        self.assertEqual(result['device_id'],self.identity.device_id)
        self.assertEqual(len(result['verification_code']),6)
        req,_=self.opener.requests[0]
        self.assertTrue(req.full_url.endswith('/api/pair/renew'))
        self.assertEqual(req.get_header('X-navix-agent-token'),self.identity.agent_secret)
        self.assertNotIn('Authorization',req.headers)

    def test_rejects_disabled_or_http_endpoints(self):
        for settings in (CloudSettings(),CloudSettings(enabled=True,relay_url='ws://insecure.example')):
            with self.assertRaises(ValueError):
                PairingHttpClient(settings,self.opener)

    def test_no_redirects_with_secret(self):
        with self.assertRaises(ValueError):
            _NoRedirect().redirect_request(None,None,302,'Moved',{},'https://other.example')

    def test_server_result_must_match_local_identity(self):
        class WrongOpener(FakeOpener):
            def open(self,request,timeout):
                return FakeResponse({'deviceId':'other_device','expiresAt':123})
        with self.assertRaises(RuntimeError):
            PairingHttpClient(self.settings,WrongOpener()).begin(self.identity)


if __name__ == '__main__':
    unittest.main()
