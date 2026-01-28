Repository Guidelines
=====================

## Project Structure & Module Organization
- `main.py` – Flask entrypoint and routes; integrations with PTX uptime, FrontRunner, tools.
- `templates/` – Jinja2 HTML views (e.g., `ptx_uptime.html`, dashboards).
- `static/` – Shared CSS/JS assets.
- `tools/` – Python helpers (PTX uptime sync/DB, health checks).
- `database/` – SQLite data files (PTX uptime, etc.).
- `autotech_client/` – Client-side tools/assets; mirrors some server helpers.
- `backups/` – Dated snapshots of `main.py` for rollback.

## Build, Test, and Development Commands
- `python main.py` – Run the Flask app locally (uses templates/static in-place).
- `npm run lint` / `npm run format` – JS/TS lint/format if frontend assets change.
- `pytest -q` – Run Python unit tests (if/when present).
- `npm run build` – Build static assets when frontend bundle exists.
- Tip: prefer `npm ci` over `npm install` in CI for deterministic installs.

## Coding Style & Naming Conventions
- Python: PEP8-ish; 4-space indent; keep functions small; prefer explicit logging via `logger`.
- Templates: keep Jinja expressions minimal; reuse shared CSS variables defined in `static/style.css`.
- Naming: snake_case for Python, kebab-case for assets, PascalCase for React/JSX components (if added).
- Avoid new dependencies unless justified; document any new env vars in `README.md` or `docs/`.

## Testing Guidelines
- Add regression tests for bug fixes; cover happy path + one failure case.
- Name tests `test_<feature>.py` and keep fixtures close to usage.
- For PTX uptime changes, mock SSH/DB where possible; don’t depend on live MMS server.

## Commit & Pull Request Guidelines
- Commits: conventional style (`feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `test:`).
- PRs: include "What/Why", test commands/results, risks/rollout notes; attach screenshots for UI changes.
- Keep diffs small and behavior-preserving unless feature work is requested.
- Use `git-workflow-specialist` agent for Git operations, versioning, and changelog updates.

## Security & Config Tips
- Never commit secrets or `.env` contents; sanitize logs (no IP passwords/tokens).
- Config changes should explain impact; prefer env vars for secrets with sane defaults.
- Validate external input (webhooks, file uploads); fail fast with clear errors.

## Agent-Specific Notes
- Scan relevant files before edits; prefer minimal diffs.
- If touching infra/config, describe what changed and why to avoid silent drift.
- Run the fastest applicable validation (lint/tests) when changing logic; note results in summaries.

