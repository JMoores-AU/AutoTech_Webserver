"""
test_utils.py
=============
Unit tests for app/utils.py — parsing helpers, network probes,
path helpers, and the login_required decorator.

Network probes are either driven by env vars (no sockets) or mocked at the
socket layer so tests run instantly without real network access.
"""

import os
import time

import pytest


# ---------------------------------------------------------------------------
# parse_ip_finder_output
# ---------------------------------------------------------------------------

def test_parse_ip_finder_output_empty():
    from app.utils import parse_ip_finder_output
    result = parse_ip_finder_output('AHG135', '')
    assert result['found'] is False
    assert result['OID'] == 'AHG135'


def test_parse_ip_finder_output_none():
    from app.utils import parse_ip_finder_output
    result = parse_ip_finder_output('AHG135', None)
    assert result['found'] is False


def test_parse_ip_finder_output_table_row():
    """Parses the equipment table row and sets found=True."""
    from app.utils import parse_ip_finder_output
    output = (
        "+--------+---------+---------------+--------------+\n"
        "| _OID_  | _CID_   | _profile      | network_ip   |\n"
        "+--------+---------+---------------+--------------+\n"
        "| AHG135 | eqmt_lv | LV Single Cab | 10.110.21.87 |\n"
        "+--------+---------+---------------+--------------+\n"
    )
    result = parse_ip_finder_output('AHG135', output)
    assert result['found'] is True
    assert result['OID'] == 'AHG135'
    assert result['profile'] == 'LV Single Cab'


def test_parse_ip_finder_output_ptx_ip_line():
    """Extracts IP from 'PTX IP is: x.x.x.x' line."""
    from app.utils import parse_ip_finder_output
    output = "PTX IP is: 10.110.21.87\n"
    result = parse_ip_finder_output('AHG135', output)
    assert result['ptx_ip'] == '10.110.21.87'


def test_parse_ip_finder_output_vehicle_online():
    from app.utils import parse_ip_finder_output
    output = "Vehicle is Online.\n"
    result = parse_ip_finder_output('AHG135', output)
    assert result['vehicle_status'] == 'Online'


def test_parse_ip_finder_output_vehicle_offline():
    from app.utils import parse_ip_finder_output
    output = "Vehicle is Offline.\n"
    result = parse_ip_finder_output('AHG135', output)
    assert result['vehicle_status'] == 'Offline'


def test_parse_ip_finder_output_ptxc_found():
    from app.utils import parse_ip_finder_output
    output = "PTXC Found.\n"
    result = parse_ip_finder_output('AHG135', output)
    assert result['ptxc_found'] is True
    assert result['ptx_model'] == 'PTXC'


def test_parse_ip_finder_avi_ip():
    """Extracts AVI IP from 'AVI IP is : x.x.x.x' line."""
    from app.utils import parse_ip_finder_output
    output = "AVI IP is : 10.111.21.87\n"
    result = parse_ip_finder_output('AHG135', output)
    assert result['avi_ip'] == '10.111.21.87'


def test_parse_ip_finder_combined_output():
    """Full realistic output is parsed correctly."""
    from app.utils import parse_ip_finder_output
    output = (
        "+--------+---------+---------------+--------------+\n"
        "| _OID_  | _CID_   | _profile      | network_ip   |\n"
        "+--------+---------+---------------+--------------+\n"
        "| AHG135 | eqmt_lv | LV Single Cab | 10.110.21.87 |\n"
        "+--------+---------+---------------+--------------+\n"
        "PTX IP is: 10.110.21.87\n"
        "Vehicle is Online.\n"
        "PTXC Found.\n"
        "AVI IP is : 10.111.21.87\n"
    )
    result = parse_ip_finder_output('AHG135', output)
    assert result['found'] is True
    assert result['ptx_ip'] == '10.110.21.87'
    assert result['vehicle_status'] == 'Online'
    assert result['ptxc_found'] is True
    assert result['avi_ip'] == '10.111.21.87'


# ---------------------------------------------------------------------------
# is_online_network — env-var driven (no sockets, instant)
# ---------------------------------------------------------------------------

def test_is_online_forced_offline_env(monkeypatch):
    """T1_OFFLINE=1 forces offline without any network probe."""
    import app.state as state
    from app.utils import is_online_network

    monkeypatch.setenv('T1_OFFLINE', '1')
    monkeypatch.delenv('T1_FORCE_ONLINE', raising=False)
    state._network_status_cache['ts'] = 0.0  # Expire cache

    result = is_online_network(force_refresh=True)
    assert result is False
    assert state._network_status_cache['online'] is False


def test_is_online_forced_online_env(monkeypatch):
    """T1_FORCE_ONLINE=1 forces online without any network probe."""
    import app.state as state
    from app.utils import is_online_network

    monkeypatch.delenv('T1_OFFLINE', raising=False)
    monkeypatch.setenv('T1_FORCE_ONLINE', '1')
    state._network_status_cache['ts'] = 0.0  # Expire cache

    result = is_online_network(force_refresh=True)
    assert result is True
    assert state._network_status_cache['online'] is True


def test_is_online_caches_result():
    """A second call within the TTL window returns the cached value."""
    import app.state as state
    from app.utils import is_online_network

    # Manually seed the cache as "online" with a fresh timestamp
    state._network_status_cache['ts'] = time.time()
    state._network_status_cache['online'] = True

    # Without force_refresh the cache is returned (no network probe)
    result = is_online_network()
    assert result is True  # Cache is authoritative


def test_is_online_expired_cache_triggers_probe(monkeypatch):
    """Expired cache + env var shortcut — proves refresh path is taken."""
    import app.state as state
    from app.utils import is_online_network

    state._network_status_cache['ts'] = 0.0  # Force expired
    state._network_status_cache['online'] = True  # Stale value

    monkeypatch.setenv('T1_OFFLINE', '1')
    monkeypatch.delenv('T1_FORCE_ONLINE', raising=False)

    # Refresh path is taken; env var says offline
    result = is_online_network()
    assert result is False


# ---------------------------------------------------------------------------
# check_network_connectivity — socket-level mocking
# ---------------------------------------------------------------------------

def test_check_connectivity_offline(mocker):
    from app.utils import check_network_connectivity
    mocker.patch('socket.create_connection', side_effect=OSError("connection refused"))
    mocker.patch('app.utils.ping3', None)
    assert check_network_connectivity() is False


def test_check_connectivity_online(mocker):
    from unittest.mock import MagicMock
    from app.utils import check_network_connectivity

    mock_sock = MagicMock()
    mock_sock.__enter__ = MagicMock(return_value=mock_sock)
    mock_sock.__exit__ = MagicMock(return_value=False)
    mocker.patch('socket.create_connection', return_value=mock_sock)
    mocker.patch('app.utils.ping3', None)

    assert check_network_connectivity() is True


# ---------------------------------------------------------------------------
# resolve_plink_path()
# ---------------------------------------------------------------------------

def test_resolve_plink_no_candidates(mocker):
    """Returns None when no plink.exe file exists."""
    from app.utils import resolve_plink_path
    mocker.patch('os.path.exists', return_value=False)
    assert resolve_plink_path() is None


def test_resolve_plink_first_match(tmp_path, monkeypatch):
    """Returns the first existing candidate path."""
    from app.utils import resolve_plink_path
    import app.utils as utils_mod

    fake_plink = tmp_path / 'plink.exe'
    fake_plink.write_bytes(b'fake')

    # Inject our fake path as the only candidate
    monkeypatch.setattr(utils_mod, 'PLINK_CANDIDATES', [str(fake_plink)])
    result = resolve_plink_path()
    assert result == str(fake_plink)


# ---------------------------------------------------------------------------
# login_required decorator
# ---------------------------------------------------------------------------

def test_login_required_unauthenticated():
    """Unauthenticated request → 401 JSON error."""
    from flask import Flask
    from app.utils import login_required

    app = Flask('_test_lr')
    app.secret_key = 'test'

    @app.route('/protected')
    @login_required
    def protected():
        from flask import jsonify
        return jsonify({'ok': True})

    with app.test_client() as c:
        resp = c.get('/protected')
        assert resp.status_code == 401
        data = resp.get_json()
        assert 'error' in data


def test_login_required_authenticated():
    """Authenticated request passes through to the view."""
    from flask import Flask
    from app.utils import login_required

    app = Flask('_test_lr2')
    app.secret_key = 'test'

    @app.route('/protected')
    @login_required
    def protected():
        from flask import jsonify
        return jsonify({'ok': True})

    with app.test_client() as c:
        with c.session_transaction() as sess:
            sess['authenticated'] = True
        resp = c.get('/protected')
        assert resp.status_code == 200
        assert resp.get_json() == {'ok': True}
