# T1 Tools - Development & Deployment Guide

> **⚠️ CRITICAL: The production environment has NO INTERNET. All resources must be bundled locally.**

---

## 🖥️ Environment Overview

| Environment | Machine | Internet | Python | Purpose |
|-------------|---------|----------|--------|---------|
| **Development** | Windows Laptop (Win11) | ✅ Yes | ✅ Installed | Build, test, develop |
| **Production** | Windows 10 Server | ❌ NO | ❌ None | Run executable only |

---

## 🚨 CRITICAL OFFLINE REQUIREMENTS

Since production has **NO INTERNET**, you must:

| Requirement | Details |
|-------------|---------|
| **No CDN Links** | Never use `<script src="https://...">` or `<link href="https://...">` |
| **No External Fonts** | Don't use Google Fonts or other web fonts |
| **No API Calls to Internet** | All APIs must be local (`/api/...`) |
| **Bundle Everything** | All CSS, JS, images must be in `static/` folder |
| **PyInstaller Build** | Final deployment is a `.exe` file |

---

## 📁 Project Structure (Offline-Ready)

```
T1_Tools_Web/
├── main.py                     # Flask application
├── requirements.txt            # Python dependencies
├── T1_Tools_Web.spec          # PyInstaller spec file
├── T1_TOOLS_DESIGN_SYSTEM.md  # Design reference
├── DEVELOPMENT_GUIDE.md       # This file
│
├── static/                     # ⚠️ ALL static files HERE
│   ├── style.css              # Main stylesheet
│   ├── [any images]           # Local images only
│   └── [any JS files]         # Local scripts only
│
├── templates/                  # HTML templates
│   ├── enhanced_index.html
│   ├── ip_finder.html
│   └── [other templates]
│
├── tools/                      # Backend tool scripts
└── utils/                      # Utility functions
```

---

## 🔧 Development Workflow

### Step 1: Develop on Laptop

```cmd
cd C:\AutoTech_WebApps\T1_Tools_Web\t1_tools_redesign

:: Run development server
python main.py

:: Open browser to test
:: http://localhost:8888
```

### Step 2: Visual Testing Checklist

Before building, manually test ALL pages:

```
□ Dashboard loads correctly
□ Login modal works
□ Server health tiles display
□ Tool cards are clickable (when logged in)
□ IP Finder page loads
□ IP Finder search works
□ Equipment results display correctly
□ Flight Recorder button shows ONLY for K830E/K930E
□ VNC, TRU, AVI buttons work
□ Copy to clipboard works
□ Toast notifications appear
□ All pages have sidebar
□ Network status indicator updates
□ Responsive design (resize browser window)
□ No console errors (F12 → Console tab)
```

### Step 3: Build Executable

```cmd
:: Install PyInstaller (first time only)
pip install pyinstaller

:: Build executable
pyinstaller T1_Tools_Web.spec

:: Or build fresh
pyinstaller --onefile --windowed ^
    --add-data "templates;templates" ^
    --add-data "static;static" ^
    --add-data "tools;tools" ^
    --name T1_Tools_Web ^
    main.py
```

### Step 4: Test the Executable

```cmd
:: Run the built executable
cd dist
T1_Tools_Web.exe

:: Test EVERYTHING again visually
:: Same checklist as Step 2
```

### Step 5: Deploy to Production

```
1. Copy dist\T1_Tools_Web.exe to USB drive
2. Transfer to Win10 production server
3. Run executable
4. Verify in browser: http://localhost:8888
```

---

## 📋 Pre-Deployment Checklist

### Code Review
```
□ No external CDN links in HTML
□ No Google Fonts or external fonts
□ No external JavaScript libraries via CDN
□ All images are local (in static/ folder)
□ No hardcoded development URLs
□ API endpoints are relative (/api/...) not absolute
```

### Visual Testing (Development Machine)
```
□ Run python main.py
□ Test all pages in browser
□ Check browser console for errors (F12)
□ Test at different window sizes
□ Verify all buttons/links work
```

### Build Testing
```
□ PyInstaller build completes without errors
□ Run .exe file
□ Test all pages again
□ Verify static files load (CSS, images)
□ Check console for missing file errors
```

### Offline Simulation Test
```
□ Disconnect laptop from internet
□ Run .exe file
□ Verify everything still works
□ All styles load
□ All functionality works
```

---

## ⚠️ Common Offline Mistakes

### ❌ DON'T: Use CDN Links
```html
<!-- BAD - Won't work offline -->
<link href="https://fonts.googleapis.com/css?family=Roboto" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
```

### ✅ DO: Use Local Files
```html
<!-- GOOD - Works offline -->
<link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
<script src="{{ url_for('static', filename='chart.min.js') }}"></script>
```

### ❌ DON'T: Use External APIs
```javascript
// BAD - Won't work offline
fetch('https://api.external-service.com/data')
```

### ✅ DO: Use Local APIs
```javascript
// GOOD - Works offline
fetch('/api/remote-stats')
```

---

## 🔨 PyInstaller Spec File

Save as `T1_Tools_Web.spec`:

```python
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('templates', 'templates'),
        ('static', 'static'),
        ('tools', 'tools'),
        ('utils', 'utils'),
    ],
    hiddenimports=[
        'flask',
        'flask_cors',
        'jinja2',
        'werkzeug',
        'paramiko',
        'ping3',
        'requests',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='T1_Tools_Web',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Set to False for no console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
```

---

## 🧪 Testing Commands Quick Reference

```cmd
:: Development testing
python main.py

:: Build executable
pyinstaller T1_Tools_Web.spec

:: Test executable
cd dist
T1_Tools_Web.exe

:: Clean build (if issues)
rmdir /s /q build dist
del *.spec
pyinstaller --onefile --add-data "templates;templates" --add-data "static;static" --add-data "tools;tools" --name T1_Tools_Web main.py
```

---

## 📝 Version Control Notes

When committing changes:

```
□ Test visually before commit
□ Update version in VERSION.txt
□ Note what was changed
□ Build and test executable
□ Tag release version
```

---

## 🆘 Troubleshooting

### "Template not found" error after build
- Ensure `--add-data "templates;templates"` in PyInstaller command
- Check spec file has correct datas entries

### CSS not loading in executable
- Ensure `--add-data "static;static"` in PyInstaller command
- Verify `url_for('static', filename='style.css')` in templates

### "Module not found" error
- Add missing module to `hiddenimports` in spec file
- Rebuild with updated spec

### Application crashes silently
- Build with `console=True` to see error messages
- Check for missing dependencies

---

**Remember: If it doesn't work on your laptop with internet disabled, it won't work in production!**
