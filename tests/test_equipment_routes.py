"""
test_equipment_routes.py
========================
Integration tests for equipment management API routes
(app/blueprints/equipment.py):
  /api/equipment/cache, /api/equipment/cache/stats,
  /api/equipment (GET, POST), /api/equipment/<name> (DELETE),
  /api/equipment/updater/start, /api/equipment/updater/stop,
  /api/equipment/updater/status

state.EQUIPMENT_DB_PATH defaults to None in tests so "no DB" error paths
are exercised without needing a real database file.
"""

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def no_db(monkeypatch):
    """Ensure EQUIPMENT_DB_PATH is None for all tests in this module."""
    import app.state as state
    monkeypatch.setattr(state, 'EQUIPMENT_DB_PATH', None)


# ---------------------------------------------------------------------------
# /api/equipment/cache — GET
# ---------------------------------------------------------------------------

def test_equipment_cache_no_db(auth_client):
    resp = auth_client.get('/api/equipment/cache')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is False
    assert 'not initialized' in data['error'].lower()


def test_equipment_cache_json_content_type(auth_client):
    resp = auth_client.get('/api/equipment/cache')
    assert 'application/json' in resp.content_type


# ---------------------------------------------------------------------------
# /api/equipment/cache/stats — GET
# ---------------------------------------------------------------------------

def test_equipment_cache_stats_no_db(auth_client):
    resp = auth_client.get('/api/equipment/cache/stats')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is False
    assert 'not initialized' in data['error'].lower()


# ---------------------------------------------------------------------------
# /api/equipment — POST (create)
# ---------------------------------------------------------------------------

def test_equipment_create_no_db(auth_client):
    """With no DB, create returns 500."""
    resp = auth_client.post(
        '/api/equipment',
        json={'equipment_name': 'RD999'},
        content_type='application/json',
    )
    assert resp.status_code == 500
    data = resp.get_json()
    assert data['success'] is False


def test_equipment_create_missing_name_no_body(auth_client, monkeypatch):
    """POST with no equipment_name field returns 400."""
    import app.state as state
    import tempfile, os
    from tools.equipment_db import init_database

    # Give it a real (temporary) DB so we test the validation path
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    try:
        init_database(db_path)
        monkeypatch.setattr(state, 'EQUIPMENT_DB_PATH', db_path)

        # Send a non-empty body that has no equipment_name — triggers name validation
        resp = auth_client.post(
            '/api/equipment',
            json={'oid': 'TEST-OID'},
            content_type='application/json',
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert data['success'] is False
        # The error should mention the missing required field
        assert 'equipment_name' in data['error'] or 'required' in data['error'].lower()
    finally:
        os.unlink(db_path)


def test_equipment_create_missing_name_null(auth_client, monkeypatch):
    """POST with explicit null name returns 400."""
    import app.state as state
    import tempfile, os
    from tools.equipment_db import init_database

    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    try:
        init_database(db_path)
        monkeypatch.setattr(state, 'EQUIPMENT_DB_PATH', db_path)

        resp = auth_client.post(
            '/api/equipment',
            json={'equipment_name': None},
            content_type='application/json',
        )
        assert resp.status_code == 400
    finally:
        os.unlink(db_path)


# ---------------------------------------------------------------------------
# /api/equipment/updater/status — GET
# ---------------------------------------------------------------------------

def test_equipment_updater_status_returns_200(auth_client):
    resp = auth_client.get('/api/equipment/updater/status')
    assert resp.status_code == 200


def test_equipment_updater_status_has_required_keys(auth_client):
    resp = auth_client.get('/api/equipment/updater/status')
    data = resp.get_json()
    assert data['success'] is True
    for key in ('running', 'status'):
        assert key in data, f"Missing key: {key}"


def test_equipment_updater_status_not_running_initially(auth_client):
    import app.state as state
    state.background_updater['running'] = False
    state.background_updater['status'] = 'stopped'

    resp = auth_client.get('/api/equipment/updater/status')
    data = resp.get_json()
    assert data['running'] is False


# ---------------------------------------------------------------------------
# /api/equipment/updater/start — POST
# ---------------------------------------------------------------------------

def test_equipment_updater_start_no_db(auth_client):
    """Without a DB path, start returns an error."""
    resp = auth_client.post('/api/equipment/updater/start', json={})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is False
    assert 'database' in data['error'].lower() or 'not initialized' in data['error'].lower()


def test_equipment_updater_start_offline(auth_client, monkeypatch):
    """Even with a DB, start refuses when offline."""
    import app.state as state
    import tempfile, os
    from tools.equipment_db import init_database

    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    try:
        init_database(db_path)
        monkeypatch.setattr(state, 'EQUIPMENT_DB_PATH', db_path)
        # is_online_network is already patched to False by autouse fixture

        resp = auth_client.post('/api/equipment/updater/start', json={})
        data = resp.get_json()
        assert data['success'] is False
        assert 'online' in data['error'].lower() or 'offline' in data['error'].lower()
    finally:
        os.unlink(db_path)


# ---------------------------------------------------------------------------
# /api/equipment/updater/stop — POST
# ---------------------------------------------------------------------------

def test_equipment_updater_stop_not_running(auth_client):
    """Stop when not running returns an error."""
    import app.state as state
    state.background_updater['running'] = False

    resp = auth_client.post('/api/equipment/updater/stop', json={})
    data = resp.get_json()
    assert data['success'] is False
    assert 'not running' in data['error'].lower()


# ---------------------------------------------------------------------------
# /api/equipment — GET (list)
# ---------------------------------------------------------------------------

def test_equipment_list_no_db(auth_client):
    resp = auth_client.get('/api/equipment')
    assert resp.status_code == 500
    data = resp.get_json()
    assert data['success'] is False


# ---------------------------------------------------------------------------
# /api/equipment/<name> — DELETE
# ---------------------------------------------------------------------------

def test_equipment_delete_no_db(auth_client):
    resp = auth_client.delete('/api/equipment/RD999')
    assert resp.status_code == 500
    data = resp.get_json()
    assert data['success'] is False


# ---------------------------------------------------------------------------
# /api/equipment/cache/<name> — single item
# ---------------------------------------------------------------------------

def test_equipment_cache_single_no_db(auth_client):
    resp = auth_client.get('/api/equipment/cache/RD111')
    data = resp.get_json()
    assert data['success'] is False
    assert 'not initialized' in data['error'].lower()
