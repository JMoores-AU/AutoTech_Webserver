# tools/tru_access.py

import subprocess
import socket
import time
import threading
import json
import os
import sys

def check_host_online(ip_address, timeout=3):
    """Check if host is reachable via ping"""
    try:
        # Use subprocess to ping the host
        result = subprocess.run(
            ['ping', '-n' if subprocess.os.name == 'nt' else '-c', '1', ip_address],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        return False
    except Exception:
        return False

def check_ssh_connection(ip_address, timeout=5):
    """Test SSH connection to determine PTX type (PTXC vs PTX10) using paramiko"""
    print(f"[SSH] Testing SSH connection to {ip_address}")
    
    try:
        import paramiko
        print("[SSH] Paramiko imported successfully")
    except ImportError:
        print("[SSH] Paramiko not found, installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "paramiko"])
        import paramiko
        print("[SSH] Paramiko installed and imported")
    
    # Try PTXC credentials first (dlog/gold)
    print("[SSH] Trying PTXC credentials (dlog/gold)...")
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(ip_address, username='dlog', password='gold', timeout=timeout)
        stdin, stdout, stderr = client.exec_command('ls /')
        exit_code = stdout.channel.recv_exit_status()
        client.close()
        print(f"[SSH] PTXC test result: exit_code={exit_code}")
        
        if exit_code == 0:
            print("[SSH] SUCCESS: PTXC credentials work")
            return 'PTXC', 'dlog', 'gold'
    except Exception as e:
        print(f"[SSH] PTXC test failed: {e}")
    
    # Try PTX10 credentials (mms/modular)
    print("[SSH] Trying PTX10 credentials (mms/modular)...")
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(ip_address, username='mms', password='modular', timeout=timeout)
        stdin, stdout, stderr = client.exec_command('ls /')
        exit_code = stdout.channel.recv_exit_status()
        client.close()
        print(f"[SSH] PTX10 test result: exit_code={exit_code}")
        
        if exit_code == 0:
            print("[SSH] SUCCESS: PTX10 credentials work")
            return 'PTX10', 'mms', 'modular'
    except Exception as e:
        print(f"[SSH] PTX10 test failed: {e}")
    
    # If both fail, default to PTXC (most common)
    print("[SSH] Both credential tests failed, defaulting to PTXC")
    return 'PTXC', 'dlog', 'gold'

def find_available_ports(start_port=8001, count=2):
    """Find available local ports for tunneling"""
    available_ports = []
    port = start_port
    
    while len(available_ports) < count:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                available_ports.append(port)
        except OSError:
            pass
        port += 1
        
        # Safety check to avoid infinite loop
        if port > start_port + 100:
            break
    
    return available_ports

class SSHTunnel:
    """Manage SSH tunnel connections using paramiko"""
    
    def __init__(self, local_port, remote_host, remote_port, ssh_host, ssh_user, ssh_password):
        self.local_port = local_port
        self.remote_host = remote_host
        self.remote_port = remote_port
        self.ssh_host = ssh_host
        self.ssh_user = ssh_user
        self.ssh_password = ssh_password
        self.ssh_client = None
        self.transport = None
        self.is_active = False
        self.tunnel_thread = None
    
    def start(self):
        """Start the SSH tunnel using paramiko"""
        print(f"[TUNNEL] Starting tunnel: {self.ssh_host}:{self.local_port} -> {self.remote_host}:{self.remote_port}")
        
        try:
            import paramiko
        except ImportError:
            print("[TUNNEL] Installing paramiko...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "paramiko"])
            import paramiko
        
        try:
            # Create SSH client
            print(f"[TUNNEL] Creating SSH client for {self.ssh_user}@{self.ssh_host}")
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Connect to SSH server
            print(f"[TUNNEL] Connecting to SSH server...")
            self.ssh_client.connect(
                self.ssh_host,
                username=self.ssh_user,
                password=self.ssh_password,
                timeout=10
            )
            print(f"[TUNNEL] SSH connection established")
            
            # Get transport
            self.transport = self.ssh_client.get_transport()
            print(f"[TUNNEL] Got SSH transport")
            
            # Mark as active before starting worker
            self.is_active = True
            
            # Create tunnel in a separate thread
            print(f"[TUNNEL] Starting tunnel worker thread...")
            self.tunnel_thread = threading.Thread(
                target=self._tunnel_worker,
                daemon=True
            )
            self.tunnel_thread.start()
            
            # Give tunnel time to establish
            print(f"[TUNNEL] Waiting for tunnel to establish...")
            time.sleep(3)
            
            # Test if local port is listening
            if self._test_local_port():
                print(f"[TUNNEL] SUCCESS: Tunnel active on port {self.local_port}")
                return True
            else:
                print(f"[TUNNEL] ERROR: Local port {self.local_port} not listening")
                self.stop()
                return False
                
        except Exception as e:
            print(f"[TUNNEL] ERROR: Failed to start tunnel: {e}")
            import traceback
            traceback.print_exc()
            self.stop()
            return False
    
    def _tunnel_worker(self):
        """Worker thread for handling tunnel connections"""
        try:
            import paramiko
            
            # Create server socket
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind(('localhost', self.local_port))
            server_socket.listen(5)
            
            while self.is_active:
                try:
                    client_socket, client_addr = server_socket.accept()
                    
                    # Create channel for port forwarding
                    channel = self.transport.open_channel(
                        'direct-tcpip',
                        (self.remote_host, self.remote_port),
                        client_addr
                    )
                    
                    # Start forwarding data
                    threading.Thread(
                        target=self._forward_data,
                        args=(client_socket, channel),
                        daemon=True
                    ).start()
                    
                except Exception as e:
                    if self.is_active:
                        print(f"Tunnel connection error: {e}")
                    break
            
            server_socket.close()
            
        except Exception as e:
            print(f"Tunnel worker error: {e}")
    
    def _forward_data(self, client_socket, channel):
        """Forward data between client socket and SSH channel"""
        def forward(src, dst):
            try:
                while True:
                    data = src.recv(4096)
                    if not data:
                        break
                    dst.send(data)
            except:
                pass
            finally:
                src.close()
                dst.close()
        
        # Start forwarding in both directions
        threading.Thread(target=forward, args=(client_socket, channel), daemon=True).start()
        threading.Thread(target=forward, args=(channel, client_socket), daemon=True).start()
    
    def _test_local_port(self):
        """Test if local port is listening"""
        try:
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = test_socket.connect_ex(('localhost', self.local_port))
            test_socket.close()
            return result == 0
        except:
            return False
    
    def stop(self):
        """Stop the SSH tunnel"""
        self.is_active = False
        
        if self.ssh_client:
            try:
                self.ssh_client.close()
            except:
                pass
        
        if self.tunnel_thread and self.tunnel_thread.is_alive():
            # Give thread time to cleanup
            time.sleep(1)

def setup_tru_access(equipment_ip, equipment_name=None):
    """
    Main function to set up TRU access for specified equipment using IP directly
    Returns dictionary with status and connection info
    """
    print(f"[TRU] Starting TRU access setup for {equipment_name} at {equipment_ip}")
    
    result = {
        'success': False,
        'message': '',
        'equipment_name': equipment_name or 'Unknown',
        'ip_address': equipment_ip,
        'ptx_type': None,
        'tunnels': [],
        'local_ports': []
    }
    
    try:
        if not equipment_ip:
            print("[TRU] ERROR: No equipment IP provided")
            result['message'] = 'Equipment IP address required'
            return result
        
        result['ip_address'] = equipment_ip
        print(f"[TRU] Using IP address: {equipment_ip}")
        
        # Check if equipment is online
        print(f"[TRU] Checking if {equipment_ip} is online...")
        if not check_host_online(equipment_ip):
            print(f"[TRU] ERROR: Cannot reach {equipment_ip}")
            result['message'] = f'Unable to reach equipment on {equipment_ip}'
            return result
        
        print(f"[TRU] Host {equipment_ip} is reachable")
        
        # Determine PTX type
        print(f"[TRU] Determining PTX type for {equipment_ip}...")
        ptx_type, username, password = check_ssh_connection(equipment_ip)
        print(f"[TRU] PTX detection result: type={ptx_type}, user={username}")
        
        if not ptx_type:
            print(f"[TRU] ERROR: Could not determine PTX type")
            result['message'] = f'Unable to determine PTX type for {equipment_ip}'
            return result
        
        result['ptx_type'] = ptx_type
        print(f"[TRU] PTX type confirmed: {ptx_type}")
        
        # Find available local ports
        print(f"[TRU] Finding available local ports...")
        available_ports = find_available_ports()
        print(f"[TRU] Available ports: {available_ports}")
        
        if len(available_ports) < 2:
            print(f"[TRU] ERROR: Only {len(available_ports)} ports available, need 2")
            result['message'] = 'Unable to find available local ports for tunneling'
            return result
        
        result['local_ports'] = available_ports[:2]
        print(f"[TRU] Using ports: GNSS1={available_ports[0]}, GNSS2={available_ports[1]}")
        
        # Set up tunnels to both GNSS receivers
        tunnels = []
        
        print(f"[TRU] Creating GNSS 1 tunnel...")
        # GNSS 1 tunnel (192.168.0.101:8002)
        tunnel1 = SSHTunnel(
            local_port=available_ports[0],
            remote_host='192.168.0.101',
            remote_port=8002,
            ssh_host=equipment_ip,
            ssh_user=username,
            ssh_password=password
        )
        
        print(f"[TRU] Creating GNSS 2 tunnel...")
        # GNSS 2 tunnel (192.168.0.102:8002)
        tunnel2 = SSHTunnel(
            local_port=available_ports[1],
            remote_host='192.168.0.102',
            remote_port=8002,
            ssh_host=equipment_ip,
            ssh_user=username,
            ssh_password=password
        )
        
        # Start tunnels
        print(f"[TRU] Starting GNSS 1 tunnel on port {available_ports[0]}...")
        tunnel1_success = tunnel1.start()
        print(f"[TRU] GNSS 1 tunnel result: {tunnel1_success}")
        
        print(f"[TRU] Starting GNSS 2 tunnel on port {available_ports[1]}...")
        tunnel2_success = tunnel2.start()
        print(f"[TRU] GNSS 2 tunnel result: {tunnel2_success}")
        
        if tunnel1_success and tunnel2_success:
            tunnels.extend([tunnel1, tunnel2])
            result['tunnels'] = tunnels
            result['success'] = True
            result['message'] = f'TRU access established to {equipment_ip} ({ptx_type}) - GNSS1: localhost:{available_ports[0]}, GNSS2: localhost:{available_ports[1]}'
            print(f"[TRU] SUCCESS: Both tunnels established")
        else:
            error_msg = f"Failed tunnels - GNSS1: {tunnel1_success}, GNSS2: {tunnel2_success}"
            print(f"[TRU] ERROR: {error_msg}")
            result['message'] = 'Failed to establish SSH tunnels'
            # Clean up any successful tunnels
            if tunnel1_success:
                print("[TRU] Cleaning up GNSS1 tunnel")
                tunnel1.stop()
            if tunnel2_success:
                print("[TRU] Cleaning up GNSS2 tunnel")
                tunnel2.stop()
        
    except Exception as e:
        print(f"[TRU] EXCEPTION: {str(e)}")
        import traceback
        traceback.print_exc()
        result['message'] = f'Error setting up TRU access: {str(e)}'
    
    print(f"[TRU] Final result: success={result['success']}, message={result['message']}")
    return result

def get_tru_connection_info():
    """Get information about active TRU connections"""
    # This would be expanded to track active connections
    # For now, return empty list
    return []

def close_tru_tunnels(tunnels):
    """Close active TRU tunnels"""
    for tunnel in tunnels:
        tunnel.stop()

# Example usage and testing
if __name__ == "__main__":
    # Test the TRU access setup
    equipment_ip = input("Enter equipment IP: ")
    equipment_name = input("Enter equipment name (optional): ")
    result = setup_tru_access(equipment_ip, equipment_name)
    
    print(json.dumps(result, indent=2, default=str))
    
    if result['success']:
        print(f"\nTunnels established:")
        print(f"GNSS 1: localhost:{result['local_ports'][0]}")
        print(f"GNSS 2: localhost:{result['local_ports'][1]}")
        print(f"PTX Type: {result['ptx_type']}")
        
        input("\nPress Enter to close tunnels...")
        close_tru_tunnels(result['tunnels'])