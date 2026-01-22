# T1 Tools Web - AutoTech Dashboard

## Project Overview
Flask web app for Komatsu mining equipment remote access/diagnostics. Runs as standalone exe (PyInstaller) or dev server.

## Tech Stack
- **Backend**: Flask + Paramiko (SSH) + ping3
- **Frontend**: Jinja2 templates, vanilla JS, CSS
- **Build**: PyInstaller (`AutoTech.spec`)
- **DB**: SQLite (equipment_db.py, ptx_uptime_db.py)

## Key Paths
- `main.py` - Flask app entry point, all routes
- `tools/` - Tool modules (ptx_uptime.py, ip_finder.py, etc.)
- `templates/` - Jinja2 HTML templates
- `static/` - CSS/JS assets
- `autotech_client/` - Client installer + batch scripts
- `database/` - SQLite DBs

## Architecture
- Routes in main.py call tool functions from `tools/*.py`
- Templates extend `_BASE_TEMPLATE.html` or `layout.html`
- SSH via Paramiko to Linux servers (serverList.py has IPs)
- Equipment data cached in SQLite

## Common Tools
| Tool | Route | Purpose |
|------|-------|---------|
| PTX Uptime | /ptx-uptime | Check PTX controller uptimes |
| IP Finder | /ip-finder | Search equipment by IP/ID |
| T1 Legacy | /t1-legacy | Launch batch scripts in CMD |
| Playback | /playback-tools | USB playback file tools |

## Build Commands
```batch
pyinstaller AutoTech.spec
# or
BUILD_WEBSERVER.bat
```

## Server Credentials
Stored in `main.py` as MMS_PASSWORD constant. SSH user: `mms`

## Conventions
- Tool routes: `/tool-name` (kebab-case)
- API endpoints: `/api/tool-name/action`
- Templates: `tool_name.html` (snake_case)

---

## Token Usage Optimization (IMPORTANT)

### Model Usage
- **Default: Sonnet** (set in `.claude/settings.local.json`)
- Use Haiku for sub-agents when appropriate
- Opus only for critical/complex problems

### Efficient Prompting (for non-coders)

**GOOD prompts (specific, single action):**
- "Add a button to ptx_uptime.html that clears the results table"
- "Fix the IP Finder search to also search by equipment name"
- "Build the exe with BUILD_WEBSERVER.bat"
- "Change the page title from 'PTX Uptime' to 'Controller Uptime'"

**BAD prompts (vague, causes exploration):**
- "Make the page better"
- "Fix the bugs"
- "Update the tool"
- "Look into the performance issues"

### Guidelines to Reduce Tokens
1. **Be specific** - Name exact files, routes, or buttons
2. **One task at a time** - Don't bundle 5 requests in one prompt
3. **Trust CLAUDE.md** - Don't ask "how does X work?" unless needed
4. **Use exact text** - Copy/paste button text or error messages
5. **Avoid exploration** - If you know the file, say it: "in templates/ptx_uptime.html line 42"

### Common Tasks (Quick Reference)
```
Add a button → "Add [button name] to [template file] that does [action]"
Fix a bug → "In [file], [specific issue], should be [expected behavior]"
Build exe → "Run BUILD_WEBSERVER.bat"
Commit → "Commit changes with message: [your message]"
Change text → "In [file], change '[old text]' to '[new text]'"
```

### When Token Usage Spikes
- Long exploration sessions (asking vague questions)
- Back-and-forth clarifications (be specific upfront)
- Reading many files unnecessarily (name the file if you know it)
- Large git status (keep it clean with regular commits)
