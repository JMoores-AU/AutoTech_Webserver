# Changelog

All notable changes to AutoTech Web Dashboard are documented here.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Git workflow specialist agent for version control management
- Cross-machine work context tracking via `.claude/CURRENT_WORK.md`
- Automatic CURRENT_WORK.md updates with every commit

### Changed

### Fixed

### Removed

---

## [v1.0.0] - 2025-01-29

### Added
- Initial release of AutoTech Web Dashboard
- Flask-based web application for Komatsu mining equipment diagnostics
- PyInstaller build pipeline for standalone Windows executable
- Windows service deployment support
- USB deployment capabilities with variable drive letter support
- PTX uptime monitoring and synchronization
- FrontRunner integration and playback tools
- Real-time download progress tracking with progress bars
- Playback file prediction and multi-file management
- Client installation system with URI handlers:
  - `autotech-ssh://` - SSH via PuTTY
  - `autotech-sftp://` - SFTP via WinSCP
  - `autotech-vnc://` - VNC viewer
  - `autotech-script://` - MMS script execution
- USB tool detection (CamStudio, Playback tools)
- IP Finder utility
- Specialized Claude agents:
  - `usb-client-specialist` - USB detection and client installation
  - `pyinstaller-build-specialist` - Build and deployment
  - `flask-logging-architect` - Logging infrastructure
  - `offline-test-authority` - Test protocols and validation
  - `docs-curator` - Documentation maintenance
  - `git-workflow-specialist` - Version control and changelog

### Technical
- Offline/air-gapped production environment support
- Path resolution for frozen, service, and USB execution modes
- SQLite database integration
- Jinja2 templating with shared CSS/JS assets
