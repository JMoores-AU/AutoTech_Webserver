# AGENTS.md

This repository uses Codex CLI agents to help with development tasks.  
Agents must follow the rules below so changes are safe, reviewable, and consistent.

---

## 1) Non-negotiables

- **Do not break builds or tests.**
- **Small, reviewable changes** are preferred over “big bang” refactors.
- **Preserve existing behavior** unless the task explicitly requires a change.
- **No secrets**: never commit tokens, passwords, private keys, `.env` contents, certs, or credentials.
- **No silent config drift**: if you touch configs/infra, explain *why* and *what changed*.

---

## 2) Repo assumptions

- Root contains this file: `AGENTS.md`
- Common directories (may not all exist):
  - `src/` application code
  - `tests/` automated tests
  - `docs/` documentation
  - `.github/` CI workflows
  - `scripts/` helper scripts
  - `infra/` or `deploy/` infrastructure

If your repo differs, update this section so agents don’t guess.

---

## 3) Working rules for agents

### 3.1 Before making changes
1. **Read the task** and restate the goal in one sentence.
2. **Scan relevant files** first (don’t guess structure).
3. Identify:
   - expected inputs/outputs
   - constraints (performance, backwards compatibility, security)
   - test coverage (what should validate this change)

### 3.2 While making changes
- Prefer minimal diffs.
- Keep formatting consistent with existing code.
- Avoid new dependencies unless asked; if needed, justify them.
- If you change behavior:
  - update/add tests
  - update docs if user-facing

### 3.3 After making changes
- Run the fastest available validation:
  - lint (if present)
  - unit tests
  - any relevant build step
- Provide a short summary:
  - what changed
  - where it changed (paths)
  - how to validate

---

## 4) Commands agents should use

> Update these to match your project. Agents should not invent commands.

### Install
- If Node:
  - `npm ci` (preferred) or `npm install`
- If Python:
  - `python -m venv .venv`
  - `. .venv/bin/activate` (mac/linux) or `.venv\Scripts\activate` (windows)
  - `pip install -r requirements.txt`
- If .NET:
  - `dotnet restore`

### Lint / Format
- `npm run lint`
- `npm run format`
- `ruff check .`
- `black .`
- `dotnet format`

### Tests
- `npm test`
- `pytest -q`
- `dotnet test`

### Build / Run
- `npm run build`
- `npm run dev`
- `python -m <module>`
- `dotnet run`

If none exist, add a **Makefile** or documented script entrypoints (preferred).

---

## 5) File editing conventions

### 5.1 Logging
- Use existing logging framework/pattern.
- Avoid noisy logs in hot paths.
- Don’t log secrets or PII.

### 5.2 Error handling
- Fail fast on invalid inputs.
- Return actionable messages.
- Prefer typed/structured errors if the codebase already does.

### 5.3 Configuration
- Prefer environment variables for secrets.
- Document new config keys in `README.md` or `docs/`.
- Provide sane defaults when possible.

---

## 6) Tests and quality bar

- Any bug fix should include a regression test when feasible.
- Any new feature should include tests for:
  - happy path
  - at least one failure/edge case
- If tests cannot be added, explain why and how risk is mitigated.

---

## 7) PR / commit standards (for agent output)

### Commit message
Use conventional style where possible:

- `feat: ...`
- `fix: ...`
- `chore: ...`
- `docs: ...`
- `refactor: ...`
- `test: ...`

### PR description (agent summary)
Include:
- What / Why
- How tested (exact command + result)
- Risks / rollout notes (if any)

---

## 8) Security checklist

Agents must ensure:
- No credentials in code or logs
- Dependency changes are minimal and justified
- Input validation for anything external (webhooks, files, CLI args)
- Safe file operations (no `rm -rf` style accidents, avoid destructive defaults)

---

## 9) When unsure

If there’s ambiguity:
- Choose the **least risky** option.
- Keep changes local and reversible.
- Document assumptions in the summary.

---

## 10) Agent roster (optional but recommended)

If you use multiple agents, list them here so tasks route cleanly:

- **backend-engineer**: API, DB, services
- **frontend-engineer**: UI, components
- **devops**: CI/CD, containers, deployment
- **qa**: test plans, automation
- **docs-writer**: documentation updates
- **security-reviewer**: threat checks, secret scanning guidance

Add or remove as needed.
