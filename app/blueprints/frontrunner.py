"""
app/blueprints/frontrunner.py
==============================
FrontRunner event log API routes:
  /api/frontrunner/events, /api/frontrunner/active-events
"""

import logging

from flask import Blueprint, jsonify
from app.config import BASE_DIR

logger = logging.getLogger(__name__)

bp = Blueprint('frontrunner', __name__, url_prefix='')


@bp.route('/api/frontrunner/events')
def api_frontrunner_events():
    """API endpoint to get FrontRunner event logs (process failures and disk warnings)"""
    try:
        from tools import frontrunner_event_db

        db_path = frontrunner_event_db.get_database_path(BASE_DIR)
        history = frontrunner_event_db.get_event_history(db_path, limit=100)

        return jsonify({
            'success': True,
            'process_events': history['process_events'],
            'disk_events': history['disk_events']
        })

    except Exception as e:
        logger.error(f"Error fetching FrontRunner events: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'process_events': [],
            'disk_events': []
        }), 500


@bp.route('/api/frontrunner/active-events')
def api_frontrunner_active_events():
    """API endpoint to get currently active FrontRunner events"""
    try:
        from tools import frontrunner_event_db

        db_path = frontrunner_event_db.get_database_path(BASE_DIR)
        active = frontrunner_event_db.get_active_events(db_path)

        return jsonify({
            'success': True,
            'process_events': active['process_events'],
            'disk_events': active['disk_events']
        })

    except Exception as e:
        logger.error(f"Error fetching active FrontRunner events: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'process_events': [],
            'disk_events': []
        }), 500
