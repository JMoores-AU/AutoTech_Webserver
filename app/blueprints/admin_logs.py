"""
app/blueprints/admin_logs.py
=============================
Admin log viewer routes:
  /admin/logs, /api/logs/<source>, /api/logs/<source>/stream, /api/logs/<source>/download
"""

import json
import logging
import os
import time
from collections import deque
from typing import Optional

from flask import Blueprint, Response, jsonify, render_template, request, send_file, stream_with_context

from tools.app_logger import LOG_FILES, get_log_directory, get_request_id

logger = logging.getLogger(__name__)

bp = Blueprint('admin_logs', __name__, url_prefix='')

# Map log source keys → filenames (built from tools.app_logger.LOG_FILES)
LOG_SOURCES = dict(LOG_FILES)

LOG_SOURCE_LABELS = {
    'server': 'Server',
    'clients': 'Clients',
    'tools': 'Tools',
    'background': 'Background',
    'security': 'Security',
    'database': 'Database'
}


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def _resolve_log_path(source: str) -> Optional[str]:
    if source not in LOG_SOURCES:
        return None
    log_dir = get_log_directory()
    return os.path.join(log_dir, LOG_SOURCES[source])


def _tail_log_lines(filepath: str, max_lines: int = 200) -> list:
    if not os.path.exists(filepath):
        return []
    max_lines = max(1, min(2000, max_lines))
    lines = deque(maxlen=max_lines)
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            lines.append(line.rstrip('\n'))
    return list(lines)


def _stream_log_lines(filepath: str, initial_lines: int = 200):
    def generate():
        try:
            if os.path.exists(filepath):
                if initial_lines > 0:
                    for line in _tail_log_lines(filepath, initial_lines):
                        payload = json.dumps({"line": line})
                        yield f"data: {payload}\n\n"
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    f.seek(0, os.SEEK_END)
                    while True:
                        line = f.readline()
                        if line:
                            payload = json.dumps({"line": line.rstrip('\n')})
                            yield f"data: {payload}\n\n"
                        else:
                            time.sleep(0.5)
            else:
                payload = json.dumps({"error": "Log file not found"})
                yield f"event: error\ndata: {payload}\n\n"
        except GeneratorExit:
            return
        except Exception as e:
            payload = json.dumps({"error": str(e)})
            yield f"event: error\ndata: {payload}\n\n"
    return generate()


# ==============================================================================
# ROUTES
# ==============================================================================

@bp.route('/admin/logs')
def admin_logs():
    sources = [
        {'key': key, 'label': LOG_SOURCE_LABELS.get(key, key.title())}
        for key in LOG_SOURCES.keys()
    ]
    return render_template('admin_logs.html', sources=sources)


@bp.route('/api/logs/<source>', methods=['GET'])
def api_logs_tail(source: str):
    log_path = _resolve_log_path(source)
    if not log_path:
        return jsonify({"error": "Unknown log source", "request_id": get_request_id()}), 404

    try:
        lines = int(request.args.get('lines', 200))
    except ValueError:
        lines = 200

    return jsonify({
        "source": source,
        "lines": _tail_log_lines(log_path, lines),
        "request_id": get_request_id()
    })


@bp.route('/api/logs/<source>/stream', methods=['GET'])
def api_logs_stream(source: str):
    log_path = _resolve_log_path(source)
    if not log_path:
        return jsonify({"error": "Unknown log source", "request_id": get_request_id()}), 404

    try:
        lines = int(request.args.get('lines', 200))
    except ValueError:
        lines = 200

    headers = {
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no"
    }
    return Response(
        stream_with_context(_stream_log_lines(log_path, lines)),
        mimetype='text/event-stream',
        headers=headers
    )


@bp.route('/api/logs/<source>/download', methods=['GET'])
def api_logs_download(source: str):
    log_path = _resolve_log_path(source)
    if not log_path:
        return jsonify({"error": "Unknown log source", "request_id": get_request_id()}), 404
    if not os.path.exists(log_path):
        return jsonify({"error": "Log file not found", "request_id": get_request_id()}), 404
    return send_file(log_path, as_attachment=True)
