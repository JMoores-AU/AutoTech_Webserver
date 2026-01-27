
---

## `/docs/BACKGROUND_TASKS.md`

```md
# Background Tasks

This document describes the architecture, responsibilities, and lifecycle of background tasks in AutoTech. It is intended as a technical reference for maintaining and extending background processing logic.

---

## 1. Overview

AutoTech runs multiple long-lived background threads alongside the Flask web server. These tasks perform continuous monitoring and periodic updates independent of user interaction.

All background tasks:
- Run as daemon threads
- Are started during application startup
- Must support graceful shutdown
- Must tolerate intermittent failures

---

## 2. Equipment Updater

### Purpose
- Sequentially queries equipment via SSH
- Collects and caches metadata
- Keeps the equipment database current

### Architecture
- Implemented in `main.py`
- Controlled via a shared state dictionary

### State Dictionary Fields
- `running`: boolean
- `thread`: Thread object
- `stop_event`: threading.Event
- `current_equipment`: equipment identifier
- `processed_count`: integer counter

### Behavior
- Iterates equipment one at a time
- Sleeps between SSH calls (default: 5 seconds)
- Updates database incrementally
- Designed to avoid overwhelming network or devices

---

## 3. PTX Uptime Checker

### Purpose
- Periodically checks PTX controller availability
- Records online/offline transitions
- Builds historical uptime records

### Architecture
- Implemented in `main.py` as `ptx_uptime_checker_worker`
- Uses SSH or ping-based checks
- Writes results to PTX uptime database

### State Dictionary Fields
- `running`, `stopped`, `waiting`, `error`: status flags
- `total_equipment`, `checked_count`, `online_count`, `offline_count`, `error_count`: metrics
- `last_cycle_start`, `last_cycle_end`, `next_cycle`: timing

### Behavior
- Polls at 30-minute intervals
- Stores timestamps for state changes
- Designed to run continuously with low overhead
- Endpoints: `/api/ptx/uptime-checker/start|stop|status`

---

## 4. Playback File Monitor

### Purpose
- Real-time monitoring of playback server files
- Detects new .log (pending) and .dat (recent) files
- Provides live file discovery for downloads

### Architecture
- Implemented in `main.py` as `playback_monitor_worker`
- Maintains persistent SSH/SFTP connections
- 10-second scan interval

### State Dictionary Fields
- `connected`, `connecting`, `monitoring`, `error`: status flags

### Behavior
- Scans playback server directories via SFTP
- Maintains connection resilience
- Endpoints: `/api/playback/monitor/start|stop|status`

---

## 5. FrontRunner Monitor

### Purpose
- Monitors FrontRunner server health
- Detects service failures and resource issues
- Records significant events for diagnostics

### Architecture
- Implemented in `tools/frontrunner_monitor.py`
- Maintains persistent SSH connection
- Writes status cache to JSON
- Logs events to database

### Behavior
- Polls health metrics every 30 seconds
- Detects and logs abnormal conditions
- Designed to survive SSH interruptions

---

## 6. Thread Lifecycle Management

### Startup
- Threads are created during application initialization
- Threads are marked as daemon threads
- Threads begin execution immediately after creation

### Shutdown
- `stop_event` must be set on application exit
- Threads must check `stop_event` regularly
- SSH connections must be closed cleanly

Failure to respect shutdown rules can cause:
- resource leaks
- hung services
- corrupted state

---

## 7. Failure Handling Expectations

Background tasks must:
- Catch and log exceptions
- Continue operation after recoverable failures
- Avoid crashing the main Flask process
- Surface failures via logging or status endpoints

Silent failures are considered defects.

---

## 8. Concurrency Considerations

- Shared state must be protected with locks where required
- Long blocking operations should not hold locks
- Background tasks must not block Flask request handling

---

## 9. Testing Guidance

- Tasks should be testable in isolation
- Failure scenarios must be simulated
- Long-running behavior should be soak-tested where possible
- Frozen executable behavior must be validated

---

## 10. Related Reference Documents

- `ARCHITECTURE.md`
- `DATABASES.md`
- `LOGGING.md`
- `RUNTIME_MODES.md`
