# AutoTech Logging Implementation Guide
## Quick Reference for Implementation Tasks

**Document Version:** 1.0
**Purpose:** Provide copy-paste ready code snippets and step-by-step implementation instructions

---

## Table of Contents

1. [Code Snippets by Category](#code-snippets-by-category)
2. [Step-by-Step Implementation](#step-by-step-implementation)
3. [Testing Procedures](#testing-procedures)
4. [Common Patterns](#common-patterns)
5. [Troubleshooting Checklist](#troubleshooting-checklist)

---

## Code Snippets by Category

### 1. Complete tools/app_logger.py

This is the foundation module. Save as `C:\AutoTech_WebApps\AutoTech_WebServer\tools\app_logger.py`

```python
# tools/app_logger.py
"""
AutoTech Application Logger - Structured logging system with rotation
Provides separate log files for different operational concerns
Works in development, frozen exe, and Windows service modes
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from datetime import datetime


# ========================================
# PATH RESOLUTION (Development vs. Frozen)
# ========================================

if getattr(sys, 'frozen', False):
    # Running as PyInstaller executable (AutoTech.exe)
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # Running as Python script (development)
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ========================================
# LOG DIRECTORY DETECTION
# ========================================

# Try USB path first, then development path
LOG_CANDIDATES = [
    os.path.join(BASE_DIR, 'AutoTech', 'database', 'logs'),  # USB: E:\AutoTech\database\logs
    os.path.join(BASE_DIR, 'database', 'logs')                 # Dev: project\database\logs
]

# Use first existing path, fallback to development
LOG_DIR = next(
    (p for p in LOG_CANDIDATES if os.path.exists(os.path.dirname(p))),
    LOG_CANDIDATES[-1]
)

# Ensure log directory exists
try:
    os.makedirs(LOG_DIR, exist_ok=True)
except PermissionError:
    # If database folder doesn't exist, create logs in temp
    import tempfile
    LOG_DIR = os.path.join(tempfile.gettempdir(), 'AutoTech', 'logs')
    os.makedirs(LOG_DIR, exist_ok=True)


# ========================================
# CUSTOM FORMATTER
# ========================================

class CategoryFormatter(logging.Formatter):
    """
    Custom formatter that includes category and subcategory fields.
    Format: [timestamp.ms] [LEVEL] [category] [subcategory] message
    """

    def format(self, record):
        # Extract category/subcategory from extra fields
        category = getattr(record, 'category', 'general')
        subcategory = getattr(record, 'subcategory', '-')

        # Assign to record for format string
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
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        max_bytes: Max file size before rotation (default 5MB)
        backup_count: Number of backup files to keep (default 5)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Prevent duplicate handlers on reload
    if logger.handlers:
        return logger

    # File handler with rotation
    file_path = os.path.join(LOG_DIR, log_file)

    try:
        handler = RotatingFileHandler(
            file_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
    except Exception as e:
        print(f"Warning: Could not create file handler for {file_path}: {e}")
        # Create a null handler as fallback
        handler = logging.NullHandler()

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

# Main category loggers - one per operational domain
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
    """Log to server.log"""
    server_logger.log(
        level,
        message,
        extra={'category': 'server', 'subcategory': subcategory},
        **kwargs
    )


def log_client(level, message, subcategory='general', **kwargs):
    """Log to clients.log"""
    client_logger.log(
        level,
        message,
        extra={'category': 'clients', 'subcategory': subcategory},
        **kwargs
    )


def log_tool(level, message, subcategory='general', **kwargs):
    """Log to tools.log"""
    tools_logger.log(
        level,
        message,
        extra={'category': 'tools', 'subcategory': subcategory},
        **kwargs
    )


def log_background(level, message, subcategory='general', **kwargs):
    """Log to background.log"""
    background_logger.log(
        level,
        message,
        extra={'category': 'background', 'subcategory': subcategory},
        **kwargs
    )


def log_security(level, message, subcategory='general', **kwargs):
    """Log to security.log"""
    security_logger.log(
        level,
        message,
        extra={'category': 'security', 'subcategory': subcategory},
        **kwargs
    )


def log_database(level, message, subcategory='general', **kwargs):
    """Log to database.log"""
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
    """Return list of all log files in directory."""
    try:
        return sorted([f for f in os.listdir(LOG_DIR) if f.endswith('.log')])
    except:
        return []


def get_log_file_info(log_file):
    """Get information about a log file."""
    file_path = os.path.join(LOG_DIR, log_file)
    if os.path.exists(file_path):
        size_bytes = os.path.getsize(file_path)
        size_mb = size_bytes / (1024 * 1024)
        mtime = os.path.getmtime(file_path)
        return {
            'name': log_file,
            'size_bytes': size_bytes,
            'size_mb': round(size_mb, 2),
            'modified': datetime.fromtimestamp(mtime).isoformat()
        }
    return None


def get_all_log_info():
    """Get information about all log files."""
    log_info = []
    for log_file in get_log_files():
        info = get_log_file_info(log_file)
        if info:
            log_info.append(info)
    return log_info
```

### 2. Flask Integration - Request/Response Logging

Add this to main.py after Flask app creation:

```python
# Add these imports at the top of main.py
from tools.app_logger import (
    log_server, log_security, log_client,
    get_log_directory, get_log_files
)
from time import time as current_time

# Add these after: app = Flask(__name__, ...)

@app.before_request
def before_request_logging():
    """Log incoming request and track timing."""
    request.start_time = current_time()
    request.client_ip = request.remote_addr

    # Log the request
    log_server(
        logging.INFO,
        f"{request.method} {request.path} from {request.remote_addr}",
        subcategory='request'
    )


@app.after_request
def after_request_logging(response):
    """Log response and calculate request duration."""
    if hasattr(request, 'start_time'):
        duration_ms = int((current_time() - request.start_time) * 1000)

        # Determine log level based on status code
        if response.status_code >= 500:
            level = logging.ERROR
        elif response.status_code >= 400:
            level = logging.WARNING
        else:
            level = logging.INFO

        log_server(
            level,
            f"{request.method} {request.path} - {response.status_code} - {duration_ms}ms",
            subcategory='response'
        )

    return response


@app.errorhandler(Exception)
def handle_exception(error):
    """Log uncaught exceptions."""
    log_server(
        logging.ERROR,
        f"Unhandled exception in {request.method} {request.path}: {type(error).__name__}: {str(error)}",
        subcategory='exception'
    )
    import traceback
    log_server(
        logging.DEBUG,
        f"Traceback:\n{traceback.format_exc()}",
        subcategory='exception'
    )
    return jsonify({'error': 'Internal server error'}), 500


# Add startup/shutdown logging
def startup_logging():
    """Log application startup."""
    log_server(
        logging.INFO,
        f"Application started. Base directory: {BASE_DIR}. Log directory: {get_log_directory()}",
        subcategory='startup'
    )
    log_server(
        logging.INFO,
        f"Running on http://localhost:8888 (frozen={getattr(sys, 'frozen', False)})",
        subcategory='startup'
    )


def shutdown_logging():
    """Log application shutdown."""
    log_server(
        logging.INFO,
        "Application shutting down",
        subcategory='shutdown'
    )


# Call startup logging after all initialization
startup_logging()

# Register shutdown hook
import atexit
atexit.register(shutdown_logging)
```

### 3. Authentication Logging

Replace existing login route with this:

```python
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Simple login form with security logging."""
    if request.method == 'POST':
        password = request.form.get('password')
        client_ip = request.remote_addr

        # Log login attempt
        log_security(
            logging.INFO,
            f"Login attempt from {client_ip}",
            subcategory='login'
        )

        if password == 'komatsu':
            session['authenticated'] = True
            session['password'] = password

            # Log successful login
            log_security(
                logging.INFO,
                f"Successful login from {client_ip}",
                subcategory='login'
            )

            return redirect(url_for('dashboard'))
        else:
            # Log failed login
            log_security(
                logging.WARNING,
                f"Failed login attempt from {client_ip} (incorrect password)",
                subcategory='login'
            )
            return render_template('login.html', error='Invalid password')

    return render_template('login.html')


@app.route('/logout')
def logout():
    """Logout and clear session."""
    client_ip = request.remote_addr

    log_security(
        logging.INFO,
        f"Logout from {client_ip}",
        subcategory='logout'
    )

    session.clear()
    return redirect(url_for('login'))
```

### 4. Client Registration Logging

Add this logging to existing register-client route:

```python
@app.route('/api/register-client', methods=['POST'])
def register_client():
    """Register AutoTech client with logging."""
    data = request.json or {}
    ip_address = request.remote_addr
    version = data.get('version', 'unknown')
    client_os = data.get('os', 'unknown')

    log_client(
        logging.INFO,
        f"Client registration attempt from {ip_address} (Version: {version}, OS: {client_os})",
        subcategory='registration'
    )

    try:
        # Existing registration logic here

        log_client(
            logging.INFO,
            f"Client registered successfully: IP={ip_address}, Version={version}, OS={client_os}",
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

### 5. Equipment Updater Logging

Update the equipment_updater_worker function:

```python
def equipment_updater_worker():
    """Background worker that updates equipment details."""
    global background_updater

    log_background(
        logging.INFO,
        "Equipment updater started",
        subcategory='equipment_updater'
    )

    background_updater['running'] = True
    background_updater['status'] = 'running'

    while not background_updater['stop_event'].is_set():
        try:
            # Get equipment needing update
            equipment_list = get_equipment_needing_update(EQUIPMENT_DB_PATH)

            if not equipment_list:
                background_updater['status'] = 'waiting'
                time.sleep(background_updater['delay_seconds'])
                continue

            for equipment in equipment_list:
                if background_updater['stop_event'].is_set():
                    break

                background_updater['current_equipment'] = equipment['name']
                background_updater['status'] = 'updating'

                try:
                    log_background(
                        logging.DEBUG,
                        f"Querying {equipment['name']} ({equipment.get('network_ip', 'unknown')})",
                        subcategory='equipment_updater'
                    )

                    # SSH query logic here
                    result = query_equipment_via_ssh(equipment)

                    # Save to database
                    save_equipment(EQUIPMENT_DB_PATH, result)

                    background_updater['processed_count'] += 1
                    background_updater['last_update'] = datetime.now()

                    log_background(
                        logging.INFO,
                        f"Updated {equipment['name']}: CPU={result.get('cpu', 'N/A')}%, "
                        f"Memory={result.get('memory', 'N/A')}%",
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

            background_updater['status'] = 'waiting'
            time.sleep(5)  # Wait before next cycle

        except Exception as e:
            log_background(
                logging.ERROR,
                f"Equipment updater error: {str(e)}",
                subcategory='equipment_updater'
            )
            background_updater['status'] = 'error'
            time.sleep(30)

    log_background(
        logging.INFO,
        "Equipment updater stopped",
        subcategory='equipment_updater'
    )
    background_updater['running'] = False
    background_updater['status'] = 'stopped'
```

### 6. PTX Uptime Checker Logging

Update ptx_uptime_checker_worker function:

```python
def ptx_uptime_checker_worker():
    """Background worker that checks PTX controller uptime."""
    global ptx_uptime_checker

    log_background(
        logging.INFO,
        "PTX uptime checker started",
        subcategory='ptx_uptime_checker'
    )

    ptx_uptime_checker['running'] = True

    while not ptx_uptime_checker['stop_event'].is_set():
        try:
            ptx_uptime_checker['status'] = 'running'
            ptx_uptime_checker['last_cycle_start'] = datetime.now()
            ptx_uptime_checker['checked_count'] = 0
            ptx_uptime_checker['online_count'] = 0
            ptx_uptime_checker['offline_count'] = 0
            ptx_uptime_checker['error_count'] = 0

            # Get equipment list
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
                    is_online = ping_host(equipment.get('ptx_ip'))
                    ptx_uptime_checker['checked_count'] += 1

                    if is_online:
                        ptx_uptime_checker['online_count'] += 1
                    else:
                        ptx_uptime_checker['offline_count'] += 1
                        log_background(
                            logging.WARNING,
                            f"PTX offline: {equipment['name']} ({equipment.get('ptx_ip', 'unknown')})",
                            subcategory='ptx_uptime_checker'
                        )

                    # Record in database
                    if ptx_uptime_db:
                        ptx_uptime_db.record_status(equipment['name'], is_online)

                except Exception as ptx_error:
                    ptx_uptime_checker['error_count'] += 1
                    log_background(
                        logging.ERROR,
                        f"PTX check failed for {equipment['name']}: {str(ptx_error)}",
                        subcategory='ptx_uptime_checker'
                    )

            # Calculate cycle time
            ptx_uptime_checker['last_cycle_end'] = datetime.now()
            cycle_time = (ptx_uptime_checker['last_cycle_end'] - ptx_uptime_checker['last_cycle_start']).total_seconds()

            log_background(
                logging.INFO,
                f"PTX cycle complete: {ptx_uptime_checker['online_count']} online, "
                f"{ptx_uptime_checker['offline_count']} offline, "
                f"{ptx_uptime_checker['error_count']} error in {cycle_time:.1f}s",
                subcategory='ptx_uptime_checker'
            )

            ptx_uptime_checker['status'] = 'waiting'
            ptx_uptime_checker['next_cycle'] = datetime.now() + timedelta(minutes=ptx_uptime_checker['interval_minutes'])

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
    ptx_uptime_checker['status'] = 'stopped'
```

### 7. Database Query Logging

Add to tools/equipment_db.py:

```python
from tools.app_logger import log_database
import logging
import time

def search_equipment(db_path, query):
    """Search equipment database with timing."""
    start_time = time.time()

    try:
        log_database(
            logging.DEBUG,
            f"Database search: query='{query}'",
            subcategory='equipment_db'
        )

        # Query logic here
        results = # ... your search implementation

        elapsed_ms = (time.time() - start_time) * 1000

        # Log slow queries
        if elapsed_ms > 500:
            log_database(
                logging.WARNING,
                f"Slow query detected ({elapsed_ms:.0f}ms): '{query}'",
                subcategory='equipment_db'
            )
        else:
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

---

## Step-by-Step Implementation

### Step 1: Create tools/app_logger.py

```bash
# Copy the complete tools/app_logger.py code from section 1 above
# Save to: C:\AutoTech_WebApps\AutoTech_WebServer\tools\app_logger.py
```

**Verification:**
```python
# Test from Python console in project directory
from tools.app_logger import (
    log_server, log_client, log_tool,
    log_background, log_security, log_database,
    get_log_directory
)
import logging

print(f"Log directory: {get_log_directory()}")

log_server(logging.INFO, "Test message", subcategory='test')
log_client(logging.INFO, "Test message", subcategory='test')

# Check for new log files
import os
log_dir = get_log_directory()
print(f"Log files: {os.listdir(log_dir)}")
```

Expected output:
```
Log directory: C:\AutoTech_WebApps\AutoTech_WebServer\database\logs
Log files: ['server.log', 'clients.log', 'tools.log', 'background.log', 'security.log', 'database.log']
```

### Step 2: Update main.py Imports

Add to top of main.py (after existing imports):

```python
# Logging imports
from tools.app_logger import (
    log_server, log_client, log_tool,
    log_background, log_security, log_database,
    get_log_directory
)
from time import time as current_time
```

Remove or replace this line:
```python
# OLD (line 90-91):
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# NEW - use the structured logger instead
```

### Step 3: Add Flask Hooks

Add these functions to main.py after Flask app creation:

```python
# Find this line in main.py:
# app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)

# And add these hooks right after:

@app.before_request
def before_request_logging():
    """Log incoming request and track timing."""
    request.start_time = current_time()
    request.client_ip = request.remote_addr
    log_server(
        logging.INFO,
        f"{request.method} {request.path} from {request.remote_addr}",
        subcategory='request'
    )

@app.after_request
def after_request_logging(response):
    """Log response and calculate request duration."""
    if hasattr(request, 'start_time'):
        duration_ms = int((current_time() - request.start_time) * 1000)
        log_server(
            logging.INFO,
            f"{request.method} {request.path} - {response.status_code} - {duration_ms}ms",
            subcategory='response'
        )
    return response

@app.errorhandler(Exception)
def handle_exception(error):
    """Log uncaught exceptions."""
    log_server(
        logging.ERROR,
        f"Unhandled exception: {type(error).__name__}: {str(error)}",
        subcategory='exception'
    )
    return jsonify({'error': 'Internal server error'}), 500
```

### Step 4: Add Startup Logging

Find the `print_startup_banner()` function and add logging call:

```python
def print_startup_banner():
    """Display startup information"""
    # ... existing code ...

    # Add this at the end:
    log_server(
        logging.INFO,
        f"AutoTech started - Server IP: {server_ip}, Port: 8888",
        subcategory='startup'
    )
```

### Step 5: Update Authentication Routes

Find and update the `/login` route:

```python
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Simple login form"""
    if request.method == 'POST':
        password = request.form.get('password')

        log_security(logging.INFO, f"Login attempt from {request.remote_addr}", subcategory='login')

        if password == 'komatsu':
            session['authenticated'] = True
            session['password'] = password

            log_security(logging.INFO, f"Successful login from {request.remote_addr}", subcategory='login')

            return redirect(url_for('dashboard'))
        else:
            log_security(logging.WARNING, f"Failed login from {request.remote_addr}", subcategory='login')
            return render_template('login.html', error='Invalid password')

    return render_template('login.html')
```

### Step 6: Test Basic Logging

```bash
# Run development server
python main.py

# Verify logs are created:
dir C:\AutoTech_WebApps\AutoTech_WebServer\database\logs

# Check contents:
type C:\AutoTech_WebApps\AutoTech_WebServer\database\logs\server.log

# Expected output:
# [2026-01-27 15:30:45.123] [INFO] [server] [startup] AutoTech started...
# [2026-01-27 15:30:46.456] [INFO] [server] [request] GET / from 127.0.0.1
# [2026-01-27 15:30:46.789] [INFO] [server] [response] GET / - 200 - 45ms
```

### Step 7: Update Background Tasks

Update `equipment_updater_worker()`, `ptx_uptime_checker_worker()` etc.

Use the code snippets from section 5-6 above.

### Step 8: Update Tool Modules

Add logging calls to:
- `tools/ip_finder.py` - log SSH queries
- `tools/equipment_db.py` - log database operations
- `tools/ptx_uptime.py` - log PTX operations
- `tools/frontrunner_monitor.py` - log connection/status

---

## Testing Procedures

### Test 1: Development Mode Logging

```bash
# Start development server
cd C:\AutoTech_WebApps\AutoTech_WebServer
python main.py

# Navigate to http://localhost:8888
# Check for console output:
# [2026-01-27 15:30:45.123] [INFO] [server] [request] GET / from 127.0.0.1

# Check log files:
type database\logs\server.log
# Should show all requests/responses
```

### Test 2: Log Rotation

```bash
# Create large log entry to trigger rotation
python -c "
from tools.app_logger import log_server
import logging

for i in range(1000):
    log_server(logging.INFO, 'X' * 5000, subcategory='test')
"

# Check log files:
dir database\logs\server.log*

# Should see server.log and server.log.1
```

### Test 3: Frozen Exe Testing

```bash
# Build frozen exe
python -m pyinstaller AutoTech.spec --noconfirm

# Run exe
dist\AutoTech.exe

# Check logs (NO console output):
dir database\logs
type database\logs\server.log
```

### Test 4: Windows Service Testing

```batch
# Install service
cd "C:\AutoTech_WebApps\AutoTech_WebServer"
tools\Install_AutoTech_Service.bat

# Start service
sc start AutoTech

# Check logs
type database\logs\server.log

# Stop service
sc stop AutoTech
```

### Test 5: Login Logging

```bash
# Navigate to http://localhost:8888/login
# Try wrong password
# Check security.log:
type database\logs\security.log

# Should show:
# [2026-01-27 15:30:45.123] [WARNING] [security] [login] Failed login...

# Login with correct password (komatsu)
# Should show:
# [2026-01-27 15:30:46.456] [INFO] [security] [login] Successful login...
```

---

## Common Patterns

### Pattern 1: Operation with Timing

```python
from tools.app_logger import log_tool
import logging
import time

def perform_operation():
    start_time = time.time()
    operation_name = "SSH Query"

    try:
        log_tool(logging.INFO, f"{operation_name} started", subcategory='ssh')

        # Your code here
        result = execute_ssh_command()

        elapsed_seconds = time.time() - start_time
        log_tool(
            logging.INFO,
            f"{operation_name} completed in {elapsed_seconds:.2f}s",
            subcategory='ssh'
        )

        return result

    except Exception as e:
        elapsed_seconds = time.time() - start_time
        log_tool(
            logging.ERROR,
            f"{operation_name} failed after {elapsed_seconds:.2f}s: {str(e)}",
            subcategory='ssh'
        )
        raise
```

### Pattern 2: Loop Processing

```python
from tools.app_logger import log_background
import logging

def process_items(items):
    total = len(items)
    processed = 0
    errors = 0

    log_background(logging.INFO, f"Processing {total} items", subcategory='batch')

    for item in items:
        try:
            log_background(logging.DEBUG, f"Processing item {item['id']}", subcategory='batch')
            # Process item
            process_item(item)
            processed += 1

        except Exception as e:
            errors += 1
            log_background(
                logging.ERROR,
                f"Failed to process item {item['id']}: {str(e)}",
                subcategory='batch'
            )

    log_background(
        logging.INFO,
        f"Batch complete: {processed}/{total} processed, {errors} errors",
        subcategory='batch'
    )
```

### Pattern 3: Conditional Logging

```python
from tools.app_logger import log_background
import logging

def check_system_health():
    disk_usage = get_disk_usage()

    if disk_usage > 90:
        log_background(
            logging.ERROR,
            f"Disk usage critical: {disk_usage}%",
            subcategory='health'
        )
    elif disk_usage > 75:
        log_background(
            logging.WARNING,
            f"Disk usage high: {disk_usage}%",
            subcategory='health'
        )
    else:
        log_background(
            logging.INFO,
            f"Disk usage normal: {disk_usage}%",
            subcategory='health'
        )
```

---

## Troubleshooting Checklist

### Logs not appearing in files

- [ ] Check database\logs directory exists
- [ ] Verify write permissions on database\logs
- [ ] Check LOG_DIR value: `from tools.app_logger import LOG_DIR; print(LOG_DIR)`
- [ ] Verify no exceptions during logger setup
- [ ] Check console output (should show during development)

### Too much console output

- [ ] Verify frozen exe (not running as Python script)
- [ ] Check `sys.frozen` value: `import sys; print(getattr(sys, 'frozen', False))`

### Logs too large

- [ ] Check rotation is working: `ls -la database\logs\*.log*`
- [ ] Verify max_bytes and backup_count in setup_logger()
- [ ] Delete old backups manually: `del database\logs\*.log.* /S`

### Windows Service logs missing

- [ ] Verify database\logs exists and has SYSTEM permissions
- [ ] Check service is actually running: `sc query AutoTech`
- [ ] Check log directory: `icacls C:\AutoTech\database\logs`

### Performance degradation

- [ ] Check log level (should be INFO, not DEBUG)
- [ ] Monitor disk I/O usage
- [ ] Verify log directory on fast local drive (not network)

---

**End of Implementation Guide**
