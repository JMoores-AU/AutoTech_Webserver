# AutoTech Architecture Overview

This document describes the high-level and internal architecture of the AutoTech Web Dashboard. It is intended as a reference for understanding system structure, runtime behavior, and component responsibilities. Governance, constraints, and agent routing rules are defined in `CLAUDE.md`.

---

## 1. Core Application Structure

AutoTech is implemented as a **single-file Flask application** (`main.py`, ~4000 lines) supported by a collection of helper modules in the `tools/` directory.

The application intentionally avoids Flask blueprints. All routes are defined directly in `main.py` using `@app.route()` decorators. This simplifies PyInstaller bundling and runtime path resolution at the cost of file size.

### Responsibilities handled directly in `main.py`

- Flask app initialization and configuration
- All HTTP route handlers (70+ routes)
- Session-based authentication
- SSH connection orchestration via Paramiko
- Background task lifecycle management
- PTX uptime polling and state management
- Equipment database update scheduling
- FrontRunner monitoring integration
- Playback file operations and progress tracking
- Runtime mode detection (dev vs frozen vs service)

---

## 2. Hybrid Deployment Model

AutoTech supports three runtime modes from the same codebase:

### Development Mode
- Executed via `python main.py`
- Uses source files directly
- Console logging enabled
- Used for local development and debugging

### Standalone Executable Mode
- Executed as `AutoTech.exe`
- Built using PyInstaller
- Python interpreter bundled
- Files extracted to a temporary runtime directory (`sys._MEIPASS`)
- Paths resolved relative to the executable

### Windows Service Mode
- `AutoTech.exe` installed as a Windows service
- Runs without user login
- Background tasks run continuously
- Console output captured by the service manager

Runtime mode is detected using:

```python
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
    meipass = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(__file__)
