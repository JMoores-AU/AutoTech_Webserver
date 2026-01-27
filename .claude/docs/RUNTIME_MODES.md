# Runtime Modes

This document describes how AutoTech behaves under its supported runtime modes and the implications each mode has on paths, logging, background tasks, and deployment. This is a reference document only. Governance and constraints are defined in `CLAUDE.md`.

---

## 1. Overview

AutoTech supports three runtime modes from a single codebase:

1. Development mode (source execution)
2. Standalone executable mode (PyInstaller)
3. Windows Service mode (headless, persistent)

Each mode affects filesystem paths, logging visibility, lifecycle behavior, and debugging techniques.

---

## 2. Development Mode

### Execution
```batch
python main.py
