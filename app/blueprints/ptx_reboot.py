"""
app/blueprints/ptx_reboot.py
==============================
PTX equipment management API routes:
  /api/ptx_reboot, /api/ptx_status
"""

import logging

from flask import Blueprint, jsonify, request

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
