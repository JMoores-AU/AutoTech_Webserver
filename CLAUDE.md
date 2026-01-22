# T1 Tools Web - AutoTech Dashboard

## Project Overview
Flask web app for Komatsu mining equipment remote access/diagnostics. Runs as standalone exe (PyInstaller) or dev server.

## Tech Stack
- **Backend**: Flask + Paramiko (SSH) + ping3
- **Frontend**: Jinja2 templates, vanilla JS, CSS
- **Build**: PyInstaller (`AutoTech.spec`)
- **DB**: SQLite (equipment_db.py, ptx_uptime_db.py)

## Key Paths
- `main.py` - Flask app entry point, all routes
- `tools/` - Tool modules (ptx_uptime.py, ip_finder.py, etc.)
- `templates/` - Jinja2 HTML templates
- `static/` - CSS/JS assets
- `autotech_client/` - Client installer + batch scripts
- `database/` - SQLite DBs

## Architecture
- Routes in main.py call tool functions from `tools/*.py`
- Templates extend `_BASE_TEMPLATE.html` or `layout.html`
- SSH via Paramiko to Linux servers (serverList.py has IPs)
- Equipment data cached in SQLite

## Common Tools
| Tool | Route | Purpose |
|------|-------|---------|
| PTX Uptime | /ptx-uptime | Check PTX controller uptimes |
| IP Finder | /ip-finder | Search equipment by IP/ID |
| T1 Legacy | /t1-legacy | Launch batch scripts in CMD |
| Playback | /playback-tools | USB playback file tools |

## Build Commands
```batch
pyinstaller AutoTech.spec
# or
BUILD_WEBSERVER.bat
```

## Server Credentials
Stored in `main.py` as MMS_PASSWORD constant. SSH user: `mms`

## Conventions
- Tool routes: `/tool-name` (kebab-case)
- API endpoints: `/api/tool-name/action`
- Templates: `tool_name.html` (snake_case)
