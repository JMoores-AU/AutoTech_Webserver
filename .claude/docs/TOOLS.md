# Tools Directory Reference

This document provides an inventory of tool modules in the `tools/` directory. It is a technical reference only. Governance and constraints are defined in `CLAUDE.md`.

---

## 1. Core Infrastructure

### app_logger.py
- **Purpose:** Centralized logging infrastructure with rotating file handlers
- **Dependencies:** Python stdlib only (logging, os, datetime)
- **Offline Safe:** Yes
- **Features:** 6 log types (server, clients, tools, background, security, database), rotating files (5MB max), category/subcategory tagging

### equipment_db.py
- **Purpose:** SQLite database for caching equipment IP discovery results
- **Dependencies:** sqlite3, os, logging (stdlib)
- **Offline Safe:** Yes
- **Features:** Equipment cache with status tracking, lookup history, IP_list.dat imports

### ptx_uptime_db.py
- **Purpose:** SQLite database for PTX uptime history and reboot tracking
- **Dependencies:** sqlite3, os, logging, datetime, re (stdlib)
- **Offline Safe:** Yes
- **Features:** Uptime snapshots, historical trends, reboot records

### frontrunner_event_db.py
- **Purpose:** SQLite database for FrontRunner process failures and disk space warnings
- **Dependencies:** sqlite3, os, datetime (stdlib)
- **Offline Safe:** Yes
- **Features:** Event duration tracking, disk usage monitoring (>90% threshold)

---

## 2. Network/SSH Tools

### ip_finder.py
- **Purpose:** Equipment IP address lookup via gateway SSH
- **Dependencies:** paramiko (SSH), shlex, re
- **Offline Safe:** No (has offline_mode fallback with dummy data)
- **Features:** SSH tunneling to gateway, PTX model detection, AVI status, VNC tunnel setup

### ptx_uptime.py
- **Purpose:** Download and parse PTX uptime reports from MMS server
- **Dependencies:** paramiko, BeautifulSoup4, scp
- **Offline Safe:** No
- **Features:** SSH/SCP file download, HTML parsing, uptime statistics

### log_cleanup.py
- **Purpose:** Remote log cleanup utility for FrontRunner logs
- **Dependencies:** paramiko, datetime, json
- **Offline Safe:** No
- **Features:** SSH connections, folder age-based retention, dry-run mode

---

## 3. Monitoring Tools

### frontrunner_status.py
- **Purpose:** Check FrontRunner server status (uptime, CPU, memory, disk)
- **Dependencies:** paramiko, os, re, datetime
- **Offline Safe:** No (has offline_mode parameter)
- **Features:** SSH to server, process monitoring, resource metrics

### frontrunner_monitor.py
- **Purpose:** Background daemon for continuous FrontRunner monitoring
- **Dependencies:** paramiko, threading, json
- **Offline Safe:** No
- **Features:** 30-second interval, threaded operation, JSON cache

---

## 4. Diagnostic Tools

### additional_tools.py
- **Purpose:** Collection of remote equipment diagnostic utilities
- **Dependencies:** paramiko, subprocess, tempfile, webbrowser
- **Offline Safe:** No (all functions have offline_mode parameters)
- **Functions:** component_tracking, avi_mm2_reboot, speed_limit_data_check, koa_data_check, watchdog_deploy, log_downloader, tcp_avi_dump

### usb_tools.py
- **Purpose:** USB drive detection and tool launching
- **Dependencies:** ctypes (Windows), os, subprocess, pathlib
- **Offline Safe:** Yes (Windows-only)
- **Features:** Removable drive detection, drive label/free space queries

---

## 5. Offline Safety Summary

| Module | Offline Safe | Fallback Mode |
|--------|-------------|---------------|
| app_logger | Yes | N/A |
| equipment_db | Yes | N/A |
| ptx_uptime_db | Yes | N/A |
| frontrunner_event_db | Yes | N/A |
| usb_tools | Yes | N/A |
| ip_finder | No | offline_mode param |
| ptx_uptime | No | None |
| log_cleanup | No | dry_run mode |
| frontrunner_status | No | offline_mode param |
| frontrunner_monitor | No | JSON cache |
| additional_tools | No | offline_mode params |

---

## 6. Related Reference Documents

- `ARCHITECTURE.md`
- `DATABASES.md`
- `BACKGROUND_TASKS.md`
- `PATH_RESOLUTION.md`
