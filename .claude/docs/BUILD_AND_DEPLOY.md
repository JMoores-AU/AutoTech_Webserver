# Build and Deployment

This document describes how AutoTech is built, packaged, and deployed across development, executable, service, and USB-based environments. This is a procedural reference only.

---

## 1. Overview

AutoTech is built from source into a standalone Windows executable using PyInstaller. The same executable is used for:
- interactive execution
- Windows service installation
- USB-based deployment

Build and deployment steps are automated via batch scripts.

---

## 2. Development Execution

```batch
python main.py
