# Blueprints

## Overview

All 96 Flask routes are distributed across 17 Blueprint modules under `app/blueprints/`. `main.py` registers each blueprint at startup and contains no `@app.route` entries.

---

## Critical Rules

### Endpoint naming in url_for()

Always use fully-qualified `blueprint_name.function_name` syntax:

```python
# Correct
url_for('dashboard.dashboard')
url_for('dashboard.run_tool', tool_name='x')
url_for('auth.login')

# Wrong — raises BuildError at runtime
url_for('dashboard')
url_for('run_tool', tool_name='x')
```

### State access in blueprints

```python
# Correct — always dereferences the live module object
import app.state as state
state.background_updater['running']

# Wrong — captures a frozen reference at import time
from app.state import background_updater
```

---

## Blueprint Reference Table

| File | Blueprint name | Key routes | Notes |
|------|---------------|-----------|-------|
| `auth.py` | `auth` | `GET/POST /login`, `GET /logout` | Password: `komatsu`. Uses `flash()`. Redirects to `dashboard.dashboard`. |
| `info_pages.py` | `info_pages` | `/autotech`, `/legacy`, `/database`, `/t1-tools-help` | Static info pages. |
| `downloads.py` | `downloads` | `/download/camstudio`, `/download/frontrunner` | File downloads from `autotech_client/`. |
| `frontrunner.py` | `frontrunner` | `/api/frontrunner/*` | Frontrunner job status API. |
| `log_cleanup.py` | `log_cleanup` | `/api/cleanup-logs/*` | Log rotation trigger endpoints. |
| `admin_logs.py` | `admin_logs` | `/admin/logs`, `/api/logs/*` | Log viewer and log download. |
| `ptx_reboot.py` | `ptx_reboot` | `/api/ptx_reboot`, `/api/ptx_status` | PTX unit reboot and status check. |
| `vnc.py` | `vnc` | `/api/vnc/*`, `/api/tru_setup` | VNC session launch and TRU setup. |
| `usb_client.py` | `usb_client` | `/api/usb/*`, `/api/client/*`, `/usb_tool` | USB detection, client install, URI handler support. 12 routes. |
| `system_health.py` | `system_health` | `/api/mode`, `/api/health`, `/api/network_status`, `/api/system/status` | Runtime mode, network reachability, system status. |
| `fleet_monitor.py` | `fleet_monitor` | `/dig_fleet_monitor`, `/api/fleet_data/*` | Fleet dashboard and data API. |
| `tools_launch.py` | `tools_launch` | `/api/launch-legacy`, `/api/launch-batch-tool` | Launch external tool processes. |
| `ptx_uptime.py` | `ptx_uptime` | `/ptx-uptime-csv`, `/api/ptx/*` | PTX uptime records, CSV export. 10 routes. |
| `playback.py` | `playback` | `/api/playback/*`, `/download/playback/*` | Playback session management and file downloads. 15 routes. |
| `equipment.py` | `equipment` | `/api/equipment/*`, `/api/find-equipment-ip` | Equipment cache CRUD and IP resolution. 11 routes. |
| `legacy_terminal.py` | `legacy_terminal` | `/api/legacy/*` | `TerminalSession` class, GRM script execution. 8 routes. |
| `dashboard.py` | `dashboard` | `/`, `/api/equipment_profiles`, `/run/<tool_name>`, `/equipment_monitor`, `/api/flight_recorder_ip` | Main dashboard and tool launcher. 6 routes. |

---

## Registration in main.py

All 17 blueprints are statically imported and registered at startup:

```python
from app.blueprints.auth import bp as auth_bp
from app.blueprints.dashboard import bp as dashboard_bp
# ... (all 17)
app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
# ...
```

Because all imports are static, PyInstaller auto-traces them — no `hiddenimports` entries are required for blueprint files.

---

## Finding a Route

1. Identify the functional area from the table above.
2. Open the corresponding file under `app/blueprints/`.
3. Use the fully-qualified endpoint name in `url_for()` calls and test fixtures.

---

## Related Reference Documents

- `ARCHITECTURE.md` — overall structure and layer responsibilities
- `TEMPLATES.md` — template conventions and `url_for()` usage in Jinja2
- `BUILD_AND_DEPLOY.md` — PyInstaller and hidden imports
- `PITFALLS.md` — frozen executable traps affecting blueprints
