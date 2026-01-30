# tools/playback_usb.py
"""
Playback USB Tool
Finds and launches V3.7.0 Playback Tool from USB drive
"""
from tools.usb_tools import find_tool_on_usb, launch_tool, get_removable_drives
from tools.app_logger import log_tool

# Tool configuration
TOOL_FOLDER = "frontrunnerV3-3.7.0-076-full"
TOOL_FILE = "V3.7.0 Playback Tool.bat"
TOOL_NAME = "Playback Tool V3.7.0"


def scan():
    """
    Scan for Playback Tool on USB drives.
    Returns dict with status and details.
    """
    drives = get_removable_drives(include_fixed=True)
    result = find_tool_on_usb(TOOL_FOLDER, TOOL_FILE)
    log_tool('info', 'usb', f"Playback USB scan drives={len(drives)} found={result is not None}")
    
    return {
        'tool_name': TOOL_NAME,
        'drives_scanned': len(drives),
        'drives': drives,
        'found': result is not None,
        'details': result
    }


def launch():
    """
    Find and launch Playback Tool from USB.
    Returns tuple of (success, message).
    """
    result = find_tool_on_usb(TOOL_FOLDER, TOOL_FILE)
    
    if not result:
        drives = get_removable_drives(include_fixed=True)
        if not drives:
            log_tool('warning', 'usb', "Playback USB launch failed: no drives")
            return False, "No USB drives detected. Please insert the USB drive with Playback Tool."
        else:
            drive_list = ", ".join([f"{d['letter']}:" for d in drives])
            log_tool('warning', 'usb', f"Playback USB tool not found in drives: {drive_list}")
            return False, f"Playback Tool not found. Checked drives: {drive_list}. Expected folder: {TOOL_FOLDER}"
    
    # Launch the tool
    success, message = launch_tool(result['file_path'], result['folder_path'])
    
    if success:
        log_tool('info', 'usb', f"Playback USB launched from {result['drive']['letter']}:")
        return True, f"Playback Tool launched from {result['drive']['letter']}:\\"
    else:
        log_tool('error', 'usb', f"Playback USB launch failed: {message}")
        return False, message


def run():
    """Legacy run function for compatibility."""
    success, message = launch()
    return message
