"""
test_dashboard_routes.py
========================
Integration tests for the dashboard blueprint routes:
  / (GET, POST), /api/equipment_profiles, /api/flight_recorder_ip/<type>,
  /equipment_monitor/<id>, /run/<tool_name>

Network calls are patched by the conftest `no_live_network` autouse fixture.
"""

import pytest


# ---------------------------------------------------------------------------
# / — main dashboard
# ---------------------------------------------------------------------------

def test_dashboard_get_returns_200(client):
    resp = client.get('/')
    assert resp.status_code == 200


def test_dashboard_get_unauthenticated_shows_login_or_dashboard(client):
    """GET / without auth returns 200 — template decides what to render."""
    resp = client.get('/')
    assert resp.status_code == 200


def test_dashboard_get_authenticated_returns_200(auth_client):
    resp = auth_client.get('/')
    assert resp.status_code == 200


def test_dashboard_post_correct_password_sets_session(client):
    """POST / with correct password sets session['authenticated']."""
    resp = client.post('/', data={'password': 'komatsu'})
    assert resp.status_code == 200
    with client.session_transaction() as sess:
        assert sess.get('authenticated') is True


def test_dashboard_post_wrong_password_no_session(client):
    """POST / with wrong password does NOT set session['authenticated']."""
    client.post('/', data={'password': 'wrong'})
    with client.session_transaction() as sess:
        assert not sess.get('authenticated')


def test_dashboard_post_returns_200(client):
    resp = client.post('/', data={'password': 'anything'})
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# /api/equipment_profiles
# ---------------------------------------------------------------------------

def test_equipment_profiles_json(client):
    resp = client.get('/api/equipment_profiles')
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, dict)


def test_equipment_profiles_has_k830e(client):
    resp = client.get('/api/equipment_profiles')
    data = resp.get_json()
    assert 'K830E' in data


def test_equipment_profiles_has_k930e(client):
    resp = client.get('/api/equipment_profiles')
    data = resp.get_json()
    assert 'K930E' in data


def test_equipment_profiles_has_other(client):
    resp = client.get('/api/equipment_profiles')
    data = resp.get_json()
    assert 'Other' in data


def test_equipment_profiles_k830e_flight_recorder(client):
    resp = client.get('/api/equipment_profiles')
    data = resp.get_json()
    assert data['K830E']['has_flight_recorder'] is True


# ---------------------------------------------------------------------------
# /api/flight_recorder_ip/<equipment_type>
# ---------------------------------------------------------------------------

def test_flight_recorder_k830e_has_flag(client):
    resp = client.get('/api/flight_recorder_ip/K830E')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['has_flight_recorder'] is True


def test_flight_recorder_k830e_has_ip(client):
    resp = client.get('/api/flight_recorder_ip/K830E')
    data = resp.get_json()
    assert 'flight_recorder_ip' in data
    assert data['flight_recorder_ip'] is not None


def test_flight_recorder_k930e(client):
    resp = client.get('/api/flight_recorder_ip/K930E')
    data = resp.get_json()
    assert data['has_flight_recorder'] is True


def test_flight_recorder_other_no_recorder(client):
    resp = client.get('/api/flight_recorder_ip/Other')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['has_flight_recorder'] is False


def test_flight_recorder_unknown_type_no_recorder(client):
    """Unknown equipment types fall back to the 'Other' profile (no recorder)."""
    resp = client.get('/api/flight_recorder_ip/UnknownType')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['has_flight_recorder'] is False


# ---------------------------------------------------------------------------
# /equipment_monitor/<equipment_id>
# ---------------------------------------------------------------------------

def test_equipment_monitor_returns_200(client):
    resp = client.get('/equipment_monitor/TEST1')
    assert resp.status_code == 200


def test_equipment_monitor_arbitrary_id(client):
    resp = client.get('/equipment_monitor/RD999')
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# /run/<tool_name> — requires authentication
# ---------------------------------------------------------------------------

def test_run_tool_unauthenticated_redirects(client):
    """Unauthenticated request to /run/<tool> redirects to dashboard."""
    resp = client.get('/run/IP Finder')
    assert resp.status_code == 302


def test_run_ip_finder_authenticated(auth_client):
    resp = auth_client.get('/run/IP Finder')
    assert resp.status_code == 200


def test_run_unknown_tool_authenticated(auth_client):
    """Unknown tool names fall back to the generic tool template."""
    resp = auth_client.get('/run/Unknown Tool XYZ')
    assert resp.status_code == 200


def test_run_playback_tools_authenticated(auth_client):
    resp = auth_client.get('/run/Playback Tools')
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# /api/equipment_search
# ---------------------------------------------------------------------------

def test_equipment_search_no_query(client):
    resp = client.post(
        '/api/equipment_search',
        json={},
        content_type='application/json',
    )
    assert resp.status_code == 400


def test_equipment_search_mock_entry(client):
    """Known mock entry is returned without any SSH/network calls."""
    resp = client.post(
        '/api/equipment_search',
        json={'query': 'DEV_K930E'},
        content_type='application/json',
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data.get('found') is True
    assert data.get('OID') == 'DEV_K930E'
