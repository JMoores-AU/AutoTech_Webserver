# CLAUDE.md

This file defines **governance, constraints, and agent routing rules** for Claude Code when working in this repository. Detailed technical knowledge is stored in `.claude/docs/` and must be loaded only when relevant.

---

## Project Overview

AutoTech Web Dashboard is a Windows-based Flask application for remote access and diagnostics of Komatsu mining equipment. It runs in development mode, as a standalone executable built with PyInstaller, and as a Windows service. Production deployments are offline and air-gapped.

---

## Non-Negotiable Constraints

- Production environment is **offline**
- Final deliverable is a **standalone Windows executable**
- Built with **PyInstaller**
- Windows-only
- No internet access at runtime
- No dynamic downloads or external services
- All paths must tolerate frozen, service, and USB execution

---

## Build Entry Points

```batch
python main.py
pyinstaller AutoTech.spec --noconfirm
BUILD_WEBSERVER.bat
```

---

## Documentation Routing

Load docs from `.claude/docs/` only when relevant. Full index: `.claude/docs/README.md`

| Task Type | Load |
|-----------|------|
| Architecture/design | `ARCHITECTURE.md` |
| Runtime modes (dev/frozen/service) | `RUNTIME_MODES.md` |
| Background tasks/threads | `BACKGROUND_TASKS.md` |
| Path resolution issues | `PATH_RESOLUTION.md` |
| Database schemas | `DATABASES.md` |
| Build/PyInstaller | `BUILD_AND_DEPLOY.md` |
| USB deployment | `USB_DEPLOYMENT.md` |
| Client/URI handlers | `CLIENT_ARCHITECTURE.md` |
| Templates/UI | `TEMPLATES.md` |
| Logging | `LOGGING.md` |
| Tool modules | `TOOLS.md` |
| Known pitfalls | `PITFALLS.md` |

---

## Agent Routing

Use specialized agents for domain-specific tasks:

| Task Domain | Agent | Trigger Keywords |
|-------------|-------|------------------|
| Git operations, versioning, changelog | `git-workflow-specialist` | git push, git pull, commit, changelog, release, version bump, tag |
| USB detection, client install, URI handlers | `usb-client-specialist` | USB not detected, client install, launch_*.bat, URI handler, autotech-ssh/sftp/vnc |
| PyInstaller, .spec, BUILD_WEBSERVER.bat | `pyinstaller-build-specialist` | Build fails, frozen mode, hidden imports, service install |
| Logging infrastructure | `flask-logging-architect` | Add logging, track events, debug visibility |
| Test protocols, offline validation | `offline-test-authority` | Release gate, offline test, air-gapped validation |
| Documentation maintenance | `docs-curator` | Update docs, CLAUDE.md, .claude/docs/ |
