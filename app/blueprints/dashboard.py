"""
app/blueprints/dashboard.py
============================
Main dashboard and tool execution routes:
  / (GET, POST), /api/equipment_profiles, /api/equipment_search,
  /equipment_monitor/<equipment_id>, /api/flight_recorder_ip/<equipment_type>,
  /run/<tool_name>
"""

import logging
from datetime import datetime

from flask import (Blueprint, flash, jsonify, redirect,
                   render_template, request, session, url_for)

from app.config import EQUIPMENT_PROFILES, GATEWAY_IP, PTX_BASE_IP, TOOL_LIST
from app.utils import check_network_connectivity, is_online_network, search_equipment

logger = logging.getLogger(__name__)

bp = Blueprint('dashboard', __name__, url_prefix='')


@bp.route('/', methods=['GET', 'POST'])
def dashboard():
    """Main dashboard with enhanced functionality"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if request.method == "POST":
        password = request.form.get("password", "").strip().lower()
        if password == "komatsu":
            session["authenticated"] = True
            session["password"] = password
            flash("Login successful!", "success")
        else:
            flash("Incorrect password", "error")

    logged_in = session.get("authenticated", False)
    network_online = check_network_connectivity()

    dashboard_data = {
        'logged_in': logged_in,
        'current_time': now,
        'tools': TOOL_LIST,
        'online': is_online_network(),
        'network_status': 'Online' if network_online else 'Offline',
        'gateway_ip': GATEWAY_IP,
        'timestamp': now,
        'equipment_count': len(EQUIPMENT_PROFILES)
    }

    # CRITICAL: Always use main_dashboard.html, never index.html
    return render_template("main_dashboard.html", **dashboard_data)


@bp.route('/api/equipment_profiles')
def equipment_profiles():
    """Equipment profiles API"""
    return jsonify(EQUIPMENT_PROFILES)


@bp.route('/api/equipment_search', methods=['POST'])
def api_equipment_search():
    """Equipment search API"""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()

        if not query:
            return jsonify({'error': 'Search query required'}), 400

        result = search_equipment(query)
        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/equipment_monitor/<equipment_id>')
def equipment_monitor(equipment_id):
    """
    Popout page for monitoring specific equipment.
    No search functionality - equipment-specific monitoring only.
    """
    return render_template('ip_finder_popout.html',
                           equipment_id=equipment_id,
                           online=is_online_network(),
                           gateway_ip=GATEWAY_IP,
                           timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))


@bp.route('/api/flight_recorder_ip/<equipment_type>')
def api_get_flight_recorder_ip(equipment_type):
    """
    Flight Recorder IP calculation API.
    CRITICAL: Only works for K830E and K930E profiles.
    """
    try:
        profile = EQUIPMENT_PROFILES.get(equipment_type, EQUIPMENT_PROFILES['Other'])

        if not profile['has_flight_recorder']:
            return jsonify({
                'error': f'Flight Recorder not available for {equipment_type}',
                'has_flight_recorder': False
            })

        base_ip_parts = PTX_BASE_IP.split('.')
        last_octet = int(base_ip_parts[-1]) + profile['ptx_offset']
        flight_recorder_ip = '.'.join(base_ip_parts[:-1] + [str(last_octet)])

        return jsonify({
            'equipment_type': equipment_type,
            'ptx_ip': PTX_BASE_IP,
            'flight_recorder_ip': flight_recorder_ip,
            'has_flight_recorder': True,
            'offset': profile['ptx_offset']
        })

    except Exception as e:
        logger.error(f"Error calculating Flight Recorder IP for {equipment_type}: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/run/<tool_name>')
def run_tool(tool_name):
    """
    Tool execution route with special handling for IP Finder.
    CRITICAL: IP Finder uses dedicated page, NOT inline.
    """
    if not session.get("authenticated"):
        return redirect(url_for("dashboard.dashboard"))

    try:
        # CRITICAL: IP Finder gets its own dedicated page
        if tool_name == "IP Finder":
            return render_template('ip_finder.html',
                                   online=is_online_network(),
                                   gateway_ip=GATEWAY_IP,
                                   timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

        # Handle PTX Uptime with enhanced functionality
        if tool_name == "PTX Uptime":
            from app.blueprints.ptx_uptime import handle_ptx_uptime
            return handle_ptx_uptime()

        # Handle FrontRunner Status
        if tool_name == "FrontRunner Status":
            from app.blueprints.ptx_uptime import handle_frontrunner_status
            return handle_frontrunner_status()

        # Handle CamStudio USB
        if tool_name == "CamStudio USB":
            return render_template('usb_tool.html',
                                   tool_name=tool_name,
                                   tool_id='camstudio',
                                   tool_icon='🎬',
                                   tool_display_name='CamStudio Portable',
                                   tool_description='Screen recording and capture tool',
                                   tool_folder='CamStudio_USB',
                                   tool_file='CamStudioPortable.exe',
                                   online=is_online_network(),
                                   gateway_ip=GATEWAY_IP,
                                   timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

        # Handle Playback USB
        if tool_name == "Playback USB":
            return render_template('usb_tool.html',
                                   tool_name=tool_name,
                                   tool_id='playback',
                                   tool_icon='\u25b6\ufe0f',
                                   tool_display_name='Playback Tool V3.7.0',
                                   tool_description='Video playback and review tool',
                                   tool_folder='frontrunnerV3-3.7.0-076-full',
                                   tool_file='V3.7.0 Playback Tool.bat',
                                   online=is_online_network(),
                                   gateway_ip=GATEWAY_IP,
                                   timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

        # Handle combined Playback Tools page
        if tool_name == "Playback Tools":
            return render_template('playback_tools.html',
                                   tool_name=tool_name,
                                   online=is_online_network(),
                                   gateway_ip=GATEWAY_IP,
                                   timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

        # For other tools, use generic tool template
        tool_data = {
            'tool_name': tool_name,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'online': is_online_network(),
            'gateway_ip': GATEWAY_IP
        }

        return render_template('tool_generic.html', **tool_data)

    except Exception as e:
        logger.error(f"Error running tool {tool_name}: {e}")
        flash(f"Tool Error: {e}", "error")
        return redirect(url_for('dashboard.dashboard'))
