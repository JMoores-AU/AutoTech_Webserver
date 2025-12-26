# T1 Tools Web Dashboard - Design System & Project Context

> **⚠️ IMPORTANT: Provide this file to any developer or AI assistant working on this project.**

---

## 🎯 Project Overview

**T1 Tools Web Dashboard** - Mining equipment remote access system for Komatsu equipment management.

- **Framework**: Flask (Python)
- **Design Style**: Posterizarr-inspired dark theme
- **Deployment**: PyInstaller Windows executable

---

## 🚨 CRITICAL RULES - NEVER BREAK

| Rule | Requirement |
|------|-------------|
| **Template** | Always use `enhanced_index.html` (NEVER `index.html`) |
| **IP Finder** | Must remain a **dedicated page** at `ip_finder.html` (NEVER inline) |
| **Flight Recorder** | Only shows for **K830E/K930E** equipment profiles |
| **CSS** | Use external `style.css` file (NEVER embed inline CSS blocks) |
| **Theme** | Dark mode only (NEVER revert to light mode) |

---

## 📁 File Structure

```
T1_Tools_Web/
├── main.py                         # Flask app with routes
├── requirements.txt                # Python dependencies
├── static/
│   └── style.css                   # ⭐ MASTER STYLESHEET
├── templates/
│   ├── enhanced_index.html         # ⭐ Main dashboard
│   ├── ip_finder.html              # ⭐ Dedicated IP Finder page
│   ├── login.html                  # Login page
│   ├── tool_generic.html           # Generic tool template
│   ├── error.html                  # Error pages (404, 500)
│   ├── ptx_uptime.html             # PTX Uptime tool
│   └── [other tool templates]
├── tools/                          # Backend tool scripts
└── utils/                          # Utility functions
```

---

## 🎨 Design System

### Color Palette (CSS Variables)

```css
:root {
    /* Primary Colors */
    --theme-primary: #3b82f6;           /* Blue - buttons, links, accents */
    --theme-primary-hover: #2563eb;     /* Darker blue for hover */
    --theme-primary-light: rgba(59, 130, 246, 0.15);  /* Subtle backgrounds */
    
    /* Background Colors */
    --theme-bg: #0f0f0f;                /* Main page background */
    --theme-bg-secondary: #141414;      /* Secondary/header background */
    --theme-bg-card: #1a1a1a;           /* Card backgrounds */
    --theme-bg-card-hover: #242424;     /* Card hover state */
    --theme-bg-sidebar: #111111;        /* Sidebar background */
    
    /* Text Colors */
    --theme-text: #e5e5e5;              /* Primary text */
    --theme-text-muted: #888888;        /* Secondary/muted text */
    --theme-text-bright: #ffffff;       /* Headings, emphasis */
    
    /* Border Colors */
    --theme-border: #2a2a2a;            /* Default borders */
    --theme-border-light: #333333;      /* Lighter borders (hover) */
    
    /* Status Colors */
    --status-online: #22c55e;           /* Green - online/success */
    --status-offline: #ef4444;          /* Red - offline/error */
    --status-warning: #f59e0b;          /* Amber - warnings */
    --status-info: #3b82f6;             /* Blue - info */
    
    /* Action Button Colors */
    --btn-vnc: #8b5cf6;                 /* Purple - VNC */
    --btn-tru: #06b6d4;                 /* Cyan - TRU Access */
    --btn-flight: #f59e0b;              /* Amber - Flight Recorder */
    --btn-avi: #ec4899;                 /* Pink - AVI System */
}
```

### Typography

- **Font Family**: `'Segoe UI', -apple-system, BlinkMacSystemFont, 'Roboto', sans-serif`
- **Monospace** (IPs, code): `'Consolas', 'Monaco', monospace`

| Element | Size | Weight | Color |
|---------|------|--------|-------|
| Page Title | 1.25rem | 600 | `--theme-text-bright` |
| Section Title | 1.1rem | 600 | `--theme-text-bright` |
| Card Title | 1rem | 600 | `--theme-text-bright` |
| Body Text | 0.9rem | 400 | `--theme-text` |
| Muted Text | 0.85rem | 400 | `--theme-text-muted` |
| Labels | 0.7rem | 600 | `--theme-text-muted` |

### Border Radius

```css
--radius-sm: 6px;    /* Small elements, buttons */
--radius-md: 10px;   /* Cards, inputs */
--radius-lg: 14px;   /* Large cards */
--radius-xl: 20px;   /* Modals, featured cards */
```

### Shadows

```css
--shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.3);
--shadow-md: 0 4px 12px rgba(0, 0, 0, 0.4);
--shadow-lg: 0 8px 24px rgba(0, 0, 0, 0.5);
```

---

## 🧩 Component Patterns

### Page Layout Structure

Every page follows this structure:

```html
<body>
    <div class="app-container">
        
        <!-- SIDEBAR (consistent across all pages) -->
        <aside class="sidebar">
            <div class="sidebar-header">...</div>
            <nav class="sidebar-nav">...</nav>
            <div class="sidebar-footer">...</div>
        </aside>
        
        <!-- MAIN CONTENT -->
        <main class="main-content">
            <header class="top-header">...</header>
            <div class="content-container">
                <!-- Page-specific content here -->
            </div>
        </main>
        
    </div>
</body>
```

### Card Component

```html
<div class="card">
    <div class="card-header">
        <h2 class="card-title">
            <span class="card-title-icon">🔧</span>
            Card Title
        </h2>
    </div>
    <div class="card-body">
        <!-- Content -->
    </div>
    <div class="card-footer">
        <!-- Optional footer -->
    </div>
</div>
```

### Section with Header

```html
<section class="mb-5">
    <div class="section-header">
        <h2 class="section-title">
            <span class="section-title-icon">⚡</span>
            Section Title
        </h2>
        <button class="btn btn-ghost btn-sm">Action</button>
    </div>
    
    <!-- Section content -->
</section>
```

### Button Classes

```html
<button class="btn btn-primary">Primary Action</button>
<button class="btn btn-secondary">Secondary</button>
<button class="btn btn-ghost">Ghost/Subtle</button>
<button class="btn btn-danger">Danger/Delete</button>

<!-- Sizes -->
<button class="btn btn-primary btn-sm">Small</button>
<button class="btn btn-primary btn-lg">Large</button>

<!-- Action buttons (IP Finder) -->
<button class="btn btn-vnc">🖥️ VNC</button>
<button class="btn btn-tru">🔗 TRU</button>
<button class="btn btn-flight">✈️ Flight Recorder</button>
<button class="btn btn-avi">📹 AVI</button>
```

### Form Inputs

```html
<div class="form-group">
    <label class="form-label" for="input">Label</label>
    <input type="text" id="input" class="form-input" placeholder="Placeholder">
</div>
```

### Toast Notifications (JavaScript)

```javascript
showToast('Message text', 'success');  // Green
showToast('Message text', 'error');    // Red
showToast('Message text', 'info');     // Blue
showToast('Message text', 'warning');  // Amber
```

---

## 🔧 Special Routes

| Route | Template | Notes |
|-------|----------|-------|
| `/` | `enhanced_index.html` | Main dashboard |
| `/run/IP Finder` | `ip_finder.html` | **DEDICATED PAGE** - never inline |
| `/run/<tool_name>` | `tool_generic.html` or specific | Other tools |
| `/api/remote-stats` | JSON | Server health data |
| `/api/mode` | JSON | Network online/offline status |
| `/api/find_equipment` | JSON | Equipment search |

---

## ✈️ Flight Recorder Logic

**CRITICAL**: Flight Recorder functionality is ONLY available for K830E and K930E equipment profiles.

```python
# In main.py
EQUIPMENT_PROFILES = {
    'K830E': {'has_flight_recorder': True, 'ptx_offset': 1},
    'K930E': {'has_flight_recorder': True, 'ptx_offset': 1},
    'Other': {'has_flight_recorder': False, 'ptx_offset': 0}
}
```

```javascript
// In ip_finder.html - check before showing button
const hasFlightRecorder = equipment.ptx_type && 
    (equipment.ptx_type === 'K830E' || equipment.ptx_type === 'K930E');

${hasFlightRecorder ? `
    <button class="action-btn btn-flight">✈️ Flight Recorder</button>
` : ''}
```

---

## 📝 Creating New Tool Pages

When adding a new tool, follow this template:

1. **Copy** `tool_generic.html` as starting point
2. **Keep** the sidebar and header structure
3. **Modify** only the content inside `<div class="content-container">`
4. **Use** existing CSS classes - don't add inline styles
5. **Follow** the card-based layout pattern

---

## ⚠️ Common Mistakes to AVOID

| ❌ Don't | ✅ Do Instead |
|----------|---------------|
| Use `index.html` | Use `enhanced_index.html` |
| Make IP Finder inline | Keep as dedicated `ip_finder.html` page |
| Add inline CSS blocks | Add classes to `style.css` |
| Use light backgrounds | Keep dark theme (`#0f0f0f` base) |
| Remove Flight Recorder check | Always check for K830E/K930E |
| Use random colors | Use CSS variables |
| Skip the sidebar | Include sidebar on all pages |

---

## 🚀 Development Commands

```bash
# Run development server
python main.py

# Access at
http://localhost:8888

# Default password
komatsu
```

---

## 📋 Checklist for New Development

Before committing any changes, verify:

- [ ] Uses `enhanced_index.html` as main template
- [ ] IP Finder is still a dedicated page
- [ ] Flight Recorder only shows for K830E/K930E
- [ ] No inline CSS blocks added
- [ ] Dark theme maintained
- [ ] Sidebar present on all pages
- [ ] Uses existing CSS classes/variables
- [ ] Responsive design not broken

---

**Last Updated**: December 2024  
**Design Version**: Posterizarr-Style v1.0
