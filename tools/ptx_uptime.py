import requests
import os
import re
from datetime import datetime
from bs4 import BeautifulSoup
from bs4 import Tag, NavigableString
import paramiko
from scp import SCPClient
from typing import Optional, List, Dict, Any
import tempfile

def get_ptx_uptime_file_path():
    """Get consistent path for PTX uptime report in Windows temp"""
    temp_dir = tempfile.gettempdir()
    return os.path.join(temp_dir, "PTX_Uptime_Report_Current.html")

def run(password: Optional[str] = None, offline_mode: bool = False) -> Dict[str, Any]:
    """
    Modified to save downloaded file to consistent location AND return parsed data
    """
    try:
        # Initialize variables
        html_content = None
        report_mode = "unknown"
        
        # Determine if we should use reference file for testing
        reference_file_path = os.path.join(os.path.dirname(__file__), 'PTX_Uptime_Report_Ref.html')
        use_reference_file = offline_mode and os.path.exists(reference_file_path)
        
        if use_reference_file:
            print("Using reference file for testing...")
            html_content = get_reference_file_content(reference_file_path)
            
            if html_content is not None:
                # Copy reference file to temp location 
                temp_file_path = get_ptx_uptime_file_path()
                with open(temp_file_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                report_mode = "reference"
            else:
                return {
                    'success': False,
                    'error': 'Failed to read reference file',
                    'report_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'mode': 'error'
                }
        else:
            # Download from live server
            print("Downloading PTX Uptime report from server...")
            html_content = download_ptx_uptime_report(password)
            report_mode = "live"
        
        # Check if we got valid content
        if not html_content:
            return {
                'success': False,
                'error': 'Failed to get PTX uptime data',
                'report_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'mode': 'error'
            }
        
        # Parse the HTML content for the enhanced template
        equipment_list = parse_ptx_uptime_html(html_content)
        
        if not equipment_list:
            return {
                'success': False,
                'error': 'No equipment data found in PTX uptime report',
                'report_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'mode': report_mode
            }

        # Filter equipment with more than 3 days (72 hours) uptime for display
        high_uptime_equipment = [
            eq for eq in equipment_list 
            if eq['uptime_hours'] > 72  # 72 hours = 3 days
        ]

        # Sort by uptime (highest first)
        high_uptime_equipment.sort(key=lambda x: x['uptime_hours'], reverse=True)

        # Calculate statistics
        statistics = {
            "total_equipment": len(equipment_list),
            "high_uptime_count": len(high_uptime_equipment),
            "avg_uptime": sum(e['uptime_hours'] for e in equipment_list) // len(equipment_list) if equipment_list else 0,
            "max_uptime": max((e['uptime_hours'] for e in equipment_list), default=0)
        }
        
        return {
            'success': True,
            'report_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'equipment_list': equipment_list,  # Full list for CSV export
            'high_uptime_equipment': high_uptime_equipment,  # Filtered for display
            'statistics': statistics,
            'file_path': get_ptx_uptime_file_path(),
            'mode': report_mode
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'report_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'mode': 'error'
        }

def get_reference_file_content(reference_file_path: str) -> Optional[str]:
    """Read content from reference file"""
    try:
        with open(reference_file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading reference file: {e}")
        return None

def download_ptx_uptime_report(password: Optional[str]) -> Optional[str]:
    """
    Download PTX uptime report using native Python SSH (no putty required)
    """
    try:
        return download_via_ssh(password)
        
    except Exception as e:
        print(f"Error downloading PTX uptime report: {e}")
        return None

def download_via_ssh(password: Optional[str]) -> Optional[str]:
    """Download using native Python SSH/SCP and save to temp folder"""
    try:
        hostname = "10.110.19.107"
        username = "mms"
        remote_file = "/home/mms/Logs/PTX_Uptime_Report.html"
        
        # Use consistent temp file location
        local_file = get_ptx_uptime_file_path()
        
        # DELETE existing cached file first
        if os.path.exists(local_file):
            os.remove(local_file)
            print(f"[DEBUG] Deleted cached file: {local_file}")
        
        print(f"Connecting to {hostname} as {username}...")
        
        # Create SSH client
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Connect to server
        ssh.connect(
            hostname=hostname,
            username=username,
            password=password,
            timeout=30
        )
        
        print("SSH connection established, downloading file...")
        
        # Get transport and check if it's available
        transport = ssh.get_transport()
        if transport is None:
            print("Failed to get SSH transport")
            ssh.close()
            return None
        
        # Use SCP to download file
        with SCPClient(transport) as scp:
            scp.get(remote_file, local_file)
        
        ssh.close()
        
        # Read the downloaded file
        if os.path.exists(local_file):
            with open(local_file, 'r', encoding='utf-8') as f:
                content = f.read()
            print(f"Successfully downloaded {len(content)} characters to {local_file}")
            return content
        else:
            print("Downloaded file not found")
            return None
            
    except Exception as e:
        print(f"Error in SSH download: {e}")
        return None

def parse_ptx_uptime_html(html_content: str) -> List[Dict[str, Any]]:
    """Parse the PTX uptime HTML content into equipment data"""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        equipment_list: List[Dict[str, Any]] = []
        
        # Find the main data table - with proper type checking
        table = soup.find('table')
        if not table or not hasattr(table, 'find_all'):
            print("No valid table found in HTML content")
            return []
        
        # Get all data rows (skip header) - safer parsing with type checks
        tbody = table.find('tbody')
        if tbody and isinstance(tbody, Tag):
            # Use tbody if it exists and is a proper Tag
            rows = tbody.find_all('tr')
        else:
            # If no tbody or tbody is not a Tag, get all rows and skip the first (header)
            all_rows = table.find_all('tr') if isinstance(table, Tag) else []
            rows = all_rows[1:] if len(all_rows) > 1 else []
        
        # Ensure rows is a list and filter out non-Tag elements
        if not isinstance(rows, list):
            rows = []
        
        for row in rows:
            # Skip if row is not a proper Tag object
            if not hasattr(row, 'find_all'):
                continue
                
            cells = row.find_all('td')
            if len(cells) >= 4:  # IP, Equipment_ID, Uptime, Last_Check
                try:
                    # Safely extract text with type checking
                    ip = cells[0].get_text().strip() if hasattr(cells[0], 'get_text') else ''
                    equipment_id = cells[1].get_text().strip() if hasattr(cells[1], 'get_text') else ''
                    uptime_text = cells[2].get_text().strip() if hasattr(cells[2], 'get_text') else ''
                    last_check = cells[3].get_text().strip() if hasattr(cells[3], 'get_text') else ''
                    
                    # Parse uptime hours
                    uptime_hours = 0.0
                    try:
                        uptime_hours = float(uptime_text)
                    except ValueError:
                        # Try to extract number from text
                        uptime_match = re.search(r'(\d+\.?\d*)', uptime_text)
                        if uptime_match:
                            uptime_hours = float(uptime_match.group(1))
                    
                    # Determine status based on uptime and last check
                    status = "Online" if uptime_hours > 0 else "Offline"
                    
                    # Calculate days from hours
                    uptime_days = round(uptime_hours / 24, 1) if uptime_hours > 0 else 0
                    
                    equipment = {
                        'ip': ip,
                        'equipment_id': equipment_id,
                        'uptime_hours': uptime_hours,
                        'uptime_days': uptime_days,
                        'last_check': last_check,
                        'status': status
                    }
                    
                    equipment_list.append(equipment)
                    
                except Exception as e:
                    print(f"Error parsing row: {e}")
                    continue
        
        print(f"Parsed {len(equipment_list)} equipment records")
        return equipment_list
        
    except Exception as e:
        print(f"Error parsing HTML: {e}")
        return []

def generate_csv_from_data(equipment_list: List[Dict[str, Any]]) -> Optional[str]:
    """Generate CSV content from equipment data"""
    try:
        csv_lines = []
        
        # Header
        csv_lines.append("IP Address,Equipment ID,Uptime Hours,Status,Last Check")
        
        # Data rows
        for equipment in equipment_list:
            ip = equipment.get('ip', '')
            equipment_id = equipment.get('equipment_id', '')
            uptime_hours = equipment.get('uptime_hours', 0)
            status = equipment.get('status', 'Unknown')
            last_check = equipment.get('last_check', '')
            
            # Escape commas in data
            equipment_id = f'"{equipment_id}"' if ',' in equipment_id else equipment_id
            last_check = f'"{last_check}"' if ',' in last_check else last_check
            
            csv_lines.append(f"{ip},{equipment_id},{uptime_hours},{status},{last_check}")
        
        return '\n'.join(csv_lines)
        
    except Exception as e:
        print(f"Error generating CSV: {e}")
        return None

# Test function
if __name__ == "__main__":
    # Test with reference file
    print("Testing PTX Uptime with reference file...")
    result = run(offline_mode=True)
    
    if result['success']:
        print(f"Success! Found {len(result['top_10'])} top equipment")
        print(f"Statistics: {result['statistics']}")
        print(f"Mode: {result['mode']}")
        
        # Test CSV generation
        csv_content = generate_csv_from_data(result['equipment_list'])
        if csv_content:
            print("CSV generation successful!")
        else:
            print("CSV generation failed")
    else:
        print(f"Error: {result['error']}")