"""
app/blueprints/ptx_uptime.py
==============================
PTX Uptime tool, database API, and checker routes:
  handle_ptx_uptime(), handle_frontrunner_status() (helpers for run_tool)
  /ptx-uptime-csv
  /api/ptx/db/sync, /api/ptx/db/stats, /api/ptx/db/reboot-log,
  /api/ptx/db/reboot-history, /api/ptx/db/update-status
  /api/ptx/uptime-checker/start, /api/ptx/uptime-checker/stop,
  /api/ptx/uptime-checker/status, /api/ptx/uptime-checker/check-single
"""

import csv
import io
import logging
import os
import threading
import time
from datetime import datetime, timedelta

from flask import (Blueprint, Response, flash, jsonify, redirect,
                   render_template, request, session, url_for)

import app.state as state
from app.background_tasks import ptx_uptime_checker_worker
from app.config import BASE_DIR, GATEWAY_IP, MMS_SERVER
from app.utils import check_ptx_reachable, get_ptx_uptime, is_online_network

logger = logging.getLogger(__name__)

try:
    from tools import ptx_uptime as ptx_uptime_tool
except ImportError:
    ptx_uptime_tool = None

try:
    from tools import frontrunner_status as frontrunner_status_tool
except ImportError:
    frontrunner_status_tool = None

bp = Blueprint('ptx_uptime', __name__, url_prefix='')


# ==============================================================================
# HELPERS (called by run_tool in main.py/dashboard blueprint)
# ==============================================================================

def handle_ptx_uptime():
    """Handle PTX Uptime tool — renders immediately from DB, JS triggers background sync."""
    try:
        online = is_online_network()

        ptx_uptime_db = state.ptx_uptime_db

        # Determine whether JS should auto-trigger a background sync on page load
        db_count = ptx_uptime_db.get_record_count()
        last_live_sync = ptx_uptime_db.get_sync_metadata('last_live_sync')
        auto_sync = False
        if online:
            if db_count == 0 or not last_live_sync:
                auto_sync = True
            else:
                try:
                    last_sync_dt = datetime.fromisoformat(last_live_sync)
                    auto_sync = (datetime.now() - last_sync_dt) > timedelta(minutes=10)
                except ValueError:
                    auto_sync = True
        # ?refresh= param forces a sync via JS (same as auto_sync=True)
        if 'refresh' in request.args or request.args.get('sync', '').lower() == 'true':
            auto_sync = online

        high_uptime_equipment = ptx_uptime_db.get_high_uptime(min_days=3)
        statistics = ptx_uptime_db.get_statistics()

        if not high_uptime_equipment:
            logger.info("Using sample PTX uptime data for testing")
            high_uptime_equipment = [
                {'timestamp': 1769006409, 'ip': '10.110.20.10', 'equipment_id': 'ROM1', 'uptime_hours': 151.05, 'uptime_days': 6.3, 'last_check': 'Thu Jan 22 00:40:09 AEST 2026'},
                {'timestamp': 1769004985, 'ip': '10.110.20.11', 'equipment_id': 'ROM2', 'uptime_hours': 150.65, 'uptime_days': 6.3, 'last_check': 'Thu Jan 22 00:16:25 AEST 2026'},
                {'timestamp': 1768977869, 'ip': '10.110.21.151', 'equipment_id': 'TRD410', 'uptime_hours': 195.80, 'uptime_days': 8.2, 'last_check': 'Wed Jan 21 16:44:29 AEST 2026'},
                {'timestamp': 1769001329, 'ip': '10.110.21.157', 'equipment_id': 'TRD498', 'uptime_hours': 169.65, 'uptime_days': 7.1, 'last_check': 'Wed Jan 21 23:15:29 AEST 2026'},
                {'timestamp': 1768992242, 'ip': '10.110.21.130', 'equipment_id': 'TRD409', 'uptime_hours': 162.27, 'uptime_days': 6.8, 'last_check': 'Wed Jan 21 20:44:02 AEST 2026'},
                {'timestamp': 1768973183, 'ip': '10.110.21.229', 'equipment_id': 'EL20', 'uptime_hours': 115.22, 'uptime_days': 4.8, 'last_check': 'Wed Jan 21 15:26:23 AEST 2026'},
                {'timestamp': 1768966923, 'ip': '10.110.21.185', 'equipment_id': 'EXD265', 'uptime_hours': 109.48, 'uptime_days': 4.6, 'last_check': 'Wed Jan 21 13:42:03 AEST 2026'},
                {'timestamp': 1768948919, 'ip': '10.110.21.196', 'equipment_id': 'DZ32NPE', 'uptime_hours': 137.42, 'uptime_days': 5.7, 'last_check': 'Wed Jan 21 08:41:59 AEST 2026'},
            ]
            statistics = {
                'total_equipment': len(high_uptime_equipment),
                'avg_uptime': 140,
                'max_uptime': 195.80,
                'high_uptime_count': len(high_uptime_equipment)
            }

        def ensure_display_timestamp(row: dict) -> dict:
            ts = row.get('timestamp') or 0
            if not ts and ptx_uptime_tool:
                ts = ptx_uptime_tool.parse_last_check_timestamp(row.get('last_check'))
            if not ts and row.get('last_updated'):
                try:
                    ts = int(datetime.fromisoformat(row['last_updated']).timestamp())
                except ValueError:
                    ts = 0
            if not ts:
                ts = int(time.time())
            row['display_ts'] = ts
            return row

        high_uptime_equipment = [ensure_display_timestamp(dict(eq)) for eq in high_uptime_equipment]

        last_sync = ptx_uptime_db.get_sync_metadata('last_html_sync')

        ptx_data = {
            'tool_name': 'PTX Uptime',
            'online': online,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'gateway_ip': GATEWAY_IP,
            'high_uptime_equipment': high_uptime_equipment,
            'statistics': statistics,
            'last_sync': last_sync,
            'mode': 'reference' if not online else 'live',
            'auto_sync': auto_sync,
        }

        return render_template('ptx_uptime.html', **ptx_data)

    except Exception as e:
        logger.error(f"PTX Uptime error: {e}")
        flash(f"PTX Uptime failed: {e}", "error")
        return redirect(url_for('dashboard.dashboard'))


def handle_frontrunner_status():
    """Handle FrontRunner Status tool."""
    try:
        online = is_online_network()
        result = None

        if online:
            try:
                from tools import frontrunner_monitor
                result = frontrunner_monitor.get_status(BASE_DIR)
                if not result or not result.get('success'):
                    logger.warning("Background monitor cache unavailable, using direct connection")
                    result = None
            except Exception as e:
                logger.warning(f"Could not read monitor cache: {e}")
                result = None

        if result is None:
            FR_PASSWORD = "M0dul1r@GRM2"
            if frontrunner_status_tool:
                result = frontrunner_status_tool.run(password=FR_PASSWORD, offline_mode=not online, enable_logging=False)
                if online and not result.get('success'):
                    logger.warning("FrontRunner live status failed (%s); falling back to offline snapshot", result.get('error'))
                    fallback = frontrunner_status_tool.run(password=FR_PASSWORD, offline_mode=True, enable_logging=False)
                    fallback['mode'] = 'offline_fallback'
                    fallback['fallback_reason'] = result.get('error')
                    result = fallback
            else:
                result = {
                    'success': False,
                    'error': 'FrontRunner Status tool not available',
                    'report_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'mode': 'error'
                }

        return render_template('frontrunner_status.html', result=result, online=online)

    except Exception as e:
        logger.error(f"FrontRunner Status error: {e}")
        flash(f"FrontRunner Status failed: {e}", "error")
        return redirect(url_for('dashboard.dashboard'))


# ==============================================================================
# BACKGROUND SYNC HELPER
# ==============================================================================

def _run_ptx_sync_background():
    """Background thread worker for PTX DB sync. Updates state.ptx_db_sync when done."""
    try:
        ptx_uptime_db = state.ptx_uptime_db
        added = 0
        updated = 0

        if is_online_network() and ptx_uptime_tool:
            result = ptx_uptime_tool.run(password=MMS_SERVER['password'])
            if not result.get('success'):
                state.ptx_db_sync['last_result'] = {
                    'success': False,
                    'error': result.get('error', 'Live sync failed')
                }
                return

            existing_ids = {row['equipment_id'] for row in ptx_uptime_db.get_all_uptime(min_hours=0)}
            for equipment in result.get('equipment_list', []):
                equipment_id = equipment.get('equipment_id')
                ip_address = equipment.get('ip')
                if not equipment_id or not ip_address:
                    continue
                if equipment_id in existing_ids:
                    updated += 1
                else:
                    added += 1
                    existing_ids.add(equipment_id)

                ts = equipment.get('timestamp') or 0
                if not ts and ptx_uptime_tool:
                    ts = ptx_uptime_tool.parse_last_check_timestamp(equipment.get('last_check'))
                if not ts:
                    ts = int(time.time())

                ptx_uptime_db.upsert_uptime(
                    equipment_id=equipment_id,
                    ip_address=ip_address,
                    uptime_hours=equipment.get('uptime_hours', 0),
                    last_check=equipment.get('last_check'),
                    last_check_timestamp=ts
                )
            ptx_uptime_db.set_sync_metadata('last_live_sync', datetime.now().isoformat())
            ptx_uptime_db.set_sync_metadata('last_live_path', result.get('file_path', ''))

        else:
            report_path = os.path.join(BASE_DIR, 'backups', 'PTX_Uptime_Report.html')
            if not os.path.exists(report_path):
                state.ptx_db_sync['last_result'] = {
                    'success': False,
                    'error': 'Offline and no PTX_Uptime_Report.html found',
                }
                return
            updated, added = ptx_uptime_db.sync_from_html_report(report_path)

        state.ptx_db_sync['last_result'] = {
            'success': True,
            'records_added': added,
            'records_updated': updated,
            'total_records': ptx_uptime_db.get_record_count(),
            'sync_time': datetime.now().isoformat(),
        }
        logger.info(f"PTX DB sync complete: {added} added, {updated} updated")

    except Exception as e:
        logger.error(f"Background PTX DB sync error: {e}")
        state.ptx_db_sync['last_result'] = {'success': False, 'error': str(e)}
    finally:
        state.ptx_db_sync['running'] = False
        state.ptx_db_sync['finished_at'] = datetime.now().isoformat()


# ==============================================================================
# ROUTES
# ==============================================================================

@bp.route('/ptx-uptime-csv')
def ptx_uptime_csv():
    """Download PTX Uptime data as CSV."""
    try:
        ptx_uptime_db = state.ptx_uptime_db
        equipment_data = ptx_uptime_db.get_all_uptime(min_hours=0)

        if not equipment_data:
            flash("No PTX uptime data available. Please sync the database first.", "warning")
            return redirect(url_for('dashboard.run_tool', tool_name='PTX Uptime'))

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Equipment ID', 'IP Address', 'Uptime (Hours)', 'Uptime (Days)', 'Last Check', 'Timestamp', 'PTX Type', 'Status'])

        for eq in equipment_data:
            writer.writerow([
                eq.get('equipment_id', ''),
                eq.get('ip', ''),
                eq.get('uptime_hours', 0),
                eq.get('uptime_days', 0),
                eq.get('last_check', ''),
                eq.get('timestamp', ''),
                eq.get('ptx_type', ''),
                eq.get('last_status', '')
            ])

        output.seek(0)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename=PTX_Uptime_Report_{timestamp}.csv'}
        )

    except Exception as e:
        logger.error(f"PTX Uptime CSV error: {e}")
        flash(f"CSV download failed: {e}", "error")
        return redirect(url_for('dashboard.run_tool', tool_name='PTX Uptime'))


@bp.route('/api/ptx/db/sync', methods=['POST'])
def api_ptx_db_sync():
    """Start async PTX uptime database sync. Returns immediately; poll /status for result."""
    try:
        if state.ptx_db_sync['running']:
            return jsonify({'success': True, 'message': 'Sync already in progress', 'already_running': True})

        state.ptx_db_sync['running'] = True
        state.ptx_db_sync['started_at'] = datetime.now().isoformat()
        state.ptx_db_sync['finished_at'] = None
        state.ptx_db_sync['last_result'] = None

        threading.Thread(target=_run_ptx_sync_background, daemon=True).start()
        return jsonify({'success': True, 'message': 'Sync started'})

    except Exception as e:
        logger.error(f"PTX DB sync error: {e}")
        state.ptx_db_sync['running'] = False
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/ptx/db/sync/status')
def api_ptx_db_sync_status():
    """Return current PTX DB sync state for the browser to poll."""
    try:
        sync = state.ptx_db_sync
        return jsonify({
            'success': True,
            'running': sync['running'],
            'last_result': sync['last_result'],
            'started_at': sync['started_at'],
            'finished_at': sync['finished_at'],
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/ptx/db/stats')
def api_ptx_db_stats():
    """Get PTX uptime database statistics."""
    try:
        ptx_uptime_db = state.ptx_uptime_db
        stats = ptx_uptime_db.get_statistics()
        stats['last_sync'] = ptx_uptime_db.get_sync_metadata('last_html_sync')
        stats['total_records'] = ptx_uptime_db.get_record_count()
        return jsonify({'success': True, 'statistics': stats})

    except Exception as e:
        logger.error(f"PTX DB stats error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/ptx/db/reboot-log', methods=['POST'])
def api_ptx_log_reboot():
    """Log a PTX reboot event to the database."""
    try:
        ptx_uptime_db = state.ptx_uptime_db
        data = request.get_json()
        equipment_id = data.get('equipment_id')
        ip_address = data.get('ip_address')
        uptime_before = data.get('uptime_before')
        success = data.get('success', True)
        notes = data.get('notes', '')

        if not equipment_id or not ip_address:
            return jsonify({'success': False, 'error': 'Missing equipment_id or ip_address'}), 400

        result = ptx_uptime_db.log_reboot(
            equipment_id=equipment_id,
            ip_address=ip_address,
            uptime_before=uptime_before,
            success=success,
            rebooted_by=session.get('username', 'web_user'),
            notes=notes
        )
        return jsonify({'success': result})

    except Exception as e:
        logger.error(f"PTX reboot log error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/ptx/db/reboot-history')
def api_ptx_reboot_history():
    """Get PTX reboot history."""
    try:
        ptx_uptime_db = state.ptx_uptime_db
        equipment_id = request.args.get('equipment_id', None)
        limit = int(request.args.get('limit', 50))

        history = ptx_uptime_db.get_reboot_history(
            equipment_id=equipment_id if equipment_id else None,
            limit=limit
        )
        return jsonify({'success': True, 'history': history, 'count': len(history)})

    except Exception as e:
        logger.error(f"PTX reboot history error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/ptx/db/update-status', methods=['POST'])
def api_ptx_update_status():
    """Update PTX equipment status in database."""
    try:
        ptx_uptime_db = state.ptx_uptime_db
        data = request.get_json()
        equipment_id = data.get('equipment_id')
        status = data.get('status')
        ptx_type = data.get('ptx_type')

        if not equipment_id or not status:
            return jsonify({'success': False, 'error': 'Missing equipment_id or status'}), 400

        result = ptx_uptime_db.update_status(
            equipment_id=equipment_id,
            status=status,
            ptx_type=ptx_type
        )
        return jsonify({'success': result})

    except Exception as e:
        logger.error(f"PTX update status error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/ptx/uptime-checker/start', methods=['POST'])
def api_start_ptx_uptime_checker():
    """Start the background PTX uptime checker."""
    try:
        if not is_online_network():
            return jsonify({
                'success': False,
                'error': 'PTX uptime checker requires online network connection'
            }), 400

        checker = state.ptx_uptime_checker
        if checker['running']:
            return jsonify({
                'success': False,
                'error': 'PTX uptime checker is already running',
                'status': checker['status']
            }), 400

        data = request.get_json() or {}
        interval = data.get('interval_minutes', 30)
        checker['interval_minutes'] = max(5, min(120, interval))

        checker['stop_event'].clear()
        checker['running'] = True
        checker['thread'] = threading.Thread(target=ptx_uptime_checker_worker, daemon=True)
        checker['thread'].start()

        return jsonify({
            'success': True,
            'message': 'PTX uptime checker started',
            'interval_minutes': checker['interval_minutes']
        })

    except Exception as e:
        logger.error(f"Error starting PTX uptime checker: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/ptx/uptime-checker/stop', methods=['POST'])
def api_stop_ptx_uptime_checker():
    """Stop the background PTX uptime checker."""
    try:
        checker = state.ptx_uptime_checker
        if not checker['running']:
            return jsonify({'success': False, 'error': 'PTX uptime checker is not running'}), 400

        checker['stop_event'].set()
        return jsonify({'success': True, 'message': 'Stop signal sent to PTX uptime checker'})

    except Exception as e:
        logger.error(f"Error stopping PTX uptime checker: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/ptx/uptime-checker/status')
def api_ptx_uptime_checker_status():
    """Get the current status of the PTX uptime checker."""
    try:
        checker = state.ptx_uptime_checker
        return jsonify({
            'success': True,
            'running': checker['running'],
            'status': checker['status'],
            'current_equipment': checker['current_equipment'],
            'total_equipment': checker['total_equipment'],
            'checked_count': checker['checked_count'],
            'online_count': checker['online_count'],
            'offline_count': checker['offline_count'],
            'error_count': checker['error_count'],
            'last_cycle_start': checker['last_cycle_start'],
            'last_cycle_end': checker['last_cycle_end'],
            'next_cycle': checker['next_cycle'],
            'interval_minutes': checker['interval_minutes']
        })

    except Exception as e:
        logger.error(f"Error getting PTX uptime checker status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/ptx/uptime-checker/check-single', methods=['POST'])
def api_check_single_ptx_uptime():
    """Check uptime for a single PTX equipment."""
    try:
        if not is_online_network():
            return jsonify({'success': False, 'error': 'Online network connection required'}), 400

        ptx_uptime_db = state.ptx_uptime_db
        data = request.get_json()
        ip_address = data.get('ip_address')
        equipment_id = data.get('equipment_id')

        if not ip_address:
            return jsonify({'success': False, 'error': 'IP address required'}), 400

        if not check_ptx_reachable(ip_address, timeout=3.0):
            if equipment_id:
                ptx_uptime_db.update_status(equipment_id, 'offline')
            return jsonify({
                'success': True,
                'reachable': False,
                'status': 'offline',
                'message': f'{ip_address} is not reachable'
            })

        result = get_ptx_uptime(ip_address)

        if result['success']:
            if equipment_id:
                ptx_type = result.get('ptx_type') or 'PTX'
                ptx_uptime_db.upsert_uptime(
                    equipment_id=equipment_id,
                    ip_address=ip_address,
                    uptime_hours=result['uptime_hours'],
                    last_check=datetime.now().strftime('%a %b %d %H:%M:%S %Z %Y'),
                    last_check_timestamp=int(time.time()),
                    ptx_type=ptx_type
                )
                ptx_uptime_db.update_status(equipment_id, 'online', ptx_type)

            return jsonify({
                'success': True,
                'reachable': True,
                'status': 'online',
                'uptime_hours': result['uptime_hours'],
                'uptime_days': round(result['uptime_hours'] / 24, 1),
                'uptime_raw': result['uptime_raw'],
                'ptx_type': result.get('ptx_type')
            })
        else:
            if equipment_id:
                ptx_uptime_db.update_status(equipment_id, 'unknown')
            return jsonify({
                'success': True,
                'reachable': True,
                'status': 'error',
                'error': result.get('error', 'Unknown error')
            })

    except Exception as e:
        logger.error(f"Error checking single PTX uptime: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
