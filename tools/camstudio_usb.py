# tools/camstudio_usb.py
"""
CamStudio USB Tool
Finds and launches CamStudioPortable.exe from USB drive
"""
from tools.usb_tools import find_tool_on_usb, launch_tool, get_removable_drives

# Tool configuration
TOOL_FOLDER = "CamStudio_USB"
TOOL_FILE = "CamStudioPortable.exe"
TOOL_NAME = "CamStudio Portable"


def scan():
    """
    Scan for CamStudio on USB drives.
    Returns dict with status and details.
    """
    drives = get_removable_drives()
    result = find_tool_on_usb(TOOL_FOLDER, TOOL_FILE)
    
    return {
        'tool_name': TOOL_NAME,
        'drives_scanned': len(drives),
        'drives': drives,
        'found': result is not None,
        'details': result
    }


def launch():
    """
    Find and launch CamStudio from USB.
    Returns tuple of (success, message).
    """
    result = find_tool_on_usb(TOOL_FOLDER, TOOL_FILE)
    
    if not result:
        drives = get_removable_drives()
        if not drives:
            return False, "No USB drives detected. Please insert the USB drive with CamStudio."
        else:
            drive_list = ", ".join([f"{d['letter']}:" for d in drives])
            return False, f"CamStudio not found. Checked drives: {drive_list}. Expected folder: {TOOL_FOLDER}"
    
    # Launch the tool
    success, message = launch_tool(result['file_path'], result['folder_path'])
    
    if success:
        return True, f"CamStudio launched from {result['drive']['letter']}:\\"
    else:
        return False, message


def run():
    """Legacy run function for compatibility."""
    success, message = launch()
    return message
