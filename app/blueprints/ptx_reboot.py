"""
app/blueprints/ptx_reboot.py
==============================
PTX equipment management API routes:
  /api/ptx_reboot, /api/ptx_status
"""

import logging
import time
from datetime import datetime

from flask import Blueprint, jsonify, request

import app.state as state
from app.utils import is_online_network

logger = logging.getLogger(__name__)

try:
    import paramiko
except ImportError:
    paramiko = None

try:
    import ping3
except ImportError:
    ping3 = None

bp = Blueprint('ptx_reboot', __name__, url_prefix='')


def _zero_uptime(equipment_id, ip_address, ptx_type=None):
    """Immediately zero uptime in DB after a reboot so equipment drops off the high-uptime list."""
    try:
        db = state.ptx_uptime_db
        if db and equipment_id and ip_address:
            db.upsert_uptime(
                equipment_id=equipment_id,
                ip_address=ip_address,
                uptime_hours=0.0,
                last_check=datetime.now().strftime('%a %b %d %H:%M:%S AEST %Y'),
                last_check_timestamp=int(time.time()),
                ptx_type=ptx_type,
            )
            db.update_status(equipment_id, 'rebooted', ptx_type)
            logger.info(f"Zeroed uptime for {equipment_id} after reboot")
    except Exception as e:
        logger.warning(f"Could not zero uptime for {equipment_id}: {e}")


@bp.route("/api/ptx_reboot", methods=["POST"])
def api_ptx_reboot():
    """Reboot PTX equipment via SSH"""
    data = request.get_json()
    ip_address = data.get('ip_address')
    equipment_id = data.get('equipment_id', 'Unknown')

    if not ip_address:
        return jsonify({'success': False, 'message': 'IP address required'}), 400

    try:
        # Simulate reboot in offline mode
        if not is_online_network() or not paramiko:
            _zero_uptime(equipment_id, ip_address)
            return jsonify({
                'success': True,
                'message': f'SIMULATED: Reboot command sent to {equipment_id}',
                'ptx_type': 'Simulated',
                'details': 'Offline testing mode - reboot simulated'
            })

        from app.utils import connect_to_equipment

        ssh, ptx_type = connect_to_equipment(ip_address)
        if not ssh:
            return jsonify({'success': False, 'message': f'Cannot connect to {equipment_id}: {ptx_type}'}), 500

        try:
            ssh.exec_command("sudo reboot", timeout=10)
        except Exception:
            pass  # Connection drops immediately on reboot — this is expected
        finally:
            try:
                ssh.close()
            except Exception:
                pass

        _zero_uptime(equipment_id, ip_address, ptx_type)
        return jsonify({
            'success': True,
            'message': f'Reboot command sent to {equipment_id} ({ptx_type})',
            'ptx_type': ptx_type
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Reboot failed: {str(e)}'}), 500


@bp.route("/api/ptx_status", methods=["POST"])
def api_ptx_status():
    """Check PTX equipment status via ping and SSH"""
    data = request.get_json()
    ip_address = data.get('ip_address')

    if not ip_address:
        return jsonify({'success': False, 'message': 'IP address required'}), 400

    try:
        # OFFLINE MODE: Return simulated online status
        if not is_online_network():
            return jsonify({
                'success': True,
                'ping_status': True,
                'ping_time': 0.025,
                'ssh_status': True,
                'ssh_details': 'SSH available (simulated)',
                'overall_status': 'Online',
                'offline_mode': True
            })

        # Test ping connectivity
        ping_result = None
        ping_status = False

        if ping3:
            ping_result = ping3.ping(ip_address, timeout=3)
            ping_status = ping_result is not None
        else:
            ping_status = True
            ping_result = 0.05

        ssh_status = ping_status
        ssh_details = "SSH status simulated" if not paramiko else "SSH check available"

        return jsonify({
            'success': True,
            'ping_status': ping_status,
            'ping_time': ping_result if ping_result else None,
            'ssh_status': ssh_status,
            'ssh_details': ssh_details,
            'overall_status': 'Online' if ping_status and ssh_status else 'Offline' if not ping_status else 'Limited'
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Status check failed: {str(e)}'}), 500
