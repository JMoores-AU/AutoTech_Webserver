# T1 Tools Web Dashboard - Posterizarr-Style Redesign

## 🎯 Overview

This is your T1 Tools Web Dashboard redesigned with a modern Posterizarr-inspired interface while keeping **all backend functionality intact**.

## ✨ What's New

### Design Changes
- **Dark Theme**: Clean, modern dark interface with CSS variables for theming
- **Sidebar Navigation**: Easy access to all tools from a collapsible sidebar
- **Card-Based Layout**: Information organized into clean, readable cards
- **Professional Look**: Consistent styling throughout with proper spacing and typography
- **Responsive Design**: Works on desktop, tablet, and mobile devices

### What's Preserved (CRITICAL)
✅ **All Flask backend routes** - main.py unchanged  
✅ **IP Finder as dedicated page** - NOT inline  
✅ **Flight Recorder for K830E/K930E only** - Logic preserved  
✅ **External CSS** - No inline CSS blocks  
✅ **All tools and utilities** - Full functionality  

## 📁 File Structure

```
T1_Tools_Web/
├── main.py                         # Flask app (UNCHANGED)
├── requirements.txt                # Dependencies (UNCHANGED)
├── static/
│   └── style.css                   # NEW: Posterizarr-style CSS
├── templates/
│   ├── enhanced_index.html         # NEW: Main dashboard
│   ├── ip_finder.html              # NEW: IP Finder (dedicated page)
│   ├── login.html                  # NEW: Login page
│   ├── tool_generic.html           # NEW: Generic tool template
│   ├── error.html                  # NEW: Error pages
│   ├── ptx_uptime.html             # PRESERVED
│   ├── ptx_uptime_offline.html     # PRESERVED
│   └── mms_parameter_form.html     # PRESERVED
├── tools/                          # ALL TOOLS PRESERVED
└── utils/                          # ALL UTILS PRESERVED
```

## 🚀 Deployment Instructions

### Step 1: Backup Your Current Installation
```bash
# Create backup of your current T1_Tools_Web folder
copy T1_Tools_Web T1_Tools_Web_backup
```

### Step 2: Replace Frontend Files
Copy these files from the redesign to your installation:

1. **static/style.css** → Replace your existing style.css
2. **templates/enhanced_index.html** → Replace your existing enhanced_index.html
3. **templates/ip_finder.html** → Replace your existing ip_finder.html
4. **templates/login.html** → Replace your existing login.html
5. **templates/tool_generic.html** → NEW file, copy to templates/
6. **templates/error.html** → NEW file, copy to templates/

### Step 3: Keep These Files
**DO NOT REPLACE:**
- main.py (your backend)
- tools/ folder (all your tools)
- utils/ folder (utilities)
- Any other custom files you've added

### Step 4: Test
```bash
python main.py
```
Then open http://localhost:8888 in your browser.

## 🎨 CSS Theme Customization

The new design uses CSS variables for easy customization. Edit `static/style.css` to change:

```css
:root {
    /* Primary Colors - Change these for different themes */
    --theme-primary: #3b82f6;        /* Main accent color */
    --theme-primary-hover: #2563eb;  /* Hover state */
    
    /* Background Colors */
    --theme-bg: #0f0f0f;             /* Main background */
    --theme-bg-card: #1a1a1a;        /* Card backgrounds */
    
    /* Text Colors */
    --theme-text: #e5e5e5;           /* Main text */
    --theme-text-muted: #888888;     /* Secondary text */
}
```

## ⚠️ Critical Rules (DO NOT BREAK)

1. **Template**: Always use `enhanced_index.html` (NEVER `index.html`)
2. **IP Finder**: Must remain a dedicated page at `ip_finder.html` (NEVER inline)
3. **Flight Recorder**: Only shows for K830E/K930E equipment profiles
4. **Styling**: Dark mode with external CSS (NEVER inline CSS blocks)
5. **CSS**: Use external `style.css` file (NEVER embed 500+ lines of inline styles)

## 🔧 Features

### Dashboard
- Server health monitoring with auto-refresh
- Quick access tool grid
- Network status indicator
- System information panel

### IP Finder
- Equipment search by ID
- Quick access buttons for common equipment
- Copy-to-clipboard for IP addresses
- Action buttons: VNC, TRU, Flight Recorder*, AVI
- *Flight Recorder only shown for K830E/K930E

### Sidebar Navigation
- Categorized tool listing
- Active state highlighting
- Network status in footer
- Collapsible on smaller screens

## 📋 Browser Support

- Chrome/Edge (recommended)
- Firefox
- Safari
- Mobile browsers

## 🆘 Troubleshooting

### Tools don't appear?
- Make sure you're logged in (default password: komatsu)
- Check that main.py TOOL_LIST contains your tools

### Styling looks wrong?
- Clear browser cache (Ctrl+Shift+R)
- Verify style.css was copied correctly
- Check for CSS errors in browser console

### Flight Recorder not showing?
- This is intentional - only shows for K830E and K930E equipment
- Check equipment type in the database

## 📝 Notes

- The redesign is purely frontend - no backend changes required
- All API endpoints remain the same
- PyInstaller builds should work the same way
- Compatible with your existing deployment process

---

**Built with ❤️ for the T1 Tools team**
