"""
app/blueprints/usb_client.py
==============================
USB scanning/launching and AutoTech client installer routes:
  /api/usb/scan/<tool_id>, /api/usb/launch/<tool_id>, /api/usb/status,
  /api/usb/scan, /usb_tool, /api/client/installer, /api/client/test,
  /download-client-setup, /download-client-package, /live-install-client,
  /api/check-client-installed, /api/register-client
"""

import logging
import os
import zipfile
from datetime import datetime
from io import BytesIO

from flask import Blueprint, jsonify, render_template, request, send_file

from app.config import GATEWAY_IP
from app.utils import get_autotech_client_folder, is_online_network, login_required
from tools.app_logger import format_client_registration, log_client

logger = logging.getLogger(__name__)

bp = Blueprint('usb_client', __name__, url_prefix='')


# ==============================================================================
# USB SCAN & LAUNCH
# ==============================================================================

@bp.route("/api/usb/scan/<tool_id>")
@login_required
def api_usb_scan(tool_id):
    """Scan USB drives for a specific tool (camstudio or playback)."""
    def _normalize_scan_result(result: dict) -> dict:
        if not isinstance(result, dict):
            return {'found': False, 'error': 'Invalid scan result type', 'details': {}, 'drives': []}

        letter = None
        try:
            letter = result.get('details', {}).get('drive', {}).get('letter')
        except Exception:
            letter = None

        if not letter:
            letter = result.get('drive_letter') or result.get('letter')

        if not letter and isinstance(result.get('drive'), str):
            d = result['drive'].strip()
            letter = d[0].upper() if d else None

        drives = result.get('drives')
        if not drives:
            drives = result.get('usb_drives') or result.get('available_drives') or []

        if not letter and isinstance(drives, list) and drives:
            first = drives[0]
            if isinstance(first, dict):
                d = first.get('letter') or first.get('drive_letter') or first.get('drive')
                if isinstance(d, str) and d:
                    letter = d.strip()[0].upper()

        found = result.get('found')
        if found is None:
            found = bool(result.get('success')) and bool(letter)

        normalized = {
            'found': bool(found),
            'details': {'drive': {'letter': letter}},
            'drives': drives if isinstance(drives, list) else [],
        }

        if 'error' in result and result['error']:
            normalized['error'] = result['error']
        if 'message' in result and result['message']:
            normalized['message'] = result['message']
        if 'path' in result and result['path']:
            normalized['path'] = result['path']

        return normalized

    try:
        if tool_id == 'camstudio':
            from tools.camstudio_usb import scan
            raw = scan()
        elif tool_id == 'playback':
            from tools.playback_usb import scan
            raw = scan()
        else:
            return jsonify({'found': False, 'error': f'Unknown tool: {tool_id}', 'details': {}, 'drives': []}), 400

        return jsonify(_normalize_scan_result(raw))

    except Exception as e:
        logger.error(f"USB scan error for {tool_id}: {e}")
        return jsonify({'found': False, 'error': str(e), 'details': {}, 'drives': []}), 500


@bp.route("/api/usb/launch/<tool_id>", methods=["POST"])
def api_usb_launch(tool_id):
    """Launch a USB tool (camstudio or playback)."""
    try:
        if tool_id == 'camstudio':
            from tools.camstudio_usb import launch
            success, message = launch()
        elif tool_id == 'playback':
            from tools.playback_usb import launch
            success, message = launch()
        else:
            return jsonify({'success': False, 'message': f'Unknown tool: {tool_id}'}), 400

        return jsonify({'success': success, 'message': message})

    except Exception as e:
        logger.error(f"USB launch error for {tool_id}: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route("/api/usb/status")
def api_usb_status():
    """Get status of all USB drives and tools."""
    try:
        from tools.usb_tools import scan_usb_status
        status = scan_usb_status()
        return jsonify(status)
    except Exception as e:
        logger.error(f"USB status error: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/api/usb/scan')
def api_usb_scan_all():
    """Scan all USB drives for AutoTech client package."""
    try:
        from tools.usb_tools import scan_usb_status
        status = scan_usb_status()
        return jsonify(status)
    except Exception as e:
        logger.error(f"USB scan error: {e}")
        return jsonify({'error': str(e)}), 500


# ==============================================================================
# USB TOOL PAGE
# ==============================================================================

@bp.route('/usb_tool')
def usb_tool_page():
    """AutoTech Client USB management page."""
    return render_template('usb_tool.html',
                           tool_name='AutoTech Client USB',
                           tool_id='client',
                           tool_icon='💾',
                           tool_display_name='AutoTech Client Package',
                           tool_description='USB installer and client management tools',
                           tool_folder='autotech_client',
                           tool_file='Install_AutoTech_Client.bat',
                           online=is_online_network(),
                           gateway_ip=GATEWAY_IP,
                           timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))


# ==============================================================================
# CLIENT INSTALLER DOWNLOADS
# ==============================================================================

@bp.route('/api/client/installer')
def api_client_installer():
    """Download AutoTech Client installer batch file (JSON API)."""
    client_folder, error = get_autotech_client_folder()
    if error or not client_folder:
        return jsonify({'error': error or 'AutoTech Client folder not found'}), 404
    installer_path = os.path.join(client_folder, 'Install_AutoTech_Client.bat')
    if not os.path.exists(installer_path):
        return jsonify({'error': 'Install_AutoTech_Client.bat not found in client folder'}), 404
    return send_file(installer_path, as_attachment=True, download_name='Install_AutoTech_Client.bat')


@bp.route('/api/client/test')
def api_client_test():
    """Test AutoTech Client installation status via registry and launcher files."""
    try:
        import winreg
    except ImportError:
        return jsonify({'error': 'winreg not available (Windows only)'}), 500

    protocols = ['autotech-ssh', 'autotech-sftp', 'autotech-vnc', 'autotech-script']
    handlers = {}
    for protocol in protocols:
        try:
            key = winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, protocol)
            winreg.CloseKey(key)
            handlers[protocol] = True
        except (FileNotFoundError, OSError):
            handlers[protocol] = False

    install_dir = r'C:\AutoTech_Client\scripts'
    launchers = {}
    for script in ['launch_putty.bat', 'launch_winscp.bat', 'launch_vnc.bat', 'launch_script.bat']:
        launchers[script] = os.path.exists(os.path.join(install_dir, script))

    all_installed = all(handlers.values()) and all(launchers.values())
    return jsonify({
        'handlers': handlers,
        'launchers': launchers,
        'install_dir': install_dir,
        'all_installed': all_installed
    })


@bp.route('/download-client-setup')
def download_client_setup():
    """Download AutoTech Client installer batch file (browser download)."""
    client_folder, error = get_autotech_client_folder()

    if error or not client_folder:
        return render_template('error.html',
                               error_title="Installer Not Found",
                               error_message=error or "AutoTech Client folder not found.",
                               online=is_online_network(),
                               gateway_ip=GATEWAY_IP), 404

    installer_path = os.path.join(client_folder, "Install_AutoTech_Client.bat")
    download_name = "Install_AutoTech_Client.bat"

    if not os.path.exists(installer_path):
        installer_path = os.path.join(client_folder, "AutoTech_Client_Installer.exe")
        download_name = "AutoTech_Client_Installer.exe"

    if not os.path.exists(installer_path):
        return render_template('error.html',
                               error_title="Installer Not Found",
                               error_message="Installer not found. Run BUILD_PYTHON_INSTALLER.bat option 5 to deploy.",
                               online=is_online_network(),
                               gateway_ip=GATEWAY_IP), 404

    return send_file(installer_path, as_attachment=True, download_name=download_name)


@bp.route('/download-client-package')
def download_client_package():
    """Download the complete AutoTech Client package as a ZIP file."""
    client_folder, error = get_autotech_client_folder()

    if error or not client_folder:
        return render_template('error.html',
                               error_title="Package Not Found",
                               error_message=error or "AutoTech Client folder not found.",
                               online=is_online_network(),
                               gateway_ip=GATEWAY_IP), 404

    tools_folder = os.path.join(client_folder, "tools")
    scripts_folder = os.path.join(client_folder, "scripts")

    if not os.path.exists(tools_folder) or not os.path.exists(scripts_folder):
        return render_template('error.html',
                               error_title="Package Incomplete",
                               error_message="The autotech_client folder is missing tools or scripts. Run BUILD_WEBSERVER.bat option 5 to deploy.",
                               online=is_online_network(),
                               gateway_ip=GATEWAY_IP), 404

    memory_file = BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(client_folder):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, client_folder)
                zf.write(file_path, arcname)

    memory_file.seek(0)
    return send_file(memory_file, mimetype='application/zip', as_attachment=True,
                     download_name='AutoTech_Client_Package.zip')


@bp.route('/live-install-client')
def live_install_client():
    """Show page with instructions for running installer directly from USB."""
    client_folder, error = get_autotech_client_folder()

    if error or not client_folder:
        return render_template('error.html',
                               error_title="Installer Not Found",
                               error_message=error or "AutoTech Client folder not found. Make sure the AUTOTECH USB is connected.",
                               online=is_online_network(),
                               gateway_ip=GATEWAY_IP), 404

    installer_path = os.path.join(client_folder, "Install_AutoTech_Client.bat")

    if not os.path.exists(installer_path):
        return render_template('error.html',
                               error_title="Installer Not Found",
                               error_message=f"Install_AutoTech_Client.bat not found in {client_folder}. Run BUILD_WEBSERVER.bat to rebuild.",
                               online=is_online_network(),
                               gateway_ip=GATEWAY_IP), 404

    installer_path_display = installer_path.replace('/', '\\')

    html_content = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Live Install - AutoTech Client</title>
        <link rel="stylesheet" href="/static/style.css">
        <style>
            .install-container {{
                max-width: 700px;
                margin: 40px auto;
                padding: 30px;
                background: var(--theme-card-bg);
                border-radius: 12px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            }}
            .install-container h1 {{
                color: var(--theme-accent);
                margin-bottom: 20px;
            }}
            .path-box {{
                background: #1a1a2e;
                border: 1px solid var(--theme-accent);
                border-radius: 8px;
                padding: 15px;
                font-family: monospace;
                font-size: 14px;
                word-break: break-all;
                margin: 20px 0;
                color: #00ff88;
            }}
            .copy-btn {{
                background: linear-gradient(135deg, var(--theme-accent) 0%, #e67e00 100%);
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                cursor: pointer;
                font-size: 16px;
                margin-right: 10px;
            }}
            .copy-btn:hover {{
                transform: translateY(-2px);
            }}
            .back-btn {{
                background: #555;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                cursor: pointer;
                font-size: 16px;
                text-decoration: none;
            }}
            .steps {{
                background: #2a2a3e;
                border-radius: 8px;
                padding: 20px;
                margin: 20px 0;
            }}
            .steps ol {{
                margin: 0;
                padding-left: 20px;
            }}
            .steps li {{
                margin: 10px 0;
                color: var(--theme-text);
            }}
            .success-msg {{
                color: #00ff88;
                display: none;
                margin-left: 10px;
            }}
        </style>
    </head>
    <body>
        <div class="install-container">
            <h1>&#9889; Live Install from USB</h1>
            <p>The installer is available at the following path:</p>

            <div class="path-box" id="installerPath">{installer_path_display}</div>

            <button class="copy-btn" onclick="copyPath()">&#128203; Copy Path</button>
            <a href="/autotech" class="back-btn">&larr; Back to T1 Legacy</a>
            <span class="success-msg" id="copySuccess">&#10003; Copied!</span>

            <div class="steps">
                <h3>Installation Steps:</h3>
                <ol>
                    <li>Open <strong>File Explorer</strong> on the target PC</li>
                    <li>Navigate to the USB drive path above (or paste the copied path)</li>
                    <li>Right-click <strong>Install_AutoTech_Client.bat</strong></li>
                    <li>Select <strong>"Run as administrator"</strong></li>
                    <li>Follow the on-screen prompts</li>
                </ol>
            </div>

            <p style="color: var(--theme-text-muted); font-size: 14px;">
                <strong>Note:</strong> The target PC must have network access to this USB drive.
                If not accessible, use the ZIP download option instead.
            </p>
        </div>

        <script>
            function copyPath() {{
                const path = document.getElementById('installerPath').textContent;
                navigator.clipboard.writeText(path).then(() => {{
                    const msg = document.getElementById('copySuccess');
                    msg.style.display = 'inline';
                    setTimeout(() => {{ msg.style.display = 'none'; }}, 2000);
                }});
            }}
        </script>
    </body>
    </html>
    '''
    return html_content


# ==============================================================================
# CLIENT REGISTRATION & VERSION CHECK
# ==============================================================================

@bp.route('/api/check-client-installed')
def api_check_client_installed():
    """Returns server version for comparison and client IP for tracking."""
    server_version = None
    server_version_file, _ = get_autotech_client_folder()
    if server_version_file:
        version_path = os.path.join(server_version_file, "AutoTech", "scripts", "VERSION")
        if not os.path.exists(version_path):
            version_path = os.path.join(server_version_file, "VERSION")
        if os.path.exists(version_path):
            try:
                with open(version_path, 'r') as f:
                    server_version = f.read().strip()
            except Exception:
                pass

    client_ip = request.remote_addr
    user_agent = request.headers.get('User-Agent', 'Unknown')

    return jsonify({
        'server_version': server_version or "1.1.1",
        'client_ip': client_ip,
        'user_agent': user_agent
    })


@bp.route('/api/register-client', methods=['POST'])
def api_register_client():
    """Register a newly installed AutoTech client with the server."""
    data = request.get_json() or {}
    client_version = data.get('client_version', '1.1.1')
    test_success = data.get('test_success', False)

    client_ip = request.remote_addr
    user_agent = request.headers.get('User-Agent', 'Unknown')
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    log_client(
        'info',
        'registration',
        format_client_registration(client_ip, client_version, user_agent, test_success)
    )

    print(f"\n{'='*60}")
    print(f"[CLIENT REGISTERED]")
    print(f"  IP Address: {client_ip}")
    print(f"  Version: v{client_version}")
    print(f"  Timestamp: {timestamp}")
    print(f"  User Agent: {user_agent[:50]}...")
    print(f"  Test Success: {test_success}")
    print(f"{'='*60}\n")

    return jsonify({
        'success': True,
        'message': f'Client registered: {client_ip}',
        'client_ip': client_ip,
        'timestamp': timestamp
    })
