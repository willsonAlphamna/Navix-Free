import pytest
from starlette.testclient import TestClient
from navix.core import Session
from navix.server import make_app
from navix.desktop import Desktop


class FakeBrowser:
    def __init__(self, session): self.session = session
    def call(self, operation, **kwargs):
        self.session.require('browser')
        return [{'id': '1', 'url': 'https://example.com', 'title': 'Test'}]


@pytest.fixture
def api(tmp_path):
    session = Session(tmp_path)
    app = make_app(session, FakeBrowser(session), Desktop(session))
    with TestClient(app, base_url='http://127.0.0.1:8765') as client:
        yield session, client


def headers(session):
    return {'Authorization': 'Bearer ' + session.token,
            'Accept': 'application/json, text/event-stream',
            'MCP-Protocol-Version': '2025-03-26'}


def rpc(client, session, method, params=None):
    return client.post('/mcp', headers=headers(session), json={
        'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params or {}})


def test_missing_token_denied(api):
    session, client = api
    assert client.post('/mcp', json={}).status_code == 401
    assert client.get('/health').status_code == 401


def test_wrong_token_denied(api):
    session, client = api
    assert client.get('/health', headers={'Authorization': 'Bearer wrong'}).status_code == 401


def test_health_identifies_service(api):
    session, client = api
    assert client.get('/health', headers=headers(session)).json()['service'] == 'navix-desktop'


def test_tools_discovered(api):
    session, client = api
    response = rpc(client, session, 'tools/list')
    assert response.status_code == 200, response.text
    names = {tool['name'] for tool in response.json()['result']['tools']}
    assert {'desktop_type', 'browser_fill', 'status', 'desktop_hotkey',
            'browser_upload', 'browser_download', 'files_read', 'files_delete',
            'command_run', 'command_exec'} <= names


def test_default_tool_denied(api):
    session, client = api
    response = rpc(client, session, 'tools/call', {'name': 'browser_tabs', 'arguments': {}})
    assert response.json()['result']['isError'] is True


def test_authorized_browser(api):
    session, client = api
    session.activate(['browser'])
    response = rpc(client, session, 'tools/call', {'name': 'browser_tabs', 'arguments': {}})
    assert not response.json()['result'].get('isError')


def test_file_permission_does_not_grant_commands(api, tmp_path):
    session, client = api
    session.activate(['files'])
    path = str(tmp_path / 'authorized.txt')
    response = rpc(client, session, 'tools/call', {'name': 'files_write',
        'arguments': {'path': path, 'text': 'ok'}})
    assert not response.json()['result'].get('isError')
    response = rpc(client, session, 'tools/call', {'name': 'command_run',
        'arguments': {'shell': 'python', 'command': 'print("not allowed")'}})
    assert response.json()['result']['isError'] is True


def test_browser_permission_does_not_grant_file_access(api, tmp_path):
    session, client = api
    session.activate(['browser'])
    response = rpc(client, session, 'tools/call', {'name': 'files_write',
        'arguments': {'path': str(tmp_path / 'denied.txt'), 'text': 'must not be created'}})
    assert response.json()['result']['isError'] is True
    assert not (tmp_path / 'denied.txt').exists()


def test_revoke_existing_client(api):
    session, client = api
    old = headers(session)
    session.stop()
    assert client.get('/health', headers=old).status_code == 401


def test_host_attack_denied(api):
    session, client = api
    request_headers = headers(session)
    request_headers['Host'] = 'evil.example'
    response = client.post('/mcp', headers=request_headers, json={})
    assert response.status_code == 421


def test_origin_attack_denied(api):
    session, client = api
    request_headers = headers(session)
    request_headers['Origin'] = 'https://evil.example'
    response = client.post('/mcp', headers=request_headers, json={})
    assert response.status_code == 403


@pytest.mark.parametrize('path', [
    '/.well-known/oauth-protected-resource/mcp',
    '/.well-known/oauth-protected-resource',
    '/.well-known/oauth-authorization-server',
])
def test_no_oauth_metadata_is_404_without_token(api, path):
    _, client = api
    assert client.get(path).status_code == 404
    # A exceção de descoberta não libera outros caminhos sem autorização.
    assert client.get('/health').status_code == 401
