# Pitfalls and Gotchas

This document lists known risks, limitations, and common mistakes when developing or modifying AutoTech. It exists to prevent regression and operational surprises.

---

## 1. SSH Connection Handling

- Paramiko connections are not pooled
- Each route creates a new SSH connection
- Long-running SSH calls can block if not handled carefully
- Connection failures must be logged explicitly

---

## 2. Session Reset on Restart

- Session secret is generated at startup
- All users are logged out on restart
- This behavior is expected but should be understood

---

## 3. Background Thread Cleanup

- Daemon threads do not guarantee cleanup
- `stop_event` must be set on shutdown
- SSH connections must be closed explicitly

Failure to handle shutdown correctly can cause:
- hung services
- corrupted state
- incomplete writes

---

## 4. Client Installation Dependency

- Remote users must install AutoTech Client
- Without client, tools execute on server (incorrect)
- Dashboard warning banner indicates unverified client
- This is a design requirement, not a bug

---

## 5. USB Deployment Overwrites

- USB deployment overwrites files without prompting
- No built-in backup mechanism exists
- Version control is the only rollback mechanism

---

## 6. Path Resolution Errors

Common mistakes include:
- using relative paths (`./database`)
- assuming working directory equals project root
- writing to `sys._MEIPASS`
- hardcoding drive letters

All paths must resolve from runtime base directory.

---

## 7. Memory Growth Risks

- `download_progress` dictionary grows unbounded
- No automatic cleanup implemented
- Long-running servers may accumulate stale entries

This should be monitored or mitigated if usage increases.

---

## 8. Hardcoded Credentials

- SSH credentials exist in code
- Server IPs are stored in source
- Acceptable only in private, isolated networks
- Must not leak into public or shared repositories

---

## 9. PyInstaller Hidden Imports

- New dependencies may fail silently when frozen
- Missing hidden imports cause runtime crashes
- Always test frozen builds after adding dependencies

---

## 10. Related Reference Documents

- `PATH_RESOLUTION.md`
- `BUILD_AND_DEPLOY.md`
- `ARCHITECTURE.md`
