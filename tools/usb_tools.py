# tools/usb_tools.py
"""
USB Tools - Shared functions for CamStudio and Playback USB tools
Scans removable drives and launches tools from USB
"""
import os
import subprocess
import string
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Tuple

# Windows-specific imports
try:
    import ctypes
    WINDOWS = True
except ImportError:
    WINDOWS = False


def get_removable_drives(include_fixed: bool = False) -> List[Dict]:
    """
    Get list of removable USB drives on Windows.
    Returns list of dicts with drive info.

    Args:
        include_fixed: If True, also include fixed drives (some USB drives report as fixed)
    """
    removable_drives = []

    if not WINDOWS:
        return removable_drives

    # Windows drive type constants
    DRIVE_REMOVABLE = 2
    DRIVE_FIXED = 3
    DRIVE_REMOTE = 4  # Covers RDP-redirected or network-mapped USBs

    # Skip system drive
    system_drive = os.environ.get('SystemDrive', 'C:')[0].upper()

    try:
        # Get all drive letters
        bitmask = ctypes.windll.kernel32.GetLogicalDrives()

        for letter in string.ascii_uppercase:
            if bitmask & 1:
                drive_path = f"{letter}:\\"
                drive_type = ctypes.windll.kernel32.GetDriveTypeW(drive_path)

                # Include removable drives, and optionally fixed drives (excluding system)
                is_removable = drive_type == DRIVE_REMOVABLE
                is_fixed_non_system = (drive_type == DRIVE_FIXED and
                                       letter != system_drive and
                                       include_fixed)
                is_remote = drive_type == DRIVE_REMOTE  # allow redirected USBs

                if is_removable or is_fixed_non_system or is_remote:
                    # Get drive info
                    drive_info = {
                        'letter': letter,
                        'path': drive_path,
                        'label': get_drive_label(drive_path),
                        'free_space': get_drive_free_space(drive_path),
                        'type': 'removable' if is_removable else 'fixed'
                    }
                    removable_drives.append(drive_info)

            bitmask >>= 1

    except Exception as e:
        print(f"Error scanning drives: {e}")

    return removable_drives


def get_drive_label(drive_path: str) -> str:
    """Get the volume label of a drive."""
    try:
        volume_name = ctypes.create_unicode_buffer(1024)
        ctypes.windll.kernel32.GetVolumeInformationW(
            drive_path,
            volume_name,
            1024,
            None, None, None, None, 0
        )
        return volume_name.value or "Removable Disk"
    except:
        return "Removable Disk"


def get_drive_free_space(drive_path: str) -> Optional[float]:
    """Get free space in GB for a drive."""
    try:
        free_bytes = ctypes.c_ulonglong(0)
        ctypes.windll.kernel32.GetDiskFreeSpaceExW(
            drive_path,
            None,
            None,
            ctypes.pointer(free_bytes)
        )
        return round(free_bytes.value / (1024**3), 2)
    except:
        return None


def find_tool_on_usb(folder_name: str, file_name: str, include_fixed: bool = True) -> Optional[Dict]:
    """
    Search all removable drives for a specific tool.

    Args:
        folder_name: Subfolder to look in (e.g., "CamStudio_USB")
        file_name: File to find (e.g., "CamStudioPortable.exe")
        include_fixed: Also search fixed drives (some USB drives report as fixed)

    Returns:
        Dict with tool info if found, None otherwise
    """
    # Optional override for locked-down/remote setups
    override_drive = os.environ.get('PLAYBACK_USB_DRIVE', '').strip()
    if override_drive:
        if not override_drive.endswith(':'):
            override_drive = override_drive + ':'
        drive_path = f"{override_drive}\\"
        drives = [{'letter': override_drive.rstrip(':'), 'path': drive_path}] if Path(drive_path).exists() else []
    else:
        # Search removable drives first, then fixed drives if not found
        drives = get_removable_drives(include_fixed=include_fixed)
    
    for drive in drives:
        # Build path to tool
        if folder_name:
            tool_folder = Path(drive['path']) / folder_name
        else:
            tool_folder = Path(drive['path'])
        
        tool_path = tool_folder / file_name
        
        if tool_path.exists():
            return {
                'found': True,
                'drive': drive,
                'folder_path': str(tool_folder),
                'file_path': str(tool_path),
                'file_name': file_name
            }
    
    return None


def launch_tool(file_path: str, working_dir: str) -> Tuple[bool, str]:
    """
    Launch a tool (exe or bat file).
    
    Args:
        file_path: Full path to the file
        working_dir: Working directory for the process
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        file_path = Path(file_path)
        
        if not file_path.exists():
            return False, f"File not found: {file_path}"
        
        extension = file_path.suffix.lower()
        
        if extension == '.bat':
            # Run batch file via cmd.exe
            subprocess.Popen(
                f'cmd.exe /c "{file_path}"',
                cwd=working_dir,
                shell=True,
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            return True, f"Batch file launched: {file_path.name}"
        
        elif extension == '.exe':
            # Run executable directly
            subprocess.Popen(
                str(file_path),
                cwd=working_dir,
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            return True, f"Executable launched: {file_path.name}"
        
        else:
            return False, f"Unsupported file type: {extension}"
    
    except Exception as e:
        return False, f"Launch failed: {str(e)}"


def scan_usb_status() -> Dict:
    """
    Scan all USB drives and check for known tools.
    Also checks fixed drives since some USB drives report as fixed.
    Returns comprehensive status.
    """
    drives = get_removable_drives(include_fixed=True)
    
    # Define known tools
    known_tools = {
        'camstudio': {
            'name': 'CamStudio Portable',
            'folder': 'CamStudio_USB',
            'file': 'CamStudioPortable.exe'
        },
        'playback': {
            'name': 'Playback Tool V3.7.0',
            'folder': 'frontrunnerV3-3.7.0-076-full',
            'file': 'V3.7.0 Playback Tool.bat'
        }
    }
    
    status = {
        'scan_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'drives_found': len(drives),
        'drives': drives,
        'tools': {}
    }
    
    # Check each tool
    for tool_id, tool_info in known_tools.items():
        result = find_tool_on_usb(tool_info['folder'], tool_info['file'])
        status['tools'][tool_id] = {
            'name': tool_info['name'],
            'found': result is not None,
            'details': result
        }
    
    return status
