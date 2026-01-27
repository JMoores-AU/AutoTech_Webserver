# Databases

This document describes the database architecture used by AutoTech, including schema ownership, initialization behavior, and migration expectations. This is a technical reference only. Governance and release controls are defined in `CLAUDE.md`.

---

## 1. Overview

AutoTech uses multiple **independent SQLite databases**, each with a single responsibility. Databases are accessed locally, require no external services, and are compatible with offline execution in development, frozen executable, and Windows service modes.

Each database:
- Has its own Python module
- Owns its schema and migrations
- Initializes automatically at application startup
- Is stored on the local filesystem relative to runtime paths

---

## 2. Equipment Database

### Purpose
- Cache of equipment metadata
- Provides fast lookup by IP, name, or type
- Reduces repeated SSH discovery

### Files
- Database file: `database/equipment.db`
- Module: `tools/equipment_db.py`

### Characteristics
- Auto-initializes if database file does not exist
- Tracks schema version internally
- Automatically imports from `IP_list.dat` when empty
- Supports search, insert, update, and bulk import

### Notes
- Auto-import behavior is intentional but can be disabled in code
- Schema changes require version increment and migration logic

---

## 3. PTX Uptime Database

### Purpose
- Persistent history of PTX controller uptime
- Records online/offline transitions over time
- Supports uptime reporting and diagnostics

### Files
- Database file: `database/ptx_uptime.db`
- Module: `tools/ptx_uptime_db.py`

### Characteristics
- Stores timestamped status changes
- Designed for append-heavy workloads
- Queried by reporting routes for historical views

### Notes
- Schema is defined within the PTXUptimeDB class
- Schema changes must preserve historical data

---

## 4. FrontRunner Events Database

### Purpose
- Records FrontRunner service failures and health events
- Supports post-incident diagnostics and trend analysis

### Files
- Database file: `database/frontrunner_events.db`
- Module: `tools/frontrunner_event_db.py`

### Characteristics
- Event-driven writes
- Stores severity, timestamp, and message
- Used by background monitoring logic

---

## 5. Initialization and Migration

### Initialization
- Databases are created automatically if missing
- Initialization occurs during application startup
- Tables are created if they do not exist

### Migration Strategy
- Each database module defines a schema version constant
- On startup:
  - Current schema version is read
  - Migration logic runs if versions differ
- Migrations must be backward-compatible

### Required Migration Steps
1. Increment schema version
2. Add migration logic
3. Test against:
   - empty database
   - populated database

---

## 6. Path Resolution

Database paths must resolve correctly in:
- development mode
- frozen executable mode
- USB deployment
- Windows service execution

Relative paths (e.g. `./database`) must not be used directly. All paths should be constructed from a resolved base directory.

See `PATH_RESOLUTION.md` for details.

---

## 7. Concurrency and Safety

- SQLite access must be serialized where required
- Long-running transactions should be avoided
- Database access must not block Flask request handling
- Background tasks must handle database errors gracefully

---

## 8. Testing Expectations

- Database initialization must be tested with no existing files
- Migration logic must be tested against existing data
- Queries must be validated for correctness and performance
- Frozen executable behavior must be verified

---

## 9. Related Reference Documents

- `ARCHITECTURE.md`
- `BACKGROUND_TASKS.md`
- `PATH_RESOLUTION.md`
- `BUILD_AND_DEPLOY.md`
