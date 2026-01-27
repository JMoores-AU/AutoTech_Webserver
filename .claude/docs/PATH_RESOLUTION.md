
---

## `/docs/PATH_RESOLUTION.md`

```md
# Path Resolution

This document describes how filesystem paths are resolved in AutoTech across development, frozen executable, Windows service, and USB deployment modes. Correct path handling is critical for reliability in offline environments.

---

## 1. Overview

AutoTech must function correctly across multiple execution contexts. Hardcoded relative paths are not reliable and must be avoided.

All filesystem access must be based on a resolved runtime base directory.

---

## 2. Base Directory Resolution

Runtime mode is detected using the `sys.frozen` attribute:

```python
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(__file__)
