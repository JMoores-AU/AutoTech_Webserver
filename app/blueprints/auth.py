"""
app/blueprints/auth.py
======================
Authentication routes: /login, /logout
"""

from flask import Blueprint, render_template, request, session, redirect, url_for
from tools.app_logger import log_security

bp = Blueprint('auth', __name__, url_prefix='')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Simple login form"""
    if request.method == 'POST':
        password = request.form.get('password')
        if password == 'komatsu':
            session['authenticated'] = True
            session['password'] = password
            log_security('info', 'login', f'Successful login from {request.remote_addr}')
            return redirect(url_for('dashboard.dashboard'))
        else:
            log_security('warning', 'login', f'Failed login attempt from {request.remote_addr}')
            return render_template('login.html', error='Invalid password')

    return render_template('login.html')


@bp.route('/logout')
def logout():
    """Logout and clear session"""
    log_security('info', 'logout', f'User logged out from {request.remote_addr}')
    session.clear()
    return redirect(url_for('auth.login'))
