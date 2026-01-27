# AutoTech Reference Documentation

This directory contains **load-on-demand reference documentation** for the AutoTech Web Dashboard. These files are intended to be consulted only when relevant to a task. Governance, agent routing, and non-negotiable constraints are defined in `CLAUDE.md`.

Claude Code should not read all documents by default. Only the files relevant to the current task should be loaded.

---

## Core System References

- `ARCHITECTURE.md`  
  High-level system structure, components, and design constraints.

- `RUNTIME_MODES.md`  
  Development, standalone executable, and Windows service behavior.

- `BACKGROUND_TASKS.md`  
  Long-running background threads, lifecycle, and failure handling.

- `DATABASES.md`  
  SQLite database responsibilities, schemas, and migration expectations.

---

## Build, Deployment, and Runtime

- `BUILD_AND_DEPLOY.md`  
  PyInstaller builds, batch pipelines, and service installation.

- `USB_DEPLOYMENT.md`  
  USB detection logic, layout, and operational expectations.

- `PATH_RESOLUTION.md`  
  Filesystem path handling across dev, frozen, service, and USB modes.

---

## Client and UI

- `CLIENT_ARCHITECTURE.md`  
  AutoTech Client purpose, URI handlers, and verification flow.

- `TEMPLATES.md`  
  Jinja template structure, base layouts, and UI conventions.

---

## Operations and Maintenance

- `LOGGING.md`
  Logging expectations, structure, and offline observability.

- `TOOLS.md`
  Tool module inventory, dependencies, and offline safety profiles.

- `PITFALLS.md`
  Known risks, limitations, and common mistakes.

---

## Logging Implementation (Detailed)

- `LOGGING_INDEX.md`
  Navigation guide to all logging documentation.

- `LOGGING_QUICK_REFERENCE.md`
  Cheat sheet for common logging patterns.

- `LOGGING_DESIGN_SUMMARY.md`
  Executive summary and implementation timeline.

- `LOGGING_IMPLEMENTATION_GUIDE.md`
  Copy-paste code snippets and step-by-step tasks.

- `LOGGING_ARCHITECTURE.md`
  Complete architectural design (25+ pages).

---

## Agent and Skill Mapping

- `SKILL_SETS.md`  
  Skill domains used to guide agent selection and task routing.

---

## Usage Guidance

- Reference docs should be **updated whenever behavior changes**
- Do not duplicate large reference content into `CLAUDE.md`
- Documentation updates are handled by the **Docs Curator agent**
- If docs conflict with code, the docs must be corrected

This structure exists to keep Claude fast, accurate, and within context limits.
