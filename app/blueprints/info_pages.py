"""
app/blueprints/info_pages.py
============================
Static informational page routes:
  /autotech, /legacy, /database, /t1-tools-help
"""

from flask import Blueprint, render_template
from app.config import GATEWAY_IP
from app.utils import is_online_network

bp = Blueprint('info_pages', __name__, url_prefix='')


@bp.route('/autotech')
@bp.route('/legacy')  # Keep legacy route for backwards compatibility
def autotech_tools():
    """AutoTech Tools page with IP Finder only"""
    return render_template('t1_legacy.html',
                           online=is_online_network(),
                           gateway_ip=GATEWAY_IP)


@bp.route('/database')
def equipment_cache_page():
    """Equipment Cache database viewer page"""
    return render_template('equip_db.html',
                           online=is_online_network())


@bp.route('/t1-tools-help')
def t1_tools_help():
    """T1 Tools command reference page"""
    return render_template('t1_tools_help.html',
                           online=is_online_network())
