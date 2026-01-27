# Logging

This document describes logging expectations, structure, and operational considerations for AutoTech. It is a technical reference only. Governance and enforcement rules are defined in `CLAUDE.md`.

---

## 1. Overview

Logging in AutoTech exists to provide:
- operational visibility
- failure diagnosis
- background task observability
- auditability in offline environments

Because AutoTech may run as a Windows service or from USB, **file-based logging is mandatory**. Console-only logging is insufficient.

---

## 2. Logging Scope

Logging should cover:
- Flask request/response lifecycle
- Authentication events
- Client registration and verification
- Tool execution (SSH, SFTP, file operations)
- Background task startup, progress, and failure
- Service startup and shutdown
- Critical errors and exceptions

Silent failures are considered defects.

---

## 3. Logging Characteristics

Logging implementations must:
- use Python standard logging facilities
- avoid external logging dependencies
- support rotation to prevent disk exhaustion
- write logs relative to runtime-resolved paths
- function in development, frozen executable, service, and USB modes

---

## 4. File-Based Logging

Logs must:
- be written to persistent storage
- not rely on current working directory
- tolerate execution from USB or service context
- be readable post-failure

Log directories should be created if missing and must be writable in all runtime modes.

---

## 5. Log Levels

Standard log levels should be used consistently:

- DEBUG — verbose internal state
- INFO — normal operations
- WARNING — recoverable issues
- ERROR — failed operations
- CRITICAL — unrecoverable failures

Avoid logging sensitive data such as passwords or full SSH output.

---

## 6. Background Task Logging

Background tasks must:
- log startup and shutdown
- log recoverable errors
- log repeated failures with throttling where appropriate
- avoid tight log loops on failure

Background logging is critical when running as a Windows service.

---

## 7. Testing Expectations

Logging must be validated in:
- development execution
- frozen executable execution
- Windows service execution
- USB execution

Test cases should confirm:
- log files are created
- rotation works
- failures are logged
- logs persist across restarts

---

## 8. Detailed Implementation Documentation

For implementation, refer to the detailed logging design documents in this folder:

- `LOGGING_INDEX.md` — Navigation guide to all logging documentation
- `LOGGING_QUICK_REFERENCE.md` — Cheat sheet for common patterns
- `LOGGING_DESIGN_SUMMARY.md` — Executive summary and timeline
- `LOGGING_IMPLEMENTATION_GUIDE.md` — Copy-paste code snippets and tasks
- `LOGGING_ARCHITECTURE.md` — Complete architectural design (25+ pages)

**Status:** Design phase complete, not yet implemented.

---

## 9. Related Reference Documents

- `ARCHITECTURE.md`
- `BACKGROUND_TASKS.md`
- `RUNTIME_MODES.md`
