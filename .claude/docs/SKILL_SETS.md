# Skill Sets

This document describes the major skill domains involved in developing, maintaining, and extending AutoTech. It is intended to guide agent selection, task routing, and mental context when working on the codebase.

---

## 1. Offline Test Authority

Primary responsibilities:
- Test gating
- Offline compliance validation
- Release readiness assessment
- Risk classification
- Refusal of unsafe or incomplete changes

Used when changes affect runtime behavior, deployment, data, or production constraints.

---

## 2. Flask Logging Architecture

Primary responsibilities:
- Structured logging design
- Rotating file handlers
- Windows service logging
- PyInstaller-safe logging paths
- Background task observability

Used when visibility or diagnostics are required.

---

## 3. Core Application Development

Primary responsibilities:
- Flask route implementation
- Background thread management
- SQLite database interactions
- Paramiko SSH usage
- Playback file logic

Used for feature development and bug fixes.

---

## 4. Background Systems Engineering

Primary responsibilities:
- Long-running thread stability
- Failure handling and recovery
- Resource management
- Graceful shutdown logic

Used when modifying background tasks or schedulers.

---

## 5. Build and Deployment Engineering

Primary responsibilities:
- PyInstaller configuration
- Executable validation
- Windows service installation
- USB deployment pipeline
- Versioning

Used when modifying build scripts or deployment behavior.

---

## 6. Client Integration

Primary responsibilities:
- Custom URI handlers
- Client verification flows
- Local tool invocation
- Browser-to-client handoff

Used when modifying client-server interaction.

---

## 7. UI and Template Development

Primary responsibilities:
- Jinja templates
- Base template selection
- Navigation consistency
- Frontend behavior tied to routes

Used when modifying templates or dashboard UX.

---

## 8. Diagnostic and Maintenance Work

Primary responsibilities:
- Log analysis
- Incident reconstruction
- Regression identification
- Operational support

Used when troubleshooting production issues.

---

## 9. Related Reference Documents

- `ARCHITECTURE.md`
- `LOGGING.md`
- `BUILD_AND_DEPLOY.md`
