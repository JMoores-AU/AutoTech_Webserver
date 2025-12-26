from flask import Flask, render_template, request, session, redirect, url_for, jsonify, flash
from tools import ptx_uptime, mineview_sessions, linux_health, playback_usb, camstudio_usb
from tools import ip_finder
from tools.additional_tools import speed_limit_data_check, koa_data_check, watchdog_deploy, component_tracking
from datetime import datetime
import threading, time, subprocess, sys, os, shutil, socket
from pathlib import Path
from functools import lru_cache
import ping3
from flask import Response
import json
from tools.ptx_health_check import run as ptx_health_check
from tools.ip_finder_enhanced import run as ip_finder_enhanced  
from tools.mineview_sessions_enhanced import run as mineview_sessions_enhanced
from tools.avi_mm2_reboot import run as avi_mm2_reboot
from tools.watchdog_deploy import run as watchdog_deploy
from tools.koa_data_check import run as koa_data_check
from tools.speed_limit_data import run as speed_limit_data
from tools.linux_health_enhanced import run as linux_health_enhanced
from tools.ip_finder import get_flight_recorder_ip

# Optional imports for future SSH features
import paramiko, shlex  # noqa: F401
import signal           # noqa: F401

from tools.serverList import SERVERS

# -------- app setup --------
if getattr(sys, 'frozen', False):
    template_folder = os.path.join(sys._MEIPASS, 'templates')
    static_folder   = os.path.join(sys._MEIPASS, 'static')
else:
    template_folder = 'templates'
    static_folder   = 'static'

app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)
app.secret_key = "T1_Tools_Secret"

# Extended tool list with additional functionality
TOOL_LIST = [
    "IP Finder", 
    "PTX Uptime", 
    "Mineview Sessions", 
    "KOA Data Check",
    "Speed Limit Data",
    "Component Tracking",
    "Watchdog Deploy",
    "Linux Health", 
    "PTX Health Check",
    "AVI/MM2 Reboot",
    "Playback USB", 
    "CamStudio USB"
]

TOOLS = {
    "PTX Uptime": ptx_uptime,
    "Mineview Sessions": mineview_sessions,
    "Linux Health": linux_health,
    "Playback USB": playback_usb,
    "CamStudio USB": camstudio_usb
}

# -------- env / network mode --------
GATEWAY_IP = "10.110.19.107"
PROBE_PORT = 22

@lru_cache(maxsize=1)
def is_online_network() -> bool:
    """True on closed network; False on laptop/dev."""
    if os.getenv("T1_OFFLINE", "").strip() == "1":
        print("[MODE] Forced OFFLINE via T1_OFFLINE")
        return False
    if os.getenv("T1_FORCE_ONLINE", "").strip() == "1":
        print("[MODE] Forced ONLINE via T1_FORCE_ONLINE")
        return True

    try:
        with socket.create_connection((GATEWAY_IP, PROBE_PORT), timeout=1.5):
            print(f"[MODE] ONLINE tcp {GATEWAY_IP}:{PROBE_PORT}")
            return True
    except Exception as e:
        print(f"[MODE] TCP probe failed: {e}")

    try:
        rtt = ping3.ping(GATEWAY_IP, timeout=1)
        ok = rtt is not None
        print(f"[MODE] ICMP {'ONLINE' if ok else 'OFFLINE'} rtt={rtt}")
        return ok
    except Exception as e:
        print(f"[MODE] ICMP error: {e}")
        return False

# -------- VNC viewer discovery --------
def find_vncviewer() -> Path:
    candidates = [
        Path(r"C:\Program Files\RealVNC\VNC Viewer\vncviewer.exe"),
        Path(r"C:\Program Files (x86)\RealVNC\VNC Viewer\vncviewer.exe"),
        Path(r"C:\Komatsu_Tier1\T1_Tools\tools\VNC\vncviewer.exe"),
        Path(r"C:\Program Files\RealVNC\VNC_Viewer_5.3.2\vncviewer.exe"),
    ]
    for p in candidates:
        if p.is_file():
            return p
    found = shutil.which("vncviewer.exe")
    if found:
        return Path(found)
    raise FileNotFoundError("vncviewer.exe not found in known locations or PATH")

def kill_vncviewer():
    for name in ("vncviewer.exe", "VNC-Viewer.exe"):
        try:
            subprocess.run(["taskkill", "/IM", name, "/F"], timeout=5, capture_output=True, text=True)
        except Exception:
            pass

def launch_vnc(ip: str):
    viewer = find_vncviewer()
    subprocess.Popen([str(viewer), f"{ip}:0"], close_fds=False)

PTX_CREDS = {
    "PTXC":  {"user": "dlog", "pass": "gold"},
    "PTX10": {"user": "mms",  "pass": "modular"},
}

# -------- helpers --------
def get_remote_stats():
    results = []
    for name, ip in SERVERS.items():
        try:
            rtt = ping3.ping(ip, timeout=1)
            status, latency = ('up', round(rtt * 1000)) if rtt is not None else ('down', None)
        except Exception:
            status, latency = 'error', None
        results.append({'name': name, 'ip': ip, 'status': status, 'latency': latency})
    return results

# -------- routes --------
@app.route("/", methods=["GET", "POST"])
def dashboard():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if request.method == "POST":
        password = request.form.get("password", "").strip().lower()
        if password == "komatsu":
            session["authenticated"] = True
            session["password"] = password
        else:
            flash("Incorrect password", "error")
    logged_in = session.get("authenticated", False)
    return render_template("enhanced_index.html",  # New template name
                           logged_in=logged_in,
                           current_time=now,
                           tools=TOOL_LIST,
                           online=is_online_network())

@app.get("/api/mode")
def api_mode():
    return jsonify({"online": is_online_network()})

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("dashboard"))

@app.route("/run/<tool_name>")
def run_tool(tool_name):
    if not session.get("authenticated"):
        return redirect(url_for("dashboard"))
    
    # Handle IP Finder as a special case - render its own page
    if tool_name == "IP Finder":
        return render_template("ip_finder.html")
    
    # Get password and online mode for tools that need them
    password = session.get("password")
    online = is_online_network()
    
    # Handle standard tools
    tool = TOOLS.get(tool_name)
    if tool:
        try:
            if hasattr(tool, 'run'):
                # Try to call with password and offline_mode if the tool supports it
                try:
                    result = tool.run(password=password, offline_mode=not online)
                except TypeError:
                    # Fallback for tools that don't accept parameters
                    result = tool.run()
            else:
                result = "Error: Tool module is not properly configured"
        except Exception as e:
            result = f"Error running {tool_name}: {str(e)}"
            
        return render_template("results.html", tool=tool_name, result=result)
    
    # Handle additional tools that require special forms
    if tool_name == "Speed Limit Data":
        result = speed_limit_data_check(password, offline_mode=not online)
        return render_template("results.html", tool=tool_name, result=result)
    
    elif tool_name == "KOA Analytics":
        result = koa_data_check(password, offline_mode=not online)
        return render_template("results.html", tool=tool_name, result=result)
    
    elif tool_name in ["Component Tracking", "Watchdog Deploy"]:
        # These need additional parameters - redirect to forms
        return render_template("tool_form.html", tool=tool_name)
    
    elif tool_name == "PTX Health Check":
        result = ptx_health_check(password=password, offline_mode=not online)
        return render_template("results.html", tool=tool_name, result=result)
    
    elif tool_name == "Linux Health Enhanced":
        result = linux_health_enhanced(password=password, offline_mode=not online)
        return render_template("results.html", tool=tool_name, result=result)
    
    elif tool_name == "Speed Limit Data":
        result = speed_limit_data(password=password, offline_mode=not online)
        return render_template("results.html", tool=tool_name, result=result)
    
    elif tool_name == "KOA Data Check":
        result = koa_data_check(password=password, offline_mode=not online)
        return render_template("results.html", tool=tool_name, result=result)
    
    elif tool_name == "MineView Sessions Enhanced":
        result = mineview_sessions_enhanced(password=password, offline_mode=not online)
        return render_template("results.html", tool=tool_name, result=result)
    
    # Tools that need parameters
    elif tool_name in ["IP Finder Enhanced", "AVI/MM2 Reboot", "Watchdog Deploy"]:
        return render_template("mms_parameter_form.html", tool=tool_name)
    
    flash("Tool not found", "error")
    return redirect(url_for("dashboard"))

@app.route("/ip_finder", methods=["POST"])
def ip_finder_query():
    if not session.get("authenticated"):
        return jsonify({"error": "Not authenticated"}), 403

    q = request.form.get("query", "").strip()
    online = is_online_network()
    mode = "offline_forced"

    try:
        if online:
            raw = ip_finder.run(q, password=session.get("password"), offline_mode=False)
            mode = "live"
        else:
            raw = ip_finder.run(q, password=session.get("password"), offline_mode=True)
            mode = "dummy_offline"
    except Exception as e:
        # Live failed → fallback to dummy
        print(f"[IPF] live failed: {e}; using dummy")
        raw = ip_finder.run(q, password=session.get("password"), offline_mode=True)
        mode = "dummy_fallback"

    parsed = ip_finder.parse_ip_finder_output(raw)

    # Add Flight Recorder IP for K830E and K930E profiles
    if parsed.get("profile") in ["K830E", "K930E"] and parsed.get("ptx_ip"):
        parsed["flight_recorder_ip"] = get_flight_recorder_ip(parsed["ptx_ip"])

    # Heuristic: if query != parsed OID and parsed looks like the canned block, flag as dummy
    if q and parsed.get("OID") and parsed["OID"].lower() != q.lower():
        mode = "dummy_detected"

    print(f"[IPF] q='{q}' online={online} mode={mode} parsed={parsed}")
    return jsonify({"result": parsed, "online": online, "mode": mode})

@app.route("/api/remote-stats")
def api_remote_stats():
    return jsonify(get_remote_stats())

@app.post("/ip_finder_vnc")
def ip_finder_vnc():
    query    = request.form.get("query","").strip()
    password = request.form.get("password","").strip()   # gateway password for 10.110.19.107
    offline  = request.form.get("offline","false").lower() == "true"
    try:
        result = ip_finder.ip_finder_to_vnc(query, password, offline_mode=offline)
        return jsonify(result)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.post("/api/vnc/open")
def api_vnc_open():
    if not session.get("authenticated"):
        return jsonify(ok=False, error="Not authenticated"), 403

    data = request.get_json(force=True, silent=True) or {}
    ip = (data.get("ip") or "").strip()
    model = (data.get("model") or "").strip().upper()

    if not ip:
        return jsonify(ok=False, error="IP required"), 400

    # Determine PTX model if not provided
    if model not in ("PTXC", "PTX10"):
        model = "PTXC" if data.get("ptxc_found") else "PTX10"

    creds = PTX_CREDS.get(model)
    if not creds:
        return jsonify(ok=False, error="Unknown PTX model"), 400

    # Return streaming response
    return Response(
        vnc_connection_stream(ip, model, creds),
        mimetype='text/plain'
    )


def vnc_connection_stream(ip, model, creds):
    """Stable VNC function that prevents connection drops"""
    
    def log_line(message, level="INFO"):
        timestamp = datetime.now().strftime("%I:%M:%S %p").lower()
        return f"[{timestamp}] [{level}] {message}\n"
    
    try:
        yield log_line(f"🖥️ Starting VNC connection to {ip}...")
        yield log_line(f"📋 PTX Model: {model}")
        
        kill_vncviewer()
        yield log_line(f"Local VNC sessions cleared")
        
        # SSH to PTX
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=ip, username=creds["user"], password=creds["pass"], timeout=10)
        yield log_line(f"✅ Connected as {creds['user']}")
        
        # Kill ALL VNC processes thoroughly
        yield log_line(f"Killing all VNC processes...")
        ssh.exec_command("pkill -f vnc")
        ssh.exec_command("pkill -f x11vnc")
        ssh.exec_command("pkill -f Xvnc")
        time.sleep(3)
        yield log_line(f"All VNC processes terminated")
        
        # Start x11vnc with password directly in command line (no file needed)
        yield log_line(f"Starting x11vnc with direct password...")
        
        # Use -passwd to pass password directly - much simpler!
        vnc_cmd = f'x11vnc -display :0 -rfbport 5900 -listen {ip} -passwd {creds["pass"]} -forever -shared -noxdamage -nap -bg'
        
        stdin, stdout, stderr = ssh.exec_command(vnc_cmd)
        time.sleep(5)
        
        # Read x11vnc output
        vnc_output = stdout.read().decode('utf-8', errors='ignore')
        vnc_error = stderr.read().decode('utf-8', errors='ignore')
        
        yield log_line(f"x11vnc startup:")
        for line in (vnc_output + vnc_error).split('\n'):
            if line.strip() and any(keyword in line for keyword in ["PORT=", "VNC desktop", "Listening", "screen setup"]):
                yield log_line(f"  {line.strip()}")
        
        # Verify x11vnc is running with correct options
        yield log_line(f"Verifying x11vnc is running...")
        
        stdin, stdout, stderr = ssh.exec_command("ps aux | grep x11vnc | grep -v grep")
        process_output = stdout.read().decode('utf-8', errors='ignore')
        
        if process_output.strip():
            yield log_line(f"✅ x11vnc process confirmed:")
            for line in process_output.split('\n')[:1]:
                if line.strip():
                    yield log_line(f"  {line.strip()}")
                    
                    # Check if it has the right options
                    if "-forever" in line:
                        yield log_line(f"✅ VNC configured to persist connections")
                    if "-passwd" in line:
                        yield log_line(f"✅ VNC using direct password authentication")
        else:
            yield log_line(f"❌ No x11vnc process found", "ERROR")
            ssh.close()
            return
        
        # Check network binding
        yield log_line(f"Checking network binding...")
        stdin, stdout, stderr = ssh.exec_command("netstat -ln | grep :5900")
        netstat_output = stdout.read().decode('utf-8', errors='ignore')
        
        if netstat_output.strip():
            for line in netstat_output.split('\n'):
                if line.strip():
                    if f"{ip}:5900" in line:
                        yield log_line(f"✅ VNC listening on {ip}:5900")
                    elif "0.0.0.0:5900" in line:
                        yield log_line(f"✅ VNC listening on all interfaces")
                    elif "127.0.0.1:5900" in line:
                        yield log_line(f"⚠️ VNC only on localhost - connection may fail", "WARNING")
        
        ssh.close()
        yield log_line(f"SSH connection closed")
        
        # Wait longer for VNC to stabilize
        yield log_line(f"Allowing VNC server to stabilize...")
        time.sleep(5)
        
        # Test port accessibility
        yield log_line(f"Testing VNC connection stability...")
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((ip, 5900))
        sock.close()
        
        if result == 0:
            yield log_line(f"✅ VNC port accessible and stable")
            
            # Launch VNC viewer
            viewer = find_vncviewer()
            subprocess.Popen([str(viewer), f"{ip}:0"])
            yield log_line(f"🎉 VNC viewer launched!")
            yield log_line(f"💡 VNC Authentication:")
            yield log_line(f"   Password: {creds['pass']}")
            yield log_line(f"   (No username needed with direct password)")
            yield log_line(f"✅ VNC connection completed successfully!")
            
        else:
            yield log_line(f"❌ VNC port not accessible", "ERROR")
            yield log_line(f"VNC server may have failed to start properly", "ERROR")
        
    except Exception as e:
        yield log_line(f"❌ Error: {str(e)}", "ERROR")

#### Additional helper function for better VNC server management ####
def find_vncviewer() -> Path:
    """Find VNC viewer executable"""
    candidates = [
        Path(r"C:\Program Files\RealVNC\VNC Viewer\vncviewer.exe"),
        Path(r"C:\Program Files (x86)\RealVNC\VNC Viewer\vncviewer.exe"),
        Path(r"C:\Komatsu_Tier1\T1_Tools\tools\VNC\vncviewer.exe"),
        Path(r"C:\Program Files\RealVNC\VNC_Viewer_5.3.2\vncviewer.exe"),
    ]
    for p in candidates:
        if p.is_file():
            return p
    found = shutil.which("vncviewer.exe")
    if found:
        return Path(found)
    raise FileNotFoundError("vncviewer.exe not found in known locations or PATH")

def kill_vncviewer():
    """Kill any existing VNC viewer processes"""
    for name in ("vncviewer.exe", "VNC-Viewer.exe"):
        try:
            subprocess.run(["taskkill", "/IM", name, "/F"], timeout=5, capture_output=True, text=True)
        except Exception:
            pass

@app.route("/handle_mms_parameter/<tool_name>", methods=["POST"])
def handle_mms_parameter(tool_name):
    if not session.get("authenticated"):
        return redirect(url_for("dashboard"))
    
    password = session.get("password")
    online = is_online_network()
    
    try:
        if tool_name == "IP Finder Enhanced":
            equipment_name = request.form.get("equipment_name", "").strip()
            if not equipment_name:
                flash("Equipment name is required", "error")
                return redirect(url_for("run_tool", tool_name=tool_name))
            result = ip_finder_enhanced(equipment_name=equipment_name, password=password, offline_mode=not online)
            
        elif tool_name == "AVI/MM2 Reboot":
            ptx_ip = request.form.get("ptx_ip", "").strip()
            if not ptx_ip:
                flash("PTX IP address is required", "error")
                return redirect(url_for("run_tool", tool_name=tool_name))
            result = avi_mm2_reboot(ptx_ip=ptx_ip, password=password, offline_mode=not online)
            
        elif tool_name == "Watchdog Deploy":
            ptx_ip = request.form.get("ptx_ip", "").strip()
            ptx_model = request.form.get("ptx_model", "PTXC")
            if not ptx_ip:
                flash("PTX IP address is required", "error")
                return redirect(url_for("run_tool", tool_name=tool_name))
            result = watchdog_deploy(ptx_ip=ptx_ip, ptx_model=ptx_model, password=password, offline_mode=not online)
            
        else:
            result = f"Tool '{tool_name}' not implemented"
            
        return render_template("results.html", tool=tool_name, result=result)
        
    except Exception as e:
        result = f"Error running {tool_name}: {str(e)}"
        return render_template("results.html", tool=tool_name, result=result)

def open_edge_browser():
    time.sleep(3)
    subprocess.Popen(['start', 'msedge', 'http://127.0.0.1:8888'], shell=True)

if __name__ == "__main__":
    threading.Thread(target=open_edge_browser, daemon=True).start()
    app.run(host="0.0.0.0", port=8888, debug=False)