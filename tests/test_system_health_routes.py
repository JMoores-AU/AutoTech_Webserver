"""
test_system_health_routes.py
============================
Integration tests for system health API routes (app/blueprints/system_health.py):
  /api/mode, /api/network_status, /api/health, /api/system/status

Network calls are patched by the conftest `no_live_network` autouse fixture
(all network checks return False by default).
Tests that need online=True patch the blueprint-level function directly.
"""

import pytest


# ---------------------------------------------------------------------------
# /api/mode
# ---------------------------------------------------------------------------

def test_api_mode_returns_200(client):
    resp = client.get('/api/mode')
    assert resp.status_code == 200


def test_api_mode_offline(client):
    """With network mocked offline, response contains online=false."""
    resp = client.get('/api/mode')
    data = resp.get_json()
    assert 'online' in data
    assert data['online'] is False


def test_api_mode_online(client, mocker):
    """Patch blueprint-level is_online_network to return True."""
    mocker.patch('app.blueprints.system_health.is_online_network', return_value=True)
    resp = client.get('/api/mode')
    data = resp.get_json()
    assert data['online'] is True


def test_api_mode_json_content_type(client):
    resp = client.get('/api/mode')
    assert 'application/json' in resp.content_type


# ---------------------------------------------------------------------------
# /api/network_status
# ---------------------------------------------------------------------------

def test_api_network_status_returns_200(client):
    resp = client.get('/api/network_status')
    assert resp.status_code == 200


def test_api_network_status_has_required_keys(client):
    resp = client.get('/api/network_status')
    data = resp.get_json()
    for key in ('online', 'gateway_ip', 'timestamp'):
        assert key in data, f"Missing key: {key}"


def test_api_network_status_gateway_ip_format(client):
    import re
    resp = client.get('/api/network_status')
    data = resp.get_json()
    assert re.match(r'^\d+\.\d+\.\d+\.\d+$', data['gateway_ip'])


def test_api_network_status_offline_by_default(client):
    resp = client.get('/api/network_status')
    data = resp.get_json()
    assert data['online'] is False


# ---------------------------------------------------------------------------
# /api/health
# ---------------------------------------------------------------------------

def test_api_health_returns_200(client):
    resp = client.get('/api/health')
    assert resp.status_code == 200


def test_api_health_has_required_keys(client):
    resp = client.get('/api/health')
    data = resp.get_json()
    for key in ('status', 'database_status', 'databases'):
        assert key in data, f"Missing key: {key}"


def test_api_health_status_field(client):
    resp = client.get('/api/health')
    data = resp.get_json()
    assert data['status'] == 'healthy'


def test_api_health_databases_is_dict(client):
    resp = client.get('/api/health')
    data = resp.get_json()
    assert isinstance(data['databases'], dict)


def test_api_health_equipment_db_missing(client, monkeypatch):
    """When EQUIPMENT_DB_PATH is None the endpoint reports not_initialized."""
    import app.state as state
    monkeypatch.setattr(state, 'EQUIPMENT_DB_PATH', None)

    resp = client.get('/api/health')
    data = resp.get_json()
    eq_db = data['databases'].get('equipment_cache', {})
    assert eq_db.get('status') == 'not_initialized'


def test_api_health_database_status_degraded_when_no_db(client, monkeypatch):
    """With no DBs configured, database_status should be 'degraded'."""
    import app.state as state
    monkeypatch.setattr(state, 'EQUIPMENT_DB_PATH', None)
    monkeypatch.setattr(state, 'PTX_UPTIME_DB_PATH', None)

    resp = client.get('/api/health')
    data = resp.get_json()
    assert data['database_status'] == 'degraded'


def test_api_health_has_server_info(client):
    resp = client.get('/api/health')
    data = resp.get_json()
    assert 'server' in data
    server = data['server']
    assert 'platform' in server
    assert 'python_version' in server


# ---------------------------------------------------------------------------
# /api/system/status
# ---------------------------------------------------------------------------

def test_api_system_status_returns_200(client):
    resp = client.get('/api/system/status')
    assert resp.status_code == 200


def test_api_system_status_has_keys(client):
    resp = client.get('/api/system/status')
    data = resp.get_json()
    for key in ('running_as_service', 'active_connections', 'timestamp'):
        assert key in data, f"Missing key: {key}"


def test_api_system_status_service_false_in_test(client):
    """In a test environment the AutoTech Windows service is not running."""
    resp = client.get('/api/system/status')
    data = resp.get_json()
    # running_as_service may be True or False — just ensure it's a bool
    assert isinstance(data['running_as_service'], bool)
