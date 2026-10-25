import json
import pytest
from navix.core import Session
from navix.browser import validate_url


def test_default_denies(tmp_path):
    session = Session(tmp_path)
    with pytest.raises(PermissionError): session.require('desktop')
    assert not session.status()['active']


def test_individual_token(tmp_path):
    assert Session(tmp_path / 'a').token != Session(tmp_path / 'b').token


def test_expiry(tmp_path):
    now = [0]
    session = Session(tmp_path, clock=lambda: now[0])
    session.activate(['browser'], minutes=1)
    session.require('browser')
    now[0] = 60
    with pytest.raises(PermissionError): session.require('browser')
    assert session.status()['permissions'] == []


def test_permission_isolation(tmp_path):
    session = Session(tmp_path)
    session.activate(['browser'])
    with pytest.raises(PermissionError): session.require('desktop')


def test_revocation(tmp_path):
    session = Session(tmp_path)
    token = session.token
    session.activate(['desktop'])
    session.stop()
    assert not session.authenticates(token)
    with pytest.raises(PermissionError): session.require('desktop')


def test_audit_has_no_token(tmp_path):
    session = Session(tmp_path)
    session.activate(['browser'])
    data = (tmp_path / 'audit.jsonl').read_text()
    assert session.token not in data
    assert set(json.loads(data)) == {'time', 'action', 'result'}


@pytest.mark.parametrize('url', ['file:///etc/passwd', 'javascript:alert(1)',
                                'https://user:pass@example.com', 'ftp://example.com', 'https://'])
def test_invalid_urls(url):
    with pytest.raises(ValueError): validate_url(url)


def test_https_url():
    assert validate_url('https://example.com') == 'https://example.com'


def test_unknown_permission(tmp_path):
    with pytest.raises(ValueError): Session(tmp_path).activate(['shell'])
