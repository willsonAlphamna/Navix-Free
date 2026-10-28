import pytest
from navix.cloud import CloudSettings, permission_for_tool, authorize_cloud_tool
from navix.core import Session


def test_cloud_disabled_without_credentials():
    CloudSettings().validate()


@pytest.mark.parametrize('url', [
    'http://relay.example.com', 'ws://relay.example.com', 'wss://localhost',
    'wss://127.0.0.1', 'wss://192.168.0.1', 'wss://user:password@relay.example.com',
    'wss://relay.example.com/?token=secret', 'wss://relay.example.com/anything',
])
def test_cloud_rejects_unsafe_endpoints(url):
    with pytest.raises(ValueError):
        CloudSettings(enabled=True, relay_url=url).validate()


def test_cloud_accepts_secure_explicit_endpoint():
    CloudSettings(enabled=True, relay_url='wss://relay.example.com/api/device/connect').validate()


@pytest.mark.parametrize('name,kind', [
    ('browser_open','browser'), ('browser_screenshot','browser'),
    ('desktop_click','desktop'), ('desktop_type','desktop'),
    ('files_read','files'), ('files_delete','files'),
    ('command_exec','commands'), ('command_run','commands'),
    ('status',None),
])
def test_tool_mapping_stays_strict(name, kind):
    assert permission_for_tool(name) == kind


def test_unknown_tool_never_executes(tmp_path):
    session=Session(tmp_path)
    session.activate(['commands'],minutes=None)
    with pytest.raises(PermissionError):
        authorize_cloud_tool(session,'super_admin')


def test_remote_oauth_cannot_override_local_permissions(tmp_path):
    session=Session(tmp_path)
    with pytest.raises(PermissionError):
        authorize_cloud_tool(session,'status')
    session.activate(['browser'],minutes=None)
    assert authorize_cloud_tool(session,'browser_open')
    with pytest.raises(PermissionError):
        authorize_cloud_tool(session,'files_delete')
    session.stop()
    with pytest.raises(PermissionError):
        authorize_cloud_tool(session,'browser_open')
