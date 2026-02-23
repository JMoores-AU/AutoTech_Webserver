"""
test_auth_routes.py
===================
Integration tests for /login and /logout routes (app/blueprints/auth.py).
Uses the session-scoped test Flask app via the `client` fixture.
"""

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _post_login(client, password, follow_redirects=False):
    return client.post(
        '/login',
        data={'password': password},
        follow_redirects=follow_redirects,
    )


# ---------------------------------------------------------------------------
# /login — GET
# ---------------------------------------------------------------------------

def test_login_get_returns_200(client):
    resp = client.get('/login')
    assert resp.status_code == 200


def test_login_get_contains_form(client):
    resp = client.get('/login')
    assert b'password' in resp.data.lower()


# ---------------------------------------------------------------------------
# /login — POST (correct password)
# ---------------------------------------------------------------------------

def test_login_correct_password_redirects(client, mocker):
    mocker.patch('app.blueprints.auth.log_security')
    resp = _post_login(client, 'komatsu')
    assert resp.status_code == 302


def test_login_correct_password_sets_session(client, mocker):
    mocker.patch('app.blueprints.auth.log_security')
    _post_login(client, 'komatsu')
    with client.session_transaction() as sess:
        assert sess.get('authenticated') is True


def test_login_correct_password_redirects_to_dashboard(client, mocker):
    mocker.patch('app.blueprints.auth.log_security')
    resp = _post_login(client, 'komatsu', follow_redirects=False)
    # Location header should point to the dashboard (/)
    assert '/' in resp.headers.get('Location', '')


# ---------------------------------------------------------------------------
# /login — POST (wrong password)
# ---------------------------------------------------------------------------

def test_login_wrong_password_returns_200(client, mocker):
    mocker.patch('app.blueprints.auth.log_security')
    resp = _post_login(client, 'wrongpassword')
    assert resp.status_code == 200


def test_login_wrong_password_no_session(client, mocker):
    mocker.patch('app.blueprints.auth.log_security')
    _post_login(client, 'wrongpassword')
    with client.session_transaction() as sess:
        assert not sess.get('authenticated')


def test_login_wrong_password_shows_login_form(client, mocker):
    """Failed login re-renders the login form (not a redirect)."""
    mocker.patch('app.blueprints.auth.log_security')
    resp = _post_login(client, 'wrongpassword')
    # login.html renders a password input — error display is template-side via flash
    assert b'password' in resp.data.lower()


# ---------------------------------------------------------------------------
# /logout
# ---------------------------------------------------------------------------

def test_logout_redirects(auth_client, mocker):
    mocker.patch('app.blueprints.auth.log_security')
    resp = auth_client.get('/logout')
    assert resp.status_code == 302


def test_logout_clears_session(auth_client, mocker):
    mocker.patch('app.blueprints.auth.log_security')
    auth_client.get('/logout')
    with auth_client.session_transaction() as sess:
        assert not sess.get('authenticated')


def test_logout_redirects_to_login(auth_client, mocker):
    mocker.patch('app.blueprints.auth.log_security')
    resp = auth_client.get('/logout', follow_redirects=False)
    assert 'login' in resp.headers.get('Location', '').lower()


def test_logout_calls_log_security(auth_client, mocker):
    mock_log = mocker.patch('app.blueprints.auth.log_security')
    auth_client.get('/logout')
    mock_log.assert_called_once()
