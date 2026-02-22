"""
app/blueprints/downloads.py
============================
Binary/tool download routes:
  /download/camstudio, /download/frontrunner
"""

import logging
import tempfile
import zipfile
from pathlib import Path

from flask import Blueprint, send_file

logger = logging.getLogger(__name__)

bp = Blueprint('downloads', __name__, url_prefix='')


@bp.route("/download/camstudio")
def download_camstudio():
    """Provide CamStudio portable as a downloadable zip."""
    try:
        from tools.usb_tools import find_tool_on_usb
        result = find_tool_on_usb("CamStudio_USB", "CamStudioPortable.exe")

        if not result:
            return "CamStudio not found on server USB", 404

        camstudio_folder = Path(result['folder_path'])

        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_file:
            zip_path = tmp_file.name

            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file in camstudio_folder.rglob('*'):
                    if file.is_file():
                        arcname = file.relative_to(camstudio_folder.parent)
                        zipf.write(file, arcname)

            return send_file(
                zip_path,
                as_attachment=True,
                download_name='CamStudio_Portable.zip',
                mimetype='application/zip'
            )

    except Exception as e:
        logger.error(f"CamStudio download error: {e}")
        return str(e), 500


@bp.route("/download/frontrunner")
def download_frontrunner():
    """Provide FrontRunner V3.7.0 portable package as zip."""
    try:
        from tools.usb_tools import find_tool_on_usb
        result = find_tool_on_usb("frontrunnerV3-3.7.0-076-full", "V3.7.0 Playback Tool.bat")

        if not result:
            return "FrontRunner package not found on server USB", 404

        frontrunner_folder = Path(result['folder_path'])

        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_file:
            zip_path = tmp_file.name

            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file in frontrunner_folder.rglob('*'):
                    if file.is_file():
                        # Skip playback folder (too large)
                        if 'playback' in file.parts:
                            continue
                        arcname = file.relative_to(frontrunner_folder.parent)
                        zipf.write(file, arcname)

            return send_file(
                zip_path,
                as_attachment=True,
                download_name='FrontRunner_V3.7.0_Portable.zip',
                mimetype='application/zip'
            )

    except Exception as e:
        logger.error(f"FrontRunner download error: {e}")
        return str(e), 500
