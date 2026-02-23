"""
conftest.py
===========
Shared fixtures for the AutoTech test suite.

Creates a minimal Flask test app that does NOT import main.py,
avoiding startup side effects (background threads, browser launch, DB init).
Blueprints are registered directly so routes can be tested in isolation.
"""

import importlib

import pytest
from flask import Flask


# ---------------------------------------------------------------------------
# Test application factory
# ---------------------------------------------------------------------------

@pytest.fixture(scope='session')
def test_app():
    """Create a Flask test app by registering blueprints directly (no main.py)."""
    from app.config import STATIC_FOLDER, TEMPLATE_FOLDER

    app = Flask(
        'autotech_test',
        template_folder=TEMPLATE_FOLDER,
        static_folder=STATIC_FOLDER,
    )
    app.secret_key = 'test-secret-key'
    app.config['TESTING'] = True

    # Register blueprints in the same order as main.py (mirrors production).
    # Use try/except so a single optional import failure doesn't break the suite.
    blueprint_modules = [
        'app.blueprints.auth',
        'app.blueprints.dashboard',
        'app.blueprints.system_health',
        'app.blueprints.equipment',
        'app.blueprints.info_pages',
        'app.blueprints.downloads',
        'app.blueprints.log_cleanup',
        'app.blueprints.admin_logs',
        'app.blueprints.ptx_reboot',
        'app.blueprints.vnc',
        'app.blueprints.usb_client',
        'app.blueprints.fleet_monitor',
        'app.blueprints.tools_launch',
        'app.blueprints.ptx_uptime',
        'app.blueprints.playback',
        'app.blueprints.legacy_terminal',
        'app.blueprints.frontrunner',
    ]

    for mod_name in blueprint_modules:
        try:
            mod = importlib.import_module(mod_name)
            app.register_blueprint(mod.bp)
        except Exception as exc:
            print(f"[conftest] Warning: could not register {mod_name}: {exc}")

    return app


@pytest.fixture
def client(test_app):
    """Return a fresh test client for each test."""
    return test_app.test_client()


@pytest.fixture
def auth_client(client):
    """Return a test client with an authenticated session pre-set."""
    with client.session_transaction() as sess:
        sess['authenticated'] = True
        sess['password'] = 'komatsu'
    return client


# ---------------------------------------------------------------------------
# State isolation fixtures (autouse — run for every test)
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_network_cache():
    """
    Expire the network status TTL cache before and after each test so that
    is_online_network() always performs a fresh check rather than returning
    a cached value from a previous test.
    """
    try:
        import app.state as state
        state._network_status_cache['ts'] = 0.0
        state._network_status_cache['online'] = False
    except Exception:
        pass
    yield
    try:
        import app.state as state
        state._network_status_cache['ts'] = 0.0
        state._network_status_cache['online'] = False
    except Exception:
        pass


@pytest.fixture(autouse=True)
def no_live_network(mocker):
    """
    Patch all blueprint-level network-probe imports so route tests run
    instantly (no 1.5 s socket timeout).  Only the blueprint-namespace
    copies are patched; the canonical functions in app.utils are left
    intact so test_utils.py can call them directly.

    Tests that need online=True for a specific route can override with an
    additional mocker.patch() or by setting T1_FORCE_ONLINE=1 via monkeypatch.
    """
    # Ensure the blueprint modules are imported before patching.
    # (session-scoped test_app may not have run yet for config/utils tests.)
    try:
        import app.blueprints.dashboard        # noqa: F401
        import app.blueprints.equipment        # noqa: F401
        import app.blueprints.system_health    # noqa: F401
    except Exception:
        pass

    targets = [
        ('app.blueprints.dashboard.check_network_connectivity', False),
        ('app.blueprints.dashboard.is_online_network', False),
        ('app.blueprints.system_health.check_network_connectivity', False),
        ('app.blueprints.system_health.is_online_network', False),
        ('app.blueprints.equipment.is_online_network', False),
    ]
    for target, value in targets:
        try:
            mocker.patch(target, return_value=value)
        except Exception:
            pass
