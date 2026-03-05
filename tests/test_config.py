"""
test_config.py
==============
Pure unit tests for app/config.py constants and helpers.
No Flask, no mocks needed for most tests.
"""

import os
import re


# ---------------------------------------------------------------------------
# BASE_DIR
# ---------------------------------------------------------------------------

def test_base_dir_resolves():
    from app.config import BASE_DIR
    assert os.path.isdir(BASE_DIR), f"BASE_DIR is not a directory: {BASE_DIR!r}"


def test_base_dir_contains_main_py():
    """BASE_DIR should be the project root where main.py lives."""
    from app.config import BASE_DIR
    assert os.path.isfile(os.path.join(BASE_DIR, 'main.py')), \
        "Expected main.py in BASE_DIR — BASE_DIR may be pointing at the wrong level"


# ---------------------------------------------------------------------------
# get_version()
# ---------------------------------------------------------------------------

def test_get_version_returns_nonempty_string():
    from app.config import get_version
    version = get_version()
    assert isinstance(version, str)
    assert len(version) > 0


def test_get_version_dev_fallback(monkeypatch):
    """When VERSION file is absent, get_version() returns 'dev'."""
    import builtins
    from app.config import get_version

    real_open = builtins.open

    def _mock_open(path, *args, **kwargs):
        if 'VERSION' in str(path):
            raise FileNotFoundError(f"mocked: {path}")
        return real_open(path, *args, **kwargs)

    monkeypatch.setattr(builtins, 'open', _mock_open)
    assert get_version() == 'dev'


# ---------------------------------------------------------------------------
# resolve_data_path()
# ---------------------------------------------------------------------------

def test_resolve_data_path_usb_priority(tmp_path):
    """When an AutoTech sub-folder exists, USB path is returned first."""
    from app.config import resolve_data_path
    usb_dir = tmp_path / 'AutoTech'
    usb_dir.mkdir()

    result = resolve_data_path(str(tmp_path), 'fleet_data.json')
    assert 'AutoTech' in result
    assert 'database' in result
    assert result.endswith('fleet_data.json')


def test_resolve_data_path_dev_fallback(tmp_path):
    """Without AutoTech folder, dev/database path is returned."""
    from app.config import resolve_data_path
    result = resolve_data_path(str(tmp_path), 'fleet_data.json')
    expected = os.path.join(str(tmp_path), 'database', 'fleet_data.json')
    assert result == expected


# ---------------------------------------------------------------------------
# EQUIPMENT_PROFILES
# ---------------------------------------------------------------------------

def test_equipment_profiles_has_required_keys():
    from app.config import EQUIPMENT_PROFILES
    for name in ('K830E', 'K930E', 'Other'):
        assert name in EQUIPMENT_PROFILES, f"Missing profile: {name}"

    for name, profile in EQUIPMENT_PROFILES.items():
        assert 'has_flight_recorder' in profile, f"{name} missing has_flight_recorder"
        assert 'ptx_offset' in profile, f"{name} missing ptx_offset"


def test_equipment_profiles_flight_recorder_flags():
    from app.config import EQUIPMENT_PROFILES
    assert EQUIPMENT_PROFILES['K830E']['has_flight_recorder'] is True
    assert EQUIPMENT_PROFILES['K930E']['has_flight_recorder'] is True
    assert EQUIPMENT_PROFILES['Other']['has_flight_recorder'] is False


def test_equipment_profiles_ptx_offset_types():
    from app.config import EQUIPMENT_PROFILES
    for name, profile in EQUIPMENT_PROFILES.items():
        assert isinstance(profile['ptx_offset'], int), \
            f"{name}.ptx_offset should be int"


# ---------------------------------------------------------------------------
# TOOL_LIST
# ---------------------------------------------------------------------------

def test_tool_list_nonempty():
    from app.config import TOOL_LIST
    assert isinstance(TOOL_LIST, list)
    assert len(TOOL_LIST) > 0


def test_tool_list_all_strings():
    from app.config import TOOL_LIST
    for item in TOOL_LIST:
        assert isinstance(item, str), f"TOOL_LIST item is not a string: {item!r}"


def test_tool_list_contains_ip_finder():
    from app.config import TOOL_LIST
    assert 'IP Finder' in TOOL_LIST


# ---------------------------------------------------------------------------
# GATEWAY_IP
# ---------------------------------------------------------------------------

def test_gateway_ip_format():
    from app.config import GATEWAY_IP
    assert re.match(r'^\d+\.\d+\.\d+\.\d+$', GATEWAY_IP), \
        f"GATEWAY_IP does not look like an IPv4 address: {GATEWAY_IP!r}"


# ---------------------------------------------------------------------------
# MOCK_EQUIPMENT_DB
# ---------------------------------------------------------------------------

def test_mock_equipment_db_nonempty():
    from app.config import MOCK_EQUIPMENT_DB
    assert len(MOCK_EQUIPMENT_DB) > 0


def test_mock_equipment_db_has_ptx_ip():
    from app.config import MOCK_EQUIPMENT_DB
    for oid, entry in MOCK_EQUIPMENT_DB.items():
        assert 'ptx_ip' in entry, f"{oid} entry missing ptx_ip"


def test_mock_equipment_db_known_entries():
    from app.config import MOCK_EQUIPMENT_DB
    # The plan spec lists these entries
    for expected in ('DEV_K930E', 'DEV_K830E', 'DEV_AHG_PTXC', 'DEV_AHG_PTX10', 'DEV_AHG_PTXCNEW'):
        assert expected in MOCK_EQUIPMENT_DB, f"Expected {expected} in MOCK_EQUIPMENT_DB"


# ---------------------------------------------------------------------------
# Servers config
# ---------------------------------------------------------------------------

def test_servers_list_nonempty():
    from app.config import SERVERS
    assert isinstance(SERVERS, list)
    assert len(SERVERS) > 0


def test_servers_have_required_keys():
    from app.config import SERVERS
    for server in SERVERS:
        for key in ('name', 'ip', 'port'):
            assert key in server, f"Server {server} missing key '{key}'"
