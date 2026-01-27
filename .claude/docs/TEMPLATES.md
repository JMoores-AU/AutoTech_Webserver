# Templates

This document describes the HTML template architecture used by AutoTech, including base templates, extension rules, and conventions for adding new UI pages. This is a technical reference only. Governance and agent rules are defined in `CLAUDE.md`.

---

## 1. Overview

AutoTech uses **Jinja2 templates** rendered by Flask to generate the web UI. Templates are organised around two base layouts: a modern primary layout and a legacy layout. All page templates extend one of these bases.

Templates are bundled into the standalone executable by PyInstaller and extracted at runtime. Template paths must remain compatible with frozen execution.

---

## 2. Template Directory Structure

Templates are stored under:

