import json
from types import SimpleNamespace

from navix.diagnostics import Diagnostics


def test_diagnostic_export_has_no_keys_or_page_data(tmp_path):
    recorder = Diagnostics(tmp_path)
    recorder.record('mcp', 'start', code='LOCAL_READY')
    session = SimpleNamespace(status=lambda: {
        'active': True, 'permissions': ['browser'], 'remaining_seconds': 120,
    })
    service = SimpleNamespace(ready=True, port=3180)
    tunnel = SimpleNamespace(process=None, check=lambda: 'executando')
    report = recorder.report(session, service, tunnel)
    text = json.dumps(report)
    assert report['server_ready']
    assert report['secrets_included'] is False
    assert report['events'][0]['code'] == 'LOCAL_READY'
    assert 'Authorization' not in text
    assert 'CONTROL_PLANE_API_KEY' not in text
