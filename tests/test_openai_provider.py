import json,unittest
from unittest.mock import patch
from aegis_core.openai_provider import OpenAIAdvisorProvider
from aegis_core.advisor import Advisor
from aegis_core.guardian import Finding
class FakeResponse:
    def __enter__(self):return self
    def __exit__(self,*_):return False
    def read(self,*_):return b''
def fake_urlopen(request,timeout=20):
    assert request.full_url=="https://api.openai.com/v1/responses"
    assert request.get_header("Authorization")=="Bearer fake-test-key"
    class R(FakeResponse):
        pass
    import io
    body=json.dumps({"output":[{"content":[{"type":"output_text","text":json.dumps({"recommendation":"Review anomaly","risk":"low"})}]}]})
    return io.BytesIO(body.encode())
class ProviderTests(unittest.TestCase):
    def test_no_secret(self):
        with patch.dict("os.environ",{},clear=True):
            with self.assertRaises(ValueError):OpenAIAdvisorProvider()
    def test_mocked_external_api(self):
        with patch("urllib.request.urlopen",side_effect=fake_urlopen):
            provider=OpenAIAdvisorProvider("fake-test-key")
            result=Advisor(provider).assess([Finding("high","blocked","danger","system")])
            self.assertEqual(result.risk,"high")
            self.assertTrue(result.requires_human_review)
            self.assertEqual(result.recommendation,"Review anomaly")
