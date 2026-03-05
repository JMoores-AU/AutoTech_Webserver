"""
app/blueprints/fleet_monitor.py
=================================
Dig Fleet Monitor routes:
  /dig_fleet_monitor, /api/fleet_data, /api/fleet_data/refresh,
  /api/fleet_data/save
"""

import json
import logging
import os
import threading
from datetime import datetime

from flask import Blueprint, jsonify, render_template, request

import app.state as state
from app.background_tasks import format_uptime_hours, probe_equipment_health
from app.config import FLEET_DATA_PATH, GATEWAY_IP
from app.utils import is_online_network
from tools.equipment_db import get_equipment
from tools.app_logger import log_database

logger = logging.getLogger(__name__)

bp = Blueprint('fleet_monitor', __name__, url_prefix='')


@bp.route('/dig_fleet_monitor')
def dig_fleet_monitor():
    """Dig Fleet Monitor page."""
    return render_template('dig_fleet_monitor.html',
                           page_title="Dig Fleet Monitor",
                           online=is_online_network(),
                           gateway_ip=GATEWAY_IP,
                           timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))


@bp.route('/api/fleet_data')
def api_fleet_data():
    """Fleet data with health info from SQL DB — non-blocking and failure resilient."""
    try:
        data = None
        if os.path.exists(FLEET_DATA_PATH):
            try:
                with open(FLEET_DATA_PATH, 'r') as f:
                    data = json.load(f)
            except Exception as read_err:
                logger.error(f"Fleet Monitor: Error reading layout file: {read_err}")

        if not data:
            logger.warning("Fleet Monitor: Using safety fallback layout")
            data = {
                "columns": [
                    {"id": "extraction", "title": "Extraction", "main": "GR1 Mining1", "back": "GR6 Mining2",
                     "phone": "4940 4777", "comms": "Normal Auto Truck | Shovel comms",
                     "color": "#8d97a5", "equipment": []},
                    {"id": "lh_north", "title": "Load & Haul North", "main": "GR17", "back": "GR18",
                     "phone": "4258", "comms": "Auto Truck", "color": "#f7a224", "equipment": ["EXD69", "EXD99"]},
                    {"id": "lh_central", "title": "Load & Haul Central", "main": "GR15", "back": "GR16",
                     "phone": "4259", "comms": "Auto Truck", "color": "#73c05c", "equipment": ["EXD265", "EXD81"]},
                    {"id": "lh_south", "title": "Load & Haul South", "main": "GR13", "back": "GR14",
                     "phone": "4252", "comms": "Auto Truck", "color": "#f7e127", "equipment": ["EXD82", "EXD66"]}
                ]
            }

        health_data = {}
        try:
            health_data = state.fleet_monitor_db.get_latest_health()
        except Exception as db_err:
            logger.error(f"Fleet Monitor: SQL error: {db_err}")

        for column in data['columns']:
            detailed = []
            for eq_id in column['equipment']:
                health = health_data.get(eq_id)
                cached = get_equipment(state.EQUIPMENT_DB_PATH, eq_id) if state.EQUIPMENT_DB_PATH else None
                ptx_ip = cached.get('network_ip') if cached else None

                if not health:
                    if is_online_network():
                        threading.Thread(target=probe_equipment_health, args=(eq_id,), daemon=True).start()
                    detailed.append({
                        'id': eq_id, 'ptx_ip': ptx_ip, 'uptime': 'Pending', 'uptime_hours': 0,
                        'mem_usage': '--%', 'mem_usage_raw': 0, 'last_updated': None
                    })
                else:
                    detailed.append({
                        'id': eq_id,
                        'ptx_ip': ptx_ip,
                        'uptime': format_uptime_hours(health['uptime_hours']),
                        'uptime_hours': health['uptime_hours'],
                        'mem_usage': f"{health['mem_usage']}%",
                        'mem_usage_raw': health['mem_usage'],
                        'last_updated': health['last_updated']
                    })
            column['equipment_detailed'] = detailed

        return jsonify(data)

    except Exception as e:
        logger.error(f"CRITICAL Fleet Monitor API Failure: {e}")
        return jsonify({
            "columns": [{"id": "emergency", "title": "SYSTEM ERROR", "main": "-", "back": "-",
                         "phone": "-", "comms": str(e), "color": "#ff0000",
                         "equipment": [], "equipment_detailed": []}]
        })


@bp.route('/api/fleet_data/refresh', methods=['POST'])
def api_fleet_data_refresh():
    """Manually trigger a re-probe of all equipment (non-blocking)."""
    try:
        if not os.path.exists(FLEET_DATA_PATH):
            return jsonify({'success': False, 'error': 'No layout'}), 404

        with open(FLEET_DATA_PATH, 'r') as f:
            data = json.load(f)

        for col in data['columns']:
            for eq_id in col['equipment']:
                threading.Thread(target=probe_equipment_health, args=(eq_id,), daemon=True).start()

        return jsonify({'success': True, 'message': 'Refresh tasks queued'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/fleet_data/save', methods=['POST'])
def api_fleet_data_save():
    """Save updated fleet layout and trigger immediate probe for new items."""
    try:
        data = request.get_json()
        if not data or 'columns' not in data:
            return jsonify({'success': False, 'error': 'Invalid data'}), 400

        save_data = {'columns': []}
        all_ids = []
        for col in data['columns']:
            eq_ids = [eq['id'] if isinstance(eq, dict) else eq for eq in col['equipment']]
            all_ids.extend(eq_ids)
            save_data['columns'].append({
                'id': col['id'], 'title': col['title'],
                'main': col['main'], 'back': col['back'],
                'phone': col['phone'], 'comms': col['comms'],
                'color': col.get('color', '#9e9e9e'),
                'equipment': eq_ids
            })

        with open(FLEET_DATA_PATH, 'w') as f:
            json.dump(save_data, f, indent=2)

        # Non-blocking probe so save returns immediately (SSH calls can take 30s+ each)
        for eq_id in all_ids:
            threading.Thread(target=probe_equipment_health, args=(eq_id,), daemon=True).start()

        log_database('info', 'fleet_data', f'Fleet layout updated and probed by {request.remote_addr}')
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error saving fleet data: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
