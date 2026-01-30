# tools/app_logger.py
"""
AutoTech Centralized Logging Infrastructure
============================================
Provides rotating log files for all application components:
- server.log: Flask requests, responses, startup, shutdown
- clients.log: Client registrations, verifications
- tools.log: SSH/SFTP operations, IP finder, PTX queries
- background.log: Equipment updater, PTX checker, FrontRunner monitor
- security.log: Login attempts, session events, unauthorized access
- database.log: Queries, slow queries, errors

Log Format: [TIMESTAMP] [LEVEL] [CATEGORY] [SUBCATEGORY] [REQUEST_ID] message

Request Correlation:
- Every HTTP request gets a unique request_id (8-char hex)
- request_id is automatically included in all log entries
- Background tasks use task-specific IDs (e.g., 'bg-ptx-checker')
"""
import os
import sys
import logging
import uuid
from contextvars import ContextVar
from logging.handlers import RotatingFileHandler
from datetime import datetime
from typing import Optional

# Thread-safe context variable for request_id correlation
_request_id_ctx: ContextVar[str] = ContextVar('request_id', default='no-request')

# Configuration
MAX_LOG_SIZE = 5 * 1024 * 1024  # 5MB per log file
BACKUP_COUNT = 5  # Keep 5 backup files (.log.1, .log.2, etc.)
LOG_FOLDER_NAME = "logs"
DEFAULT_LOG_LEVEL = logging.INFO

# Log file names
LOG_FILES = {
    'server': 'server.log',
    'clients': 'clients.log',
    'tools': 'tools.log',
    'background': 'background.log',
    'security': 'security.log',
    'database': 'database.log',
}

# Store initialized loggers
_loggers = {}
_log_dir = None
_initialized = False


def get_log_directory() -> str:
    """
    Get the log directory path, creating it if necessary.
    Supports dev, frozen exe, service, and USB deployment modes.

    Directory structure:
    - USB: E:\\AutoTech\\database\\logs
    - Dev: project\\database\\logs
    """
    global _log_dir

    if _log_dir and os.path.exists(_log_dir):
        return _log_dir

    # Determine base directory based on execution context
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller executable
        base_dir = os.path.dirname(sys.executable)
    else:
        # Running as Python script
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Try USB structure first (E:\AutoTech\database\logs)
    usb_db_folder = os.path.join(base_dir, "AutoTech", "database")
    if os.path.exists(os.path.join(base_dir, "AutoTech")):
        _log_dir = os.path.join(usb_db_folder, LOG_FOLDER_NAME)
    else:
        # Fallback to dev structure (project\database\logs)
        _log_dir = os.path.join(base_dir, "database", LOG_FOLDER_NAME)

    os.makedirs(_log_dir, exist_ok=True)
    return _log_dir


def get_log_level() -> int:
    """
    Get log level from environment variable or use default.
    Set AUTOTECH_LOG_LEVEL=DEBUG for verbose logging.
    """
    level_name = os.environ.get('AUTOTECH_LOG_LEVEL', 'INFO').upper()
    level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL,
    }
    return level_map.get(level_name, DEFAULT_LOG_LEVEL)


# === Request ID Functions ===

def generate_request_id() -> str:
    """Generate a unique request ID (8-char hex for brevity)."""
    return uuid.uuid4().hex[:8]


def set_request_id(request_id: str) -> None:
    """Set the request ID for the current context (call from Flask before_request)."""
    _request_id_ctx.set(request_id)


def get_request_id() -> str:
    """Get the current request ID (safe to call from any thread/context)."""
    return _request_id_ctx.get()


def _create_formatter() -> logging.Formatter:
    """Create consistent log formatter with request_id support."""
    return logging.Formatter(
        '[%(asctime)s.%(msecs)03d] [%(levelname)s] [%(category)s] [%(subcategory)s] [%(request_id)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def _get_logger(name: str, log_file: str) -> logging.Logger:
    """
    Get or create a logger with rotating file handler.

    Args:
        name: Logger name (e.g., 'autotech.server')
        log_file: Log file name (e.g., 'server.log')

    Returns:
        Configured logger instance
    """
    global _loggers

    if name in _loggers:
        return _loggers[name]

    logger = logging.getLogger(name)
    logger.setLevel(get_log_level())
    logger.propagate = False  # Don't propagate to root logger

    # Create log directory if needed
    log_dir = get_log_directory()
    log_path = os.path.join(log_dir, log_file)

    # Add rotating file handler
    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=MAX_LOG_SIZE,
        backupCount=BACKUP_COUNT,
        encoding='utf-8'
    )
    file_handler.setLevel(get_log_level())
    file_handler.setFormatter(_create_formatter())
    logger.addHandler(file_handler)

    # Add console handler for development (not in frozen exe or service)
    # Check if running in service mode by looking for specific markers
    is_service = os.environ.get('AUTOTECH_SERVICE_MODE', '').strip() == '1'
    is_frozen = getattr(sys, 'frozen', False)

    if not is_service:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(get_log_level())
        console_handler.setFormatter(_create_formatter())
        logger.addHandler(console_handler)

    _loggers[name] = logger
    return logger


class CategoryLogAdapter(logging.LoggerAdapter):
    """
    Log adapter that adds category and subcategory to log records.
    """
    def process(self, msg, kwargs):
        # Add category and subcategory to the record
        extra = kwargs.get('extra', {})
        extra['category'] = self.extra.get('category', 'unknown')
        extra['subcategory'] = self.extra.get('subcategory', 'general')
        if 'request_id' not in extra:
            extra['request_id'] = get_request_id()
        kwargs['extra'] = extra
        return msg, kwargs


def _get_category_logger(category: str, log_file: str) -> CategoryLogAdapter:
    """
    Get a logger adapter for a specific category.
    """
    logger = _get_logger(f'autotech.{category}', log_file)
    return CategoryLogAdapter(logger, {'category': category, 'subcategory': 'general'})


# === Public Logging Functions ===

def log_server(level: str, subcategory: str, message: str, request_id: Optional[str] = None) -> None:
    """
    Log server events (requests, responses, startup, shutdown).

    Args:
        level: Log level ('debug', 'info', 'warning', 'error', 'critical')
        subcategory: Event subcategory ('request', 'response', 'startup', 'shutdown')
        message: Log message
        request_id: Optional explicit request_id (uses context if not provided)

    Examples:
        log_server('info', 'request', 'GET /api/equipment_search - 10.110.19.100')
        log_server('info', 'startup', 'Server started on port 8888')
    """
    logger = _get_logger('autotech.server', LOG_FILES['server'])
    log_func = getattr(logger, level.lower(), logger.info)
    log_func(message, extra={
        'category': 'server',
        'subcategory': subcategory,
        'request_id': request_id or get_request_id()
    })


def log_client(level: str, subcategory: str, message: str, request_id: Optional[str] = None) -> None:
    """
    Log client events (registrations, verifications).

    Args:
        level: Log level
        subcategory: Event subcategory ('registration', 'verification', 'connection')
        message: Log message
        request_id: Optional explicit request_id (uses context if not provided)

    Examples:
        log_client('info', 'registration', 'Client registered: IP=10.110.19.100, Version=v1.1.1')
    """
    logger = _get_logger('autotech.clients', LOG_FILES['clients'])
    log_func = getattr(logger, level.lower(), logger.info)
    log_func(message, extra={
        'category': 'clients',
        'subcategory': subcategory,
        'request_id': request_id or get_request_id()
    })


def log_tool(level: str, subcategory: str, message: str, request_id: Optional[str] = None) -> None:
    """
    Log tool operations (SSH, SFTP, IP finder, PTX queries).

    Args:
        level: Log level
        subcategory: Tool subcategory ('ssh', 'sftp', 'ip_finder', 'ptx', 'frontrunner')
        message: Log message
        request_id: Optional explicit request_id (uses context if not provided)

    Examples:
        log_tool('info', 'ssh', 'SSH connected to 10.110.19.16')
        log_tool('error', 'ssh', 'SSH connection failed: Authentication error')
    """
    logger = _get_logger('autotech.tools', LOG_FILES['tools'])
    log_func = getattr(logger, level.lower(), logger.info)
    log_func(message, extra={
        'category': 'tools',
        'subcategory': subcategory,
        'request_id': request_id or get_request_id()
    })


def log_background(level: str, subcategory: str, message: str, request_id: Optional[str] = None) -> None:
    """
    Log background task events (equipment updater, PTX checker, monitors).

    Args:
        level: Log level
        subcategory: Task subcategory ('ptx_checker', 'equipment_updater', 'playback_monitor', 'frontrunner_monitor')
        message: Log message
        request_id: Optional explicit request_id (uses context if not provided)

    Examples:
        log_background('info', 'ptx_checker', 'Cycle complete: 45 checked, 42 online, 3 offline')
    """
    logger = _get_logger('autotech.background', LOG_FILES['background'])
    log_func = getattr(logger, level.lower(), logger.info)
    log_func(message, extra={
        'category': 'background',
        'subcategory': subcategory,
        'request_id': request_id or get_request_id()
    })


def log_security(level: str, subcategory: str, message: str, request_id: Optional[str] = None) -> None:
    """
    Log security events (login attempts, session events, unauthorized access).

    Args:
        level: Log level
        subcategory: Event subcategory ('login', 'logout', 'session', 'unauthorized')
        message: Log message
        request_id: Optional explicit request_id (uses context if not provided)

    Examples:
        log_security('info', 'login', 'Successful login from 10.110.19.100')
        log_security('warning', 'login', 'Failed login attempt from 10.110.19.100')
    """
    logger = _get_logger('autotech.security', LOG_FILES['security'])
    log_func = getattr(logger, level.lower(), logger.info)
    log_func(message, extra={
        'category': 'security',
        'subcategory': subcategory,
        'request_id': request_id or get_request_id()
    })


def log_database(level: str, subcategory: str, message: str, request_id: Optional[str] = None) -> None:
    """
    Log database events (queries, slow queries, errors).

    Args:
        level: Log level
        subcategory: Event subcategory ('query', 'slow_query', 'error', 'migration')
        message: Log message
        request_id: Optional explicit request_id (uses context if not provided)

    Examples:
        log_database('info', 'query', 'Equipment search: 45 results in 12ms')
        log_database('warning', 'slow_query', 'Query took 5.2s: SELECT * FROM large_table')
    """
    logger = _get_logger('autotech.database', LOG_FILES['database'])
    log_func = getattr(logger, level.lower(), logger.info)
    log_func(message, extra={
        'category': 'database',
        'subcategory': subcategory,
        'request_id': request_id or get_request_id()
    })


# === Utility Functions ===

def format_request_log(method: str, path: str, client_ip: str,
                       duration_ms: Optional[float] = None,
                       status_code: Optional[int] = None) -> str:
    """
    Format a request/response log message.

    Args:
        method: HTTP method (GET, POST, etc.)
        path: Request path
        client_ip: Client IP address
        duration_ms: Request duration in milliseconds (optional)
        status_code: Response status code (optional)

    Returns:
        Formatted log message
    """
    parts = [f"{method} {path}", f"IP={client_ip}"]

    if status_code is not None:
        parts.append(f"status={status_code}")

    if duration_ms is not None:
        parts.append(f"{duration_ms:.1f}ms")

    return " - ".join(parts)


def format_client_registration(client_ip: str, version: str,
                                user_agent: Optional[str] = None,
                                test_success: bool = True) -> str:
    """
    Format a client registration log message.

    Args:
        client_ip: Client IP address
        version: Client version
        user_agent: User agent string (optional)
        test_success: Whether the registration test succeeded

    Returns:
        Formatted log message
    """
    msg = f"Client registered: IP={client_ip}, Version={version}"
    if user_agent:
        msg += f", UserAgent={user_agent[:50]}"
    msg += f", TestSuccess={test_success}"
    return msg


def get_log_stats() -> dict:
    """
    Get statistics about current log files.

    Returns:
        Dictionary with log file sizes and paths
    """
    log_dir = get_log_directory()
    stats = {
        'log_directory': log_dir,
        'files': {}
    }

    for category, filename in LOG_FILES.items():
        filepath = os.path.join(log_dir, filename)
        if os.path.exists(filepath):
            size_bytes = os.path.getsize(filepath)
            stats['files'][category] = {
                'path': filepath,
                'size_bytes': size_bytes,
                'size_kb': round(size_bytes / 1024, 2),
                'size_mb': round(size_bytes / (1024 * 1024), 4),
            }
        else:
            stats['files'][category] = {
                'path': filepath,
                'size_bytes': 0,
                'size_kb': 0,
                'size_mb': 0,
            }

    return stats


def init_logging() -> str:
    """
    Initialize logging infrastructure (call at startup).
    Creates log directory and initializes all loggers.

    Returns:
        Path to log directory
    """
    global _initialized

    log_dir = get_log_directory()

    # Pre-initialize all loggers to create empty log files
    for category, filename in LOG_FILES.items():
        _get_logger(f'autotech.{category}', filename)

    _initialized = True

    # Log initialization to server log
    log_server('info', 'startup', f'Logging initialized. Log directory: {log_dir}')

    return log_dir


# Test function
if __name__ == "__main__":
    print("AutoTech Logging Infrastructure Test")
    print("=" * 50)

    # Initialize logging
    log_dir = init_logging()
    print(f"Log directory: {log_dir}")

    # Test each log type
    log_server('info', 'startup', 'Test server startup message')
    log_server('info', 'request', format_request_log('GET', '/api/test', '127.0.0.1', 45.2, 200))

    log_client('info', 'registration', format_client_registration('10.110.19.100', 'v1.1.1', 'Mozilla/5.0', True))

    log_tool('info', 'ssh', 'SSH connected to 10.110.19.16')
    log_tool('error', 'ssh', 'SSH connection failed: Authentication error')

    log_background('info', 'ptx_checker', 'PTX Uptime Checker started')
    log_background('info', 'ptx_checker', 'Cycle complete: Online=42, Offline=3, Errors=0')

    log_security('info', 'login', 'Successful login from 127.0.0.1')
    log_security('warning', 'login', 'Failed login attempt from 192.168.1.100')

    log_database('info', 'query', 'Equipment search completed: 45 results in 12ms')
    log_database('warning', 'slow_query', 'Slow query detected: 5200ms')

    # Print stats
    print("\nLog Statistics:")
    stats = get_log_stats()
    for category, info in stats['files'].items():
        print(f"  {category}: {info['size_kb']:.2f} KB")

    print("\nTest complete. Check log files in:", log_dir)
