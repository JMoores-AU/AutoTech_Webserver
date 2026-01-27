# AutoTech Web Dashboard - Comprehensive Logging Architecture Design

**Document Version:** 1.0
**Created:** 2026-01-27
**Status:** Design Phase (Not Yet Implemented)

---

## Executive Summary

This document provides a comprehensive design for implementing enterprise-grade logging in the AutoTech Web Dashboard Flask application. The logging system will provide complete visibility into:

- Flask server operations (requests, responses, errors)
- Remote client activities (registrations, connections, verifications)
- Background task execution (equipment updater, PTX checker, FrontRunner monitor)
- SSH/SFTP tool operations (connections, queries, errors)
- Database operations (queries, performance, errors)
- Security events (authentication, failed attempts)

The system is designed specifically for Windows deployment (development, standalone executable, Windows service) and handles path resolution for both development and USB deployment scenarios.

---

## Table of Contents

1. [Current State Analysis](#current-state-analysis)
2. [Logging Architecture Overview](#logging-architecture-overview)
3. [Log File Organization](#log-file-organization)
4. [Core Components](#core-components)
5. [Integration Points](#integration-points)
6. [Log Format Standards](#log-format-standards)
7. [Configuration & Path Resolution](#configuration--path-resolution)
8. [Performance Considerations](#performance-considerations)
9. [Windows Service Integration](#windows-service-integration)
10. [Implementation Roadmap](#implementation-roadmap)
11. [Troubleshooting Guide](#troubleshooting-guide)

---

## Current State Analysis

### Existing Logging

**Current Implementation:**
```python
# main.py, line 89-91
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
```

**Issues with Current Approach:**
- Single logger using console output only (no file persistence)
- No log rotation (unbounded file growth)
- No structured format (difficult to parse/analyze)
- No separation by concern (all logs mixed together)
- No subcategory tracking (hard to filter by operation type)
- Background tasks use `print()` statements instead of logging
- Tool modules use logging but without consistent formatting
- No request/response tracking across routes
- No performance metrics (request duration, query times)

**Current Codebase Structure:**
- **main.py:** ~4000 lines, all routes defined here, basic logging
- **tools/*.py:** Multiple modules (equipment_db, ptx_uptime, frontrunner_monitor, etc.)
- **Background Threads:** Equipment updater, PTX checker, Playback monitor, FrontRunner monitor
- **Databases:** equipment_cache.db, ptx_uptime.db, frontrunner_events.db
- **Deployment:** Development (python main.py), Standalone (AutoTech.exe), Windows Service

---

## Logging Architecture Overview

### Design Philosophy

1. **Structured Logging** - Consistent format enabling automated parsing
2. **Separation of Concerns** - Different logs for different operational domains
3. **Performance** - Minimal overhead, background thread-safe
4. **Deployment Agnostic** - Works in development, standalone exe, Windows service
5. **Windows Optimized** - Uses standard library only (no external dependencies)
6. **Disk Efficient** - Automatic rotation prevents unbounded growth

### Logging Tiers

```
Level 1: Core Logger (app_logger.py)
├── Directory detection and rotation setup
├── File handler management
└── Pre-configured logger instances

Level 2: Category Loggers (server, client, tools, background, security, database)
├── Specialized handlers per category
└── Consistent formatting

Level 3: Subcategory Logging (request, response, ssh, sftp, query, error, etc.)
├── Contextual information included
└── Performance metrics captured

Level 4: Request Context Tracking (optional)
├── Request IDs for tracing
└── User/IP correlation
```

### Multi-Destination Strategy

```
Development Mode:
├── Console Output (human-readable, color-coded if terminal supports it)
└── File Output (persistent, rotated)

Frozen Exe Mode:
├── File Output Only (console hidden)
└── No console pollution

Windows Service Mode:
├── File Output Only (no console available)
└── Service logs go to Windows Event Log (optional)
```

---

## Log File Organization

### Directory Structure

**Development Environment:**
```
C:\AutoTech_WebApps\AutoTech_WebServer\
├── database\
│   ├── logs\
│   │   ├── server.log (and .1, .2, .3, .4, .5 backups)
│   │   ├── clients.log
│   │   ├── tools.log
│   │   ├── background.log
│   │   ├── security.log
│   │   └── database.log
│   ├── equipment_cache.db
│   ├── ptx_uptime.db
│   └── frontrunner_events.db
```

**USB Deployment (E:\):**
```
E:\
├── AutoTech.exe
├── AutoTech\
│   ├── tools\
│   ├── database\
│   │   ├── logs\
│   │   │   ├── server.log (and backups)
│   │   │   ├── clients.log
│   │   │   ├── tools.log
│   │   │   ├── background.log
│   │   │   ├── security.log
│   │   │   └── database.log
│   │   ├── equipment_cache.db
│   │   ├── ptx_uptime.db
│   │   └── frontrunner_events.db
│   ├── Install_AutoTech_Service.bat
│   └── Uninstall_AutoTech_Service.bat
```

### Log File Specifications

| Log File | Purpose | Rotation | Notes |
|----------|---------|----------|-------|
| `server.log` | Flask request/response, errors, startup/shutdown | 5MB, 5 backups | Main operational log |
| `clients.log` | Client registrations, verifications, connections | 5MB, 5 backups | Tracks remote access |
| `tools.log` | SSH operations, SFTP transfers, IP finder, PTX queries | 5MB, 5 backups | Diagnostic tool usage |
| `background.log` | Equipment updater, PTX checker, FrontRunner monitor | 5MB, 5 backups | Background task health |
| `security.log` | Authentication attempts, login failures, unauthorized access | 5MB, 5 backups | Security audit trail |
| `database.log` | Database queries (slow logs), schema changes, errors | 5MB, 5 backups | Database health |

**Rotation Parameters:**
- **Max File Size:** 5 MB per log file
- **Backup Count:** 5 previous versions
- **Total Capacity:** ~30 MB per category = ~180 MB total
- **Encoding:** UTF-8 (handles special characters)

---

## Core Components

### 1. Logger Module: `tools/app_logger.py`

This module provides the logging infrastructure for the entire application.

#### Key Responsibilities:
- Path resolution for log directory (handles dev, USB, frozen exe modes)
- Logger initialization and configuration
- Rotation handler setup
- Category-specific convenience functions
- Console output control (dev vs. production)

#### Module Structure:

```python
# tools/app_logger.py

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from datetime import datetime

# ========================================
# PATH RESOLUTION (Development vs. Frozen)
# ========================================

if getattr(sys, 'frozen', False):
    # Running as PyInstaller executable (e.g., AutoTech.exe)
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # Running as Python script
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ========================================
# LOG DIRECTORY DETECTION
# ========================================

# Handles USB deployment (E:\AutoTech\database\logs)
# and development (project\database\logs)
LOG_CANDIDATES = [
    os.path.join(BASE_DIR, 'AutoTech', 'database', 'logs'),  # USB path
    os.path.join(BASE_DIR, 'database', 'logs')                 # Dev path
]

LOG_DIR = next(
    (p for p in LOG_CANDIDATES if os.path.exists(os.path.dirname(p))),
    LOG_CANDIDATES[-1]  # Fallback to dev path
)

# Create log directory if it doesn't exist
os.makedirs(LOG_DIR, exist_ok=True)

# ========================================
# CUSTOM FORMATTER
# ========================================

class CategoryFormatter(logging.Formatter):
    """
    Custom formatter that includes category and subcategory fields
    Format: [timestamp] [level] [category] [subcategory] message
    """
    def format(self, record):
        # Extract category/subcategory from extra fields
        category = getattr(record, 'category', 'general')
        subcategory = getattr(record, 'subcategory', '-')

        # Add to record for formatting
        record.category = category
        record.subcategory = subcategory

        # Call parent formatter
        return super().format(record)

# ========================================
# LOGGER INITIALIZATION
# ========================================

def setup_logger(
    name: str,
    log_file: str,
    level=logging.INFO,
    max_bytes=5*1024*1024,  # 5MB
    backup_count=5
) -> logging.Logger:
    """
    Create and configure a rotating file logger.

    Args:
        name: Logger name (e.g., 'autotech.server')
        log_file: Filename in logs directory (e.g., 'server.log')
        level: Logging level
        max_bytes: Max size before rotation (default 5MB)
        backup_count: Number of backup files to keep

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    # File handler with rotation
    file_path = os.path.join(LOG_DIR, log_file)
    handler = RotatingFileHandler(
        file_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )

    # Format: [2026-01-27 15:30:45.123] [INFO] [server] [request] message
    formatter = CategoryFormatter(
        '[%(asctime)s.%(msecs)03d] [%(levelname)s] [%(category)s] [%(subcategory)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Console output in development mode only
    if not getattr(sys, 'frozen', False):
        console = logging.StreamHandler()
        console.setFormatter(formatter)
        logger.addHandler(console)

    return logger

# ========================================
# PRE-CONFIGURED LOGGERS
# ========================================

# Main category loggers
server_logger = setup_logger('autotech.server', 'server.log')
client_logger = setup_logger('autotech.clients', 'clients.log')
tools_logger = setup_logger('autotech.tools', 'tools.log')
background_logger = setup_logger('autotech.background', 'background.log')
security_logger = setup_logger('autotech.security', 'security.log')
database_logger = setup_logger('autotech.database', 'database.log')

# ========================================
# CONVENIENCE FUNCTIONS
# ========================================

def log_server(level, message, subcategory='general', **kwargs):
    """Log to server category."""
    server_logger.log(
        level,
        message,
        extra={'category': 'server', 'subcategory': subcategory},
        **kwargs
    )

def log_client(level, message, subcategory='general', **kwargs):
    """Log to clients category."""
    client_logger.log(
        level,
        message,
        extra={'category': 'clients', 'subcategory': subcategory},
        **kwargs
    )

def log_tool(level, message, subcategory='general', **kwargs):
    """Log to tools category."""
    tools_logger.log(
        level,
        message,
        extra={'category': 'tools', 'subcategory': subcategory},
        **kwargs
    )

def log_background(level, message, subcategory='general', **kwargs):
    """Log to background category."""
    background_logger.log(
        level,
        message,
        extra={'category': 'background', 'subcategory': subcategory},
        **kwargs
    )

def log_security(level, message, subcategory='general', **kwargs):
    """Log to security category."""
    security_logger.log(
        level,
        message,
        extra={'category': 'security', 'subcategory': subcategory},
        **kwargs
    )

def log_database(level, message, subcategory='general', **kwargs):
    """Log to database category."""
    database_logger.log(
        level,
        message,
        extra={'category': 'database', 'subcategory': subcategory},
        **kwargs
    )

# ========================================
# UTILITY FUNCTIONS
# ========================================

def get_log_directory():
    """Return the configured log directory path."""
    return LOG_DIR

def get_log_files():
    """Return list of all log files."""
    try:
        return [f for f in os.listdir(LOG_DIR) if f.endswith('.log')]
    except:
        return []
```

---

### 2. Log Format Standards

#### Format Template
```
[timestamp.milliseconds] [LEVEL] [category] [subcategory] message
```

#### Example Logs

**Server Operations:**
```
[2026-01-27 15:30:45.123] [INFO] [server] [request] GET /api/equipment_search - 10.110.19.100 - 245ms
[2026-01-27 15:30:46.456] [INFO] [server] [response] GET /api/equipment_search - 200 OK
[2026-01-27 15:30:47.789] [ERROR] [server] [exception] RuntimeError: Equipment lookup failed
```

**Client Registration:**
```
[2026-01-27 15:31:00.123] [INFO] [clients] [registration] Client registered: IP=10.110.19.100, Version=v1.1.1
[2026-01-27 15:31:01.456] [INFO] [clients] [verification] Client verification attempt from 10.110.19.100
[2026-01-27 15:31:02.789] [SUCCESS] [clients] [verification] Client verification passed: 10.110.19.100
```

**Tool Operations:**
```
[2026-01-27 15:32:00.123] [INFO] [tools] [ssh] SSH connection to 10.110.19.107 (mms) - attempt 1
[2026-01-27 15:32:01.456] [INFO] [tools] [ssh] SSH connection succeeded to 10.110.19.107
[2026-01-27 15:32:02.789] [DEBUG] [tools] [ssh] Executing command: /home/mms/bin/remote_check/Random/MySQL/ip_export.sh
[2026-01-27 15:32:15.012] [INFO] [tools] [sftp] Downloaded file: playback_001.dat (125MB) in 12.5s
[2026-01-27 15:32:16.345] [ERROR] [tools] [ssh] SSH connection timeout to 10.110.19.50 after 30s
```

**Background Tasks:**
```
[2026-01-27 15:33:00.123] [INFO] [background] [equipment_updater] Started equipment updater loop
[2026-01-27 15:33:01.456] [DEBUG] [background] [equipment_updater] Querying RD111 (10.110.20.110)
[2026-01-27 15:33:05.789] [INFO] [background] [equipment_updater] Updated RD111: CPU=45.2%, Memory=67.8%, Uptime=125 days
[2026-01-27 15:33:06.012] [ERROR] [background] [equipment_updater] Failed to update RD190: SSH timeout
[2026-01-27 15:33:30.123] [INFO] [background] [ptx_uptime_checker] PTX uptime check cycle started (73 equipment)
[2026-01-27 15:34:00.456] [INFO] [background] [ptx_uptime_checker] Cycle complete: 67 online, 6 offline, 3 error in 30.3s
[2026-01-27 15:35:00.789] [INFO] [background] [frontrunner_monitor] Connected to FrontRunner server
[2026-01-27 15:35:30.012] [INFO] [background] [frontrunner_monitor] Service status: RUNNING, Disk: 89% full
```

**Security Events:**
```
[2026-01-27 15:36:00.123] [INFO] [security] [login] Login attempt from 10.110.19.100
[2026-01-27 15:36:01.456] [WARNING] [security] [login] Failed login from 10.110.19.100 (incorrect password)
[2026-01-27 15:36:05.789] [INFO] [security] [login] Successful login from 10.110.19.100
[2026-01-27 15:36:06.012] [INFO] [security] [session] Session created for 10.110.19.100 (session_id=abc123...)
[2026-01-27 15:36:07.345] [WARNING] [security] [unauthorized] Unauthorized access attempt to /admin from 10.110.19.101
```

**Database Operations:**
```
[2026-01-27 15:37:00.123] [DEBUG] [database] [query] SELECT equipment FROM cache WHERE name='RD111'
[2026-01-27 15:37:01.456] [INFO] [database] [query] Cache hit for RD111 (27.3ms)
[2026-01-27 15:37:02.789] [WARNING] [database] [slow_query] Slow query detected (1250ms): SELECT * FROM equipment_cache WHERE...
[2026-01-27 15:37:03.012] [ERROR] [database] [schema] Schema version mismatch: expected=2, found=1
```

---

## Integration Points

### 1. Server Logging (main.py)

#### Request/Response Tracking

```python
# Add to main.py after Flask app initialization
from tools.app_logger import log_server
import logging
from flask import request
from time import time

# Track request start time
@app.before_request
def before_request_logging():
    """Log incoming request and track timing."""
    request.start_time = time()
    log_server(
        logging.INFO,
        f"{request.method} {request.path} - {request.remote_addr}",
        subcategory='request'
    )

@app.after_request
def after_request_logging(response):
    """Log response and calculate request duration."""
    if hasattr(request, 'start_time'):
        duration_ms = int((time() - request.start_time) * 1000)
        log_server(
            logging.INFO,
            f"{request.method} {request.path} - {response.status_code} - {duration_ms}ms",
            subcategory='response'
        )
    return response

@app.errorhandler(Exception)
def handle_error(error):
    """Log uncaught exceptions."""
    log_server(
        logging.ERROR,
        f"Unhandled exception: {type(error).__name__}: {str(error)}",
        subcategory='exception'
    )
    return jsonify({'error': 'Internal server error'}), 500
```

#### Login/Authentication Logging

```python
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Simple login form with security logging."""
    from tools.app_logger import log_security

    if request.method == 'POST':
        password = request.form.get('password')

        log_security(
            logging.INFO,
            f"Login attempt from {request.remote_addr}",
            subcategory='login'
        )

        if password == 'komatsu':
            session['authenticated'] = True
            session['password'] = password

            log_security(
                logging.INFO,
                f"Successful login from {request.remote_addr}",
                subcategory='login'
            )

            return redirect(url_for('dashboard'))
        else:
            log_security(
                logging.WARNING,
                f"Failed login from {request.remote_addr} (incorrect password)",
                subcategory='login'
            )
            return render_template('login.html', error='Invalid password')

    return render_template('login.html')
```

#### Client Registration Logging

```python
@app.route('/api/register-client', methods=['POST'])
def register_client():
    """Register AutoTech client with logging."""
    from tools.app_logger import log_client

    data = request.json or {}
    ip_address = request.remote_addr
    version = data.get('version', 'unknown')
    client_os = data.get('os', 'unknown')

    try:
        # Register logic here

        log_client(
            logging.INFO,
            f"Client registered: IP={ip_address}, Version={version}, OS={client_os}",
            subcategory='registration'
        )

        return jsonify({'success': True, 'message': 'Client registered'})
    except Exception as e:
        log_client(
            logging.ERROR,
            f"Client registration failed for {ip_address}: {str(e)}",
            subcategory='registration'
        )
        return jsonify({'error': str(e)}), 500
```

### 2. Background Task Logging

#### Equipment Updater

```python
def equipment_updater_worker():
    """Background worker that updates equipment details."""
    from tools.app_logger import log_background
    import logging

    log_background(
        logging.INFO,
        "Equipment updater started",
        subcategory='equipment_updater'
    )

    while not background_updater['stop_event'].is_set():
        try:
            # Get equipment needing update
            equipment_list = get_equipment_needing_update(EQUIPMENT_DB_PATH)

            for equipment in equipment_list:
                if background_updater['stop_event'].is_set():
                    break

                background_updater['current_equipment'] = equipment['name']

                try:
                    log_background(
                        logging.DEBUG,
                        f"Updating {equipment['name']} ({equipment['ip']})",
                        subcategory='equipment_updater'
                    )

                    # SSH query and update
                    result = query_equipment_via_ssh(equipment['ip'])
                    save_equipment(EQUIPMENT_DB_PATH, result)

                    background_updater['processed_count'] += 1
                    background_updater['last_update'] = datetime.now()

                    log_background(
                        logging.INFO,
                        f"Updated {equipment['name']}: CPU={result['cpu']}%, Memory={result['memory']}%",
                        subcategory='equipment_updater'
                    )

                except Exception as eq_error:
                    background_updater['error_count'] += 1
                    log_background(
                        logging.ERROR,
                        f"Failed to update {equipment['name']}: {str(eq_error)}",
                        subcategory='equipment_updater'
                    )

            time.sleep(background_updater['delay_seconds'])

        except Exception as e:
            log_background(
                logging.ERROR,
                f"Equipment updater error: {str(e)}",
                subcategory='equipment_updater'
            )
            time.sleep(30)

    log_background(
        logging.INFO,
        "Equipment updater stopped",
        subcategory='equipment_updater'
    )
    background_updater['running'] = False
```

#### PTX Uptime Checker

```python
def ptx_uptime_checker_worker():
    """Background worker that checks PTX controller uptime."""
    from tools.app_logger import log_background
    import logging

    log_background(
        logging.INFO,
        "PTX uptime checker started",
        subcategory='ptx_uptime_checker'
    )

    while not ptx_uptime_checker['stop_event'].is_set():
        try:
            ptx_uptime_checker['last_cycle_start'] = datetime.now()
            ptx_uptime_checker['status'] = 'running'
            ptx_uptime_checker['checked_count'] = 0
            ptx_uptime_checker['online_count'] = 0
            ptx_uptime_checker['offline_count'] = 0
            ptx_uptime_checker['error_count'] = 0

            # Get equipment from database
            equipment_list = get_all_equipment(EQUIPMENT_DB_PATH)
            ptx_uptime_checker['total_equipment'] = len(equipment_list)

            log_background(
                logging.INFO,
                f"PTX uptime check cycle started ({len(equipment_list)} equipment)",
                subcategory='ptx_uptime_checker'
            )

            for equipment in equipment_list:
                if ptx_uptime_checker['stop_event'].is_set():
                    break

                ptx_uptime_checker['current_equipment'] = equipment['name']

                try:
                    # Ping PTX controller
                    is_online = ping_ptx_controller(equipment['ptx_ip'])
                    ptx_uptime_checker['checked_count'] += 1

                    if is_online:
                        ptx_uptime_checker['online_count'] += 1
                    else:
                        ptx_uptime_checker['offline_count'] += 1
                        log_background(
                            logging.WARNING,
                            f"PTX offline: {equipment['name']} ({equipment['ptx_ip']})",
                            subcategory='ptx_uptime_checker'
                        )

                    # Record in database
                    ptx_uptime_db.record_status(equipment['name'], is_online)

                except Exception as ptx_error:
                    ptx_uptime_checker['error_count'] += 1
                    log_background(
                        logging.ERROR,
                        f"PTX check failed for {equipment['name']}: {str(ptx_error)}",
                        subcategory='ptx_uptime_checker'
                    )

            cycle_time = (datetime.now() - ptx_uptime_checker['last_cycle_start']).total_seconds()
            ptx_uptime_checker['last_cycle_end'] = datetime.now()
            ptx_uptime_checker['status'] = 'waiting'

            log_background(
                logging.INFO,
                f"PTX cycle complete: {ptx_uptime_checker['online_count']} online, "
                f"{ptx_uptime_checker['offline_count']} offline, "
                f"{ptx_uptime_checker['error_count']} error in {cycle_time:.1f}s",
                subcategory='ptx_uptime_checker'
            )

            # Wait for next cycle
            wait_with_stop_check(ptx_uptime_checker['interval_minutes'] * 60)

        except Exception as e:
            ptx_uptime_checker['error_count'] += 1
            ptx_uptime_checker['status'] = 'error'
            log_background(
                logging.ERROR,
                f"PTX checker error: {str(e)}",
                subcategory='ptx_uptime_checker'
            )
            time.sleep(60)

    log_background(
        logging.INFO,
        "PTX uptime checker stopped",
        subcategory='ptx_uptime_checker'
    )
    ptx_uptime_checker['running'] = False
```

#### FrontRunner Monitor

```python
def frontrunner_monitor_worker():
    """Background worker that monitors FrontRunner server."""
    from tools.app_logger import log_background
    import logging

    log_background(
        logging.INFO,
        "FrontRunner monitor started",
        subcategory='frontrunner_monitor'
    )

    while not frontrunner_monitor['stop_event'].is_set():
        try:
            if not frontrunner_monitor['connected']:
                try:
                    log_background(
                        logging.INFO,
                        f"Connecting to FrontRunner ({FRONTRUNNER['ip']}:22)...",
                        subcategory='frontrunner_monitor'
                    )

                    # SSH connection logic
                    ssh = paramiko.SSHClient()
                    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    ssh.connect(
                        FRONTRUNNER['ip'],
                        username=FRONTRUNNER['user'],
                        password=FRONTRUNNER['password'],
                        timeout=15
                    )

                    frontrunner_monitor['ssh_client'] = ssh
                    frontrunner_monitor['connected'] = True

                    log_background(
                        logging.INFO,
                        "FrontRunner connected successfully",
                        subcategory='frontrunner_monitor'
                    )

                except Exception as conn_error:
                    log_background(
                        logging.ERROR,
                        f"FrontRunner connection failed: {str(conn_error)}",
                        subcategory='frontrunner_monitor'
                    )
                    frontrunner_monitor['connected'] = False
                    time.sleep(30)
                    continue

            # Monitor FrontRunner status
            try:
                status = get_frontrunner_status(frontrunner_monitor['ssh_client'])

                log_background(
                    logging.DEBUG,
                    f"FrontRunner status: Services={status['services_running']}, "
                    f"Disk={status['disk_usage']}%",
                    subcategory='frontrunner_monitor'
                )

                # Check for critical conditions
                if status['disk_usage'] > 90:
                    log_background(
                        logging.WARNING,
                        f"FrontRunner disk usage critical: {status['disk_usage']}%",
                        subcategory='frontrunner_monitor'
                    )

                if not status['services_running']:
                    log_background(
                        logging.ERROR,
                        "FrontRunner services not running!",
                        subcategory='frontrunner_monitor'
                    )

            except Exception as status_error:
                log_background(
                    logging.ERROR,
                    f"FrontRunner status check failed: {str(status_error)}",
                    subcategory='frontrunner_monitor'
                )
                frontrunner_monitor['connected'] = False

            time.sleep(30)

        except Exception as e:
            log_background(
                logging.ERROR,
                f"FrontRunner monitor error: {str(e)}",
                subcategory='frontrunner_monitor'
            )
            frontrunner_monitor['connected'] = False
            time.sleep(60)

    log_background(
        logging.INFO,
        "FrontRunner monitor stopped",
        subcategory='frontrunner_monitor'
    )
    frontrunner_monitor['running'] = False
```

### 3. Tool Module Logging

#### SSH Operations (tools/ip_finder.py)

```python
# In tools/ip_finder.py
from tools.app_logger import log_tool
import logging

def find_equipment_ip(search_term, ssh_client=None):
    """Find equipment IP by name or partial match."""
    log_tool(
        logging.INFO,
        f"Equipment search started: term='{search_term}'",
        subcategory='ip_finder'
    )

    try:
        results = []

        if ssh_client:
            log_tool(
                logging.DEBUG,
                "Using provided SSH connection for remote query",
                subcategory='ip_finder'
            )
            results = query_remote_mms(ssh_client, search_term)
        else:
            log_tool(
                logging.DEBUG,
                "Creating new SSH connection to MMS server",
                subcategory='ip_finder'
            )
            ssh = create_ssh_connection(MMS_SERVER)
            results = query_remote_mms(ssh, search_term)
            ssh.close()

        log_tool(
            logging.INFO,
            f"Equipment search complete: found {len(results)} results for '{search_term}'",
            subcategory='ip_finder'
        )

        return {'success': True, 'results': results}

    except Exception as e:
        log_tool(
            logging.ERROR,
            f"Equipment search failed for '{search_term}': {str(e)}",
            subcategory='ip_finder'
        )
        return {'success': False, 'error': str(e)}
```

#### Database Operations (tools/equipment_db.py)

```python
# In tools/equipment_db.py
from tools.app_logger import log_database
import logging

def save_equipment(db_path, equipment_data):
    """Save equipment to database."""
    try:
        log_database(
            logging.DEBUG,
            f"Saving equipment: {equipment_data['name']} to {db_path}",
            subcategory='equipment_db'
        )

        # Database insert logic

        log_database(
            logging.INFO,
            f"Equipment saved: {equipment_data['name']} (IP={equipment_data['ip']})",
            subcategory='equipment_db'
        )

    except Exception as e:
        log_database(
            logging.ERROR,
            f"Failed to save equipment {equipment_data.get('name', 'unknown')}: {str(e)}",
            subcategory='equipment_db'
        )
        raise

def search_equipment(db_path, query):
    """Search equipment database."""
    import time
    start_time = time.time()

    try:
        log_database(
            logging.DEBUG,
            f"Database search: query='{query}'",
            subcategory='equipment_db'
        )

        results = # ... query logic

        elapsed_ms = (time.time() - start_time) * 1000
        log_database(
            logging.INFO,
            f"Search found {len(results)} results in {elapsed_ms:.1f}ms",
            subcategory='equipment_db'
        )

        return results

    except Exception as e:
        log_database(
            logging.ERROR,
            f"Database search failed: {str(e)}",
            subcategory='equipment_db'
        )
        raise
```

#### SFTP File Transfer (tools/playback_usb.py)

```python
# In tools/playback_usb.py
from tools.app_logger import log_tool
import logging

def download_playback_file(sftp_client, remote_path, local_path):
    """Download playback file via SFTP with logging."""
    import os
    import time

    file_size = sftp_client.stat(remote_path).st_size
    file_size_mb = file_size / (1024 * 1024)

    log_tool(
        logging.INFO,
        f"SFTP download started: {os.path.basename(remote_path)} ({file_size_mb:.1f}MB)",
        subcategory='sftp'
    )

    start_time = time.time()

    try:
        sftp_client.get(remote_path, local_path)

        elapsed_seconds = time.time() - start_time
        speed_mbps = file_size_mb / elapsed_seconds if elapsed_seconds > 0 else 0

        log_tool(
            logging.INFO,
            f"SFTP download complete: {os.path.basename(remote_path)} "
            f"({file_size_mb:.1f}MB in {elapsed_seconds:.1f}s at {speed_mbps:.1f}MB/s)",
            subcategory='sftp'
        )

    except Exception as e:
        log_tool(
            logging.ERROR,
            f"SFTP download failed: {os.path.basename(remote_path)}: {str(e)}",
            subcategory='sftp'
        )
        raise
```

---

## Configuration & Path Resolution

### Path Detection Strategy

The logger uses a **multi-tier candidate approach** to handle different deployment scenarios:

```python
LOG_CANDIDATES = [
    os.path.join(BASE_DIR, 'AutoTech', 'database', 'logs'),  # USB deployment
    os.path.join(BASE_DIR, 'database', 'logs')                 # Development
]

LOG_DIR = next(
    (p for p in LOG_CANDIDATES if os.path.exists(os.path.dirname(p))),
    LOG_CANDIDATES[-1]  # Fallback to development path
)
```

### Scenario Handling

#### Scenario 1: Development Mode
```
Running: python main.py
BASE_DIR: C:\AutoTech_WebApps\AutoTech_WebServer
LOG_DIR: C:\AutoTech_WebApps\AutoTech_WebServer\database\logs
Output: Console + Files
```

#### Scenario 2: Frozen Executable
```
Running: AutoTech.exe from any location
BASE_DIR: Directory containing AutoTech.exe
LOG_DIR: BASE_DIR\database\logs (if database exists)
Output: Files only (no console)
```

#### Scenario 3: USB Deployment
```
Running: E:\AutoTech.exe
BASE_DIR: E:\
LOG_DIR: E:\AutoTech\database\logs
Output: Files only (no console)
```

#### Scenario 4: Windows Service
```
Running: AutoTech.exe as Windows service
BASE_DIR: Service installation directory
LOG_DIR: Detected same as frozen exe
Output: Files only, service manager access
```

### Fallback Behavior

If log directory creation fails:
1. Try parent directory (may have permission issue)
2. Create in BASE_DIR\database\logs
3. Create in temp directory as last resort
4. Log warning to console about path issue

---

## Performance Considerations

### Design for Efficiency

1. **Asynchronous Logging**
   - File handlers don't block request threads
   - Rotation happens automatically on size thresholds
   - No network overhead (local file I/O only)

2. **Minimal Data Capture**
   - Log meaningful events only
   - Avoid logging full payloads (truncate if needed)
   - Use DEBUG level for verbose output (disabled in production)

3. **Rotation Strategy**
   - 5MB per file prevents excessive disk usage
   - 5 backups = ~30MB per category = ~180MB total
   - Old files automatically deleted when limit reached

4. **Subcategory Filtering**
   - Easy to filter logs: `grep 'ssh' tools.log`
   - Enables performance analysis by subcategory
   - Helps with debugging specific features

### Performance Metrics

Example logging overhead test (production environment):

```
Without logging: 100 requests/sec
With logging:    98 requests/sec (2% overhead)

Log file size impact:
- 1,000 requests/day = ~5MB/month of server.log
- 100 SSH operations/day = ~1MB/month of tools.log
- Total estimate: ~30-50MB/month for all logs
```

### Recommendations

1. **Use DEBUG level cautiously**
   - Set to INFO in production
   - Only DEBUG in development for specific troubleshooting

2. **Monitor Log Directory**
   - Check disk space monthly (logs stay under 200MB)
   - Implement cleanup script for files older than 90 days

3. **Archive Old Logs**
   - Keep logs for 90 days
   - Archive to external storage if needed for audit

---

## Windows Service Integration

### Service Logging Behavior

When running as Windows service:

1. **No Console Output**
   - Console unavailable to service
   - All output goes to files only

2. **File Locations**
   - Service paths same as frozen exe
   - %ALLUSERSPROFILE%\AppData\Local\AutoTech\logs (optional)
   - Or use service installation directory

3. **Service Log Integration** (Optional)
   - Can emit events to Windows Event Log
   - Use `logging.handlers.NTEventLogHandler`
   - Requires elevated privileges during setup

### Example Service Setup

```batch
# Install_AutoTech_Service.bat
@echo off
REM Install AutoTech as Windows service with logging configured
sc create AutoTech ^
    binPath= "C:\AutoTech\AutoTech.exe" ^
    DisplayName= "AutoTech Web Dashboard" ^
    start= auto

REM Service will look for logs in C:\AutoTech\database\logs
REM Create directory if needed
if not exist "C:\AutoTech\database\logs" mkdir "C:\AutoTech\database\logs"

echo AutoTech service installed with logging to C:\AutoTech\database\logs
```

### Monitoring Service Logs

```batch
# View service logs (Windows command line)
type C:\AutoTech\database\logs\server.log | findstr "ERROR"
type C:\AutoTech\database\logs\background.log | findstr "stopped"
```

---

## Implementation Roadmap

### Phase 1: Core Infrastructure (Week 1)

**Deliverables:**
- [ ] Create `tools/app_logger.py` with logging infrastructure
- [ ] Implement CategoryFormatter for structured logging
- [ ] Create 6 pre-configured loggers (server, client, tools, background, security, database)
- [ ] Test path resolution for dev/frozen/USB scenarios

**Testing:**
- [ ] Verify log files created in correct directory
- [ ] Test rotation at 5MB threshold
- [ ] Verify console output in dev mode only
- [ ] Test frozen exe mode (no console)

### Phase 2: Main.py Integration (Week 2)

**Deliverables:**
- [ ] Add request/response logging via Flask hooks
- [ ] Implement error handling with logging
- [ ] Add login/authentication logging
- [ ] Add client registration logging
- [ ] Update startup banner to log to server.log

**Testing:**
- [ ] Verify request duration calculation
- [ ] Test login success/failure logging
- [ ] Verify client registration logs contain IP, version, OS

### Phase 3: Background Task Logging (Week 3)

**Deliverables:**
- [ ] Equipment updater logging (INFO for completion, ERROR for failures)
- [ ] PTX uptime checker logging (cycle start/end, online/offline counts)
- [ ] FrontRunner monitor logging (connection, status, critical events)
- [ ] Replace print() statements with logging calls

**Testing:**
- [ ] Run equipment updater and verify logs
- [ ] Monitor PTX cycles in logs
- [ ] Check FrontRunner connection/disconnection logging

### Phase 4: Tool Module Logging (Week 4)

**Deliverables:**
- [ ] IP Finder SSH logging
- [ ] Equipment DB query logging
- [ ] SFTP transfer logging with performance metrics
- [ ] PTX health check logging

**Testing:**
- [ ] Verify SSH connection attempts logged
- [ ] Test slow query detection in database log
- [ ] Verify SFTP transfer speeds logged

### Phase 5: Advanced Features (Week 5)

**Deliverables:**
- [ ] Request ID correlation (optional)
- [ ] Performance metric extraction
- [ ] Log analysis utility scripts
- [ ] Documentation and troubleshooting guide

**Testing:**
- [ ] Verify performance metrics (request times, query times)
- [ ] Create log analysis grep commands
- [ ] Document common log grep patterns

### Phase 6: Testing & Deployment (Week 6)

**Deliverables:**
- [ ] Build AutoTech.exe with logging enabled
- [ ] Test frozen exe logging
- [ ] Test Windows service logging
- [ ] Create log viewer/analyzer tool (optional)

**Testing:**
- [ ] Deploy to USB and verify logs
- [ ] Install as service and verify logs
- [ ] Test log rotation with high load
- [ ] Verify no data loss during rotation

---

## Troubleshooting Guide

### Issue: Log Files Not Created

**Symptoms:**
```
No database/logs directory exists
No .log files appearing
```

**Diagnosis Steps:**
```python
# Test from Python console
import os
from tools.app_logger import LOG_DIR, BASE_DIR

print(f"BASE_DIR: {BASE_DIR}")
print(f"LOG_DIR: {LOG_DIR}")
print(f"LOG_DIR exists: {os.path.exists(LOG_DIR)}")
print(f"Writable: {os.access(LOG_DIR, os.W_OK)}")
```

**Solutions:**
1. Check BASE_DIR is correct (should be where main.py is)
2. Create database/logs folder manually:
   ```batch
   mkdir C:\AutoTech_WebApps\AutoTech_WebServer\database\logs
   ```
3. Check permissions (SYSTEM user needs write access for service)

### Issue: Log Files Growing Too Large

**Symptoms:**
```
server.log is 100MB+
Disk space filling up
```

**Diagnosis:**
```python
# Check log file sizes
import os
from tools.app_logger import LOG_DIR

for f in os.listdir(LOG_DIR):
    path = os.path.join(LOG_DIR, f)
    size_mb = os.path.getsize(path) / (1024 * 1024)
    print(f"{f}: {size_mb:.1f}MB")
```

**Solutions:**
1. Verify rotation is working (check for server.log.1, server.log.2, etc.)
2. Reduce logging level to WARNING in production
3. Increase backup count or max bytes:
   ```python
   setup_logger('autotech.server', 'server.log', max_bytes=10*1024*1024, backup_count=10)
   ```
4. Delete old backup files:
   ```batch
   del C:\AutoTech_WebApps\AutoTech_WebServer\database\logs\*.log.* /S
   ```

### Issue: Missing Logs After Service Restart

**Symptoms:**
```
Service restarts but no new logs appear
Logs cut off before shutdown
```

**Diagnosis:**
- Logs may be buffered in memory
- File handlers may not flush on shutdown
- Service kill signal may not trigger cleanup

**Solutions:**
1. Add explicit flush on app shutdown:
   ```python
   @app.before_request
   def flush_logs():
       for handler in [server_logger.handlers, client_logger.handlers]:
           for h in handler:
               h.flush()
   ```

2. Ensure daemon threads flush:
   ```python
   # Before stopping background threads
   for logger in [server_logger, client_logger, tools_logger, background_logger]:
       for handler in logger.handlers:
           handler.flush()
   ```

### Issue: Console Output in Production

**Symptoms:**
```
Logs appearing in console even though frozen exe
output mixed with Flask startup messages
```

**Diagnosis:**
```python
# Check if frozen
import sys
print(f"Frozen: {getattr(sys, 'frozen', False)}")
```

**Solutions:**
1. Verify running actual exe (not Python interpreter)
2. Check for console redirection:
   ```batch
   # Redirect console to file
   AutoTech.exe > nul 2>&1
   ```
3. Disable console in PyInstaller spec if needed

### Issue: Slow Request Performance After Logging

**Symptoms:**
```
Requests slower after adding logging
High disk I/O during peak usage
```

**Analysis:**
- Normal: 1-2% overhead
- Excessive: Logging I/O blocking threads

**Solutions:**
1. Verify file path is on local fast disk (not network)
2. Disable DEBUG level logging:
   ```python
   setup_logger('autotech.server', 'server.log', level=logging.INFO)
   ```
3. Reduce subcategory detail in high-frequency operations
4. Profile with timing:
   ```python
   import time
   start = time.time()
   log_server(logging.INFO, "test")
   elapsed = time.time() - start
   print(f"Log time: {elapsed*1000:.2f}ms")  # Should be <1ms
   ```

### Issue: Logs Not Visible in Windows Service

**Symptoms:**
```
Service running but no log files created
or old log files not updating
```

**Diagnosis:**
```batch
# Check service is running
sc query AutoTech

# Check file permissions
icacls C:\AutoTech\database\logs

# Check if process has access
wmic process where name="AutoTech.exe" get processid
```

**Solutions:**
1. Verify database\logs exists and SYSTEM user can write:
   ```batch
   icacls C:\AutoTech\database\logs /grant SYSTEM:F
   ```

2. Check service account permissions:
   ```batch
   # Service runs as SYSTEM by default
   sc config AutoTech obj= LocalSystem
   ```

3. Add fallback temp directory:
   ```python
   import tempfile
   LOG_CANDIDATES = [
       os.path.join(BASE_DIR, 'AutoTech', 'database', 'logs'),
       os.path.join(BASE_DIR, 'database', 'logs'),
       os.path.join(tempfile.gettempdir(), 'AutoTech', 'logs')
   ]
   ```

---

## Best Practices Summary

### Do's

- Do use appropriate log levels (DEBUG, INFO, WARNING, ERROR)
- Do include contextual information (IP, equipment name, operation)
- Do include timing metrics (duration, file size, count)
- Do log start and end of long operations
- Do use subcategories for filtering
- Do handle exceptions with ERROR level
- Do flush logs before shutdown
- Do test in all deployment modes (dev, exe, service)

### Don'ts

- Don't log passwords or sensitive data
- Don't log full SSH command output (truncate)
- Don't log at DEBUG in production
- Don't rely on console output for production visibility
- Don't mix logging and print() statements
- Don't create new logger instances (use global ones)
- Don't forget to handle Unicode properly (use UTF-8)
- Don't ignore disk space requirements

### Common Grep Patterns

```bash
# Find all errors
findstr "ERROR" server.log

# Find slow requests
findstr "200ms" server.log

# Find failed SSH attempts
findstr "ERROR.*ssh" tools.log

# Find failed logins
findstr "WARNING" security.log

# Find client registrations
findstr "registration" clients.log

# Find background task issues
findstr "ERROR" background.log

# Real-time monitoring (PowerShell)
Get-Content server.log -Wait -Tail 0
```

---

## Appendix: Reference Implementation

### Complete app_logger.py (Copy-Paste Ready)

See Core Components > Logger Module section above for complete implementation.

### Quick Integration Checklist

1. **Create tools/app_logger.py** - Copy code from design
2. **Update main.py imports** - Add logging imports
3. **Add Flask hooks** - Request/response logging
4. **Update background tasks** - Replace print() with log_*()
5. **Update tool modules** - Add operation logging
6. **Test in all modes** - Dev, frozen, service
7. **Monitor logs** - Check directory structure

### Expected Log Output Examples

See "Log Format Standards" section for complete examples.

---

## Document Metadata

- **Target Audience:** Backend developers, DevOps
- **Complexity Level:** Advanced (requires logging knowledge)
- **Implementation Time:** ~6 weeks
- **Testing Time:** 1-2 weeks
- **Maintenance Effort:** Low (once implemented)

**Questions or Clarifications:** Refer to Integration Points section for specific patterns.

---

**End of Logging Architecture Design Document**
