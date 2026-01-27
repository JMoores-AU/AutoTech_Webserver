# USB Deployment

This document describes how AutoTech is deployed via USB media, including detection logic, directory layout, and operational expectations. This is a reference document only. Governance and release controls are defined in `CLAUDE.md`.

---

## 1. Overview

AutoTech supports deployment via removable USB media. This deployment method is used to distribute the standalone executable, client installer, databases, and supporting scripts to isolated or offline environments.

USB deployment is automated as part of the build pipeline and is designed to require minimal manual intervention.

---

## 2. Deployment Trigger

USB deployment is initiated by the build pipeline:

```batch
BUILD_WEBSERVER.bat
