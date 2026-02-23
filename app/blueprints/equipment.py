"""
app/blueprints/equipment.py
============================
Equipment management API routes:
  /api/find-equipment-ip
  /api/equipment/cache, /api/equipment/cache/stats,
  /api/equipment/cache/<equipment_name>
  /api/equipment (GET, POST), /api/equipment/<name> (DELETE)
  /api/equipment/import-ip-list
  /api/equipment/updater/start, /api/equipment/updater/stop,
  /api/equipment/updater/status
"""

import logging
import os
import platform
import sqlite3
import subprocess
import threading

from flask import Blueprint, jsonify, request, session

import app.state as state
from app.background_tasks import background_update_worker
from app.config import CLIENT_PLINK_PATH, IP_LIST_PATH
from app.utils import is_online_network
from tools.app_logger import log_database
from tools.equipment_db import (
    get_all_equipment, get_database_stats, get_equipment,
    get_update_progress, parse_ip_list_file,
    save_equipment, search_equipment as search_equipment_db
)

logger = logging.getLogger(__name__)

bp = Blueprint('equipment', __name__, url_prefix='')


@bp.route('/api/find-equipment-ip', methods=['POST'])
def api_find_equipment_ip():
    """Find equipment IP address for terminal display."""
    try:
        data = request.get_json()
        equipment = data.get('equipment_id', '').strip().upper()

        if not equipment:
            return jsonify({'success': False, 'error': 'Equipment ID is required'})

        mms_server = '10.110.19.107'
        mms_user = 'mms'
        mms_password = session.get('mms_password', '')

        if not mms_password:
            return jsonify({'success': False, 'error': 'MMS password not found. Please log in again.'})

        plink_path = CLIENT_PLINK_PATH
        if not os.path.exists(plink_path):
            return jsonify({
                'success': False,
                'error': f'plink.exe not found at: {plink_path}. Install AutoTech Client or check USB connection.'
            })

        ip_finder_cmd = f"/home/mms/bin/remote_check/Random/MySQL/ip_export.sh {equipment}"

        ip_lookup_plink = [
            plink_path, '-batch', '-t',
            f'{mms_user}@{mms_server}',
            '-pw', mms_password,
            ip_finder_cmd
        ]

        result = subprocess.run(
            ip_lookup_plink,
            capture_output=True, text=True, timeout=30,
            creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == 'Windows' else 0
        )

        equipment_ip = None
        equipment_status = 'unknown'
        output_lines = []

        for line in result.stdout.split('\n'):
            if line.strip():
                output_lines.append(line)
                if 'PTX IP is:' in line:
                    equipment_ip = line.split('PTX IP is:')[1].strip()
                elif '|' in line and not line.startswith('+') and 'network_ip' not in line:
                    parts = [p.strip() for p in line.split('|') if p.strip()]
                    if len(parts) >= 4:
                        equipment_ip = parts[3]
                if 'Vehicle is Online' in line or 'Equipment is Online' in line:
                    equipment_status = 'ONLINE'
                elif 'Vehicle is Offline' in line or 'Equipment is Offline' in line:
                    equipment_status = 'OFFLINE'

        formatted_output = '\n'.join(output_lines)
        if equipment_ip:
            formatted_output += f'\n\n[RESULT] Equipment: {equipment}\n'
            formatted_output += f'[RESULT] IP Address: {equipment_ip}\n'
            formatted_output += f'[RESULT] Status: {equipment_status}'
        else:
            formatted_output += f'\n\n[ERROR] Could not find IP address for equipment: {equipment}'

        return jsonify({
            'success': True,
            'output': formatted_output,
            'equipment_ip': equipment_ip,
            'status': equipment_status
        })

    except subprocess.TimeoutExpired:
        return jsonify({'success': False, 'error': 'Request timed out. MMS server may be unreachable.'})
    except Exception as e:
        logger.error(f"Error finding equipment IP: {str(e)}")
        return jsonify({'success': False, 'error': f'Error: {str(e)}'})


@bp.route('/api/equipment/cache', methods=['GET'])
def api_equipment_cache():
    """Get all cached equipment from database."""
    try:
        db_path = state.EQUIPMENT_DB_PATH
        if not db_path:
            return jsonify({'success': False, 'error': 'Equipment database not initialized'})

        limit = request.args.get('limit', 100, type=int)
        search_term = request.args.get('search', '').strip()

        if search_term:
            equipment_list = search_equipment_db(db_path, search_term, limit)
        else:
            equipment_list = get_all_equipment(db_path, limit)

        return jsonify({'success': True, 'count': len(equipment_list), 'equipment': equipment_list})

    except Exception as e:
        logger.error(f"Error getting equipment cache: {e}")
        return jsonify({'success': False, 'error': str(e)})


@bp.route('/api/equipment/cache/stats', methods=['GET'])
def api_equipment_cache_stats():
    """Get statistics about the equipment cache database."""
    try:
        db_path = state.EQUIPMENT_DB_PATH
        if not db_path:
            return jsonify({'success': False, 'error': 'Equipment database not initialized'})

        stats = get_database_stats(db_path)
        stats['database_path'] = db_path
        return jsonify({'success': True, 'stats': stats})

    except Exception as e:
        logger.error(f"Error getting database stats: {e}")
        return jsonify({'success': False, 'error': str(e)})


@bp.route('/api/equipment/cache/<equipment_name>', methods=['GET'])
def api_equipment_cache_single(equipment_name):
    """Get a single equipment record from the cache."""
    try:
        db_path = state.EQUIPMENT_DB_PATH
        if not db_path:
            return jsonify({'success': False, 'error': 'Equipment database not initialized'})

        equipment = get_equipment(db_path, equipment_name)
        if equipment:
            return jsonify({'success': True, 'equipment': equipment})
        else:
            return jsonify({'success': False, 'error': f'Equipment {equipment_name} not found in cache'})

    except Exception as e:
        logger.error(f"Error getting equipment {equipment_name}: {e}")
        return jsonify({'success': False, 'error': str(e)})


@bp.route('/api/equipment', methods=['POST'])
def api_equipment_create():
    """Create or update an equipment record in the database."""
    try:
        db_path = state.EQUIPMENT_DB_PATH
        if not db_path:
            return jsonify({'success': False, 'error': 'Equipment database not initialized'}), 500

        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Request body must be JSON'}), 400

        equipment_name = data.get('equipment_name') or data.get('name')
        if not equipment_name:
            return jsonify({'success': False, 'error': 'equipment_name is required'}), 400

        result = save_equipment(
            db_path,
            equipment_name=equipment_name,
            oid=data.get('oid'),
            cid=data.get('cid'),
            profile=data.get('profile'),
            network_ip=data.get('network_ip'),
            avi_ip=data.get('avi_ip'),
            ptx_model=data.get('ptx_model'),
            status=data.get('status')
        )

        if result:
            log_database('info', 'equipment_create', f'Equipment created/updated: {equipment_name}')
            return jsonify({
                'success': True,
                'message': f'Equipment {equipment_name} saved successfully',
                'equipment_name': equipment_name.upper().strip()
            }), 201
        else:
            return jsonify({'success': False, 'error': f'Failed to save equipment {equipment_name}'}), 500

    except Exception as e:
        logger.error(f"Error creating equipment: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/equipment/<equipment_name>', methods=['DELETE'])
def api_equipment_delete(equipment_name):
    """Delete an equipment record from the database by name."""
    try:
        db_path = state.EQUIPMENT_DB_PATH
        if not db_path:
            return jsonify({'success': False, 'error': 'Equipment database not initialized'}), 500

        conn = sqlite3.connect(db_path)
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA busy_timeout=5000')
        cursor = conn.cursor()
        equipment_name_upper = equipment_name.upper().strip()
        cursor.execute('DELETE FROM equipment_cache WHERE equipment_name = ?', (equipment_name_upper,))
        deleted = cursor.rowcount
        conn.commit()
        conn.close()

        if deleted > 0:
            log_database('info', 'equipment_delete', f'Equipment deleted: {equipment_name_upper}')
            return jsonify({'success': True, 'message': f'Equipment {equipment_name_upper} deleted'})
        else:
            return jsonify({'success': False, 'error': f'Equipment {equipment_name_upper} not found'}), 404

    except Exception as e:
        logger.error(f"Error deleting equipment {equipment_name}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/equipment', methods=['GET'])
def api_equipment_list():
    """Get all equipment from the database."""
    try:
        db_path = state.EQUIPMENT_DB_PATH
        if not db_path:
            return jsonify({'success': False, 'error': 'Equipment database not initialized'}), 500

        limit = request.args.get('limit', 100, type=int)
        search_term = request.args.get('search', '').strip()

        if search_term:
            equipment_list = search_equipment_db(db_path, search_term, limit)
        else:
            equipment_list = get_all_equipment(db_path, limit)

        return jsonify({'success': True, 'count': len(equipment_list), 'equipment': equipment_list})

    except Exception as e:
        logger.error(f"Error listing equipment: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/equipment/import-ip-list', methods=['POST'])
def api_import_ip_list():
    """Import equipment from IP_list.dat file into the database."""
    try:
        db_path = state.EQUIPMENT_DB_PATH
        if not db_path:
            return jsonify({'success': False, 'error': 'Equipment database not initialized'})

        if not os.path.exists(IP_LIST_PATH):
            return jsonify({'success': False, 'error': f'IP_list.dat not found at {IP_LIST_PATH}'})

        result = parse_ip_list_file(db_path, IP_LIST_PATH)
        return jsonify({
            'success': result['success'],
            'imported': result['imported'],
            'updated': result['updated'],
            'skipped': result['skipped'],
            'total_lines': result['total_lines'],
            'errors': result['errors']
        })

    except Exception as e:
        logger.error(f"Error importing IP list: {e}")
        return jsonify({'success': False, 'error': str(e)})


@bp.route('/api/equipment/updater/start', methods=['POST'])
def api_start_background_updater():
    """Start the background equipment updater."""
    try:
        db_path = state.EQUIPMENT_DB_PATH
        updater = state.background_updater

        if not db_path:
            return jsonify({'success': False, 'error': 'Equipment database not initialized'})

        if not is_online_network():
            return jsonify({'success': False, 'error': 'Cannot start updater - not on online network'})

        if updater['running']:
            return jsonify({'success': False, 'error': 'Background updater is already running'})

        data = request.get_json() or {}
        delay = data.get('delay_seconds', 5)
        updater['delay_seconds'] = max(2, min(60, delay))

        updater['stop_event'].clear()
        updater['running'] = True
        updater['thread'] = threading.Thread(target=background_update_worker, daemon=True)
        updater['thread'].start()

        return jsonify({
            'success': True,
            'message': 'Background updater started',
            'delay_seconds': updater['delay_seconds']
        })

    except Exception as e:
        logger.error(f"Error starting background updater: {e}")
        return jsonify({'success': False, 'error': str(e)})


@bp.route('/api/equipment/updater/stop', methods=['POST'])
def api_stop_background_updater():
    """Stop the background equipment updater."""
    try:
        updater = state.background_updater
        if not updater['running']:
            return jsonify({'success': False, 'error': 'Background updater is not running'})

        updater['stop_event'].set()
        return jsonify({'success': True, 'message': 'Stop signal sent to background updater'})

    except Exception as e:
        logger.error(f"Error stopping background updater: {e}")
        return jsonify({'success': False, 'error': str(e)})


@bp.route('/api/equipment/updater/status', methods=['GET'])
def api_background_updater_status():
    """Get the current status of the background equipment updater."""
    try:
        db_path = state.EQUIPMENT_DB_PATH
        updater = state.background_updater
        progress = get_update_progress(db_path) if db_path else {}

        return jsonify({
            'success': True,
            'running': updater['running'],
            'status': updater['status'],
            'current_equipment': updater['current_equipment'],
            'processed_count': updater['processed_count'],
            'error_count': updater['error_count'],
            'last_update': updater['last_update'],
            'delay_seconds': updater['delay_seconds'],
            'progress': progress
        })

    except Exception as e:
        logger.error(f"Error getting updater status: {e}")
        return jsonify({'success': False, 'error': str(e)})
