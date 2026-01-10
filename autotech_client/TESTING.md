# AutoTech Client Setup - Testing Guide

## Prerequisites

1. **Portable Tools Downloaded**
   - Ensure all tools are in `client_setup/tools/`:
     - putty.exe
     - plink.exe
     - pscp.exe
     - WinSCP.exe
     - vncviewer.exe

2. **Flask Server Running**
   - Server should be accessible via IP:Port
   - Navigate to T1 Legacy Tools page

---

## Installation Testing

### Test 1: Client Setup Installation

1. **Copy Client Setup Files:**
   ```
   C:\AutoTech_WebApps\T1_Tools_Web-1\client_setup\
   ```

2. **Run Installer as Administrator:**
   ```
   Right-click: client_setup\scripts\install.bat
   Select: Run as administrator
   ```

3. **Verify Installation:**
   ```
   ✓ C:\AutoTech_Client\ folder created
   ✓ Tools copied: putty.exe, plink.exe, pscp.exe, WinSCP.exe, vncviewer_5.3.2.exe
   ✓ Scripts folder: C:\AutoTech_Client\scripts\
   ✓ Launcher scripts: launch_putty.bat, launch_winscp.bat, launch_vnc.bat
   ✓ Uninstaller created: C:\AutoTech_Client\Uninstall.bat
   ```

4. **Verify Registry Entries:**
   ```
   Run: regedit
   Navigate to: HKEY_CLASSES_ROOT\
   Confirm keys exist:
   - autotech-ssh
   - autotech-sftp
   - autotech-vnc
   ```

---

## Functionality Testing

### Test 2: VNC Viewer Launch (Start PTX VNC)

**Setup:**
1. Open web interface: `http://SERVER_IP:8888/legacy`
2. Enter equipment name: `TEST`
3. Click "Find Details" button

**Test Steps:**
1. Click "Start PTX VNC" button
2. Check terminal output:
   ```
   [DEBUG] [TEST MODE] Looking up IP for equipment: TEST
   [DEBUG] Found PTX IP: 10.110.99.99
   [DEBUG] Equipment status: ONLINE

   VNC Connection Details:
   Host: 10.110.99.99
   Port: 5900

   Launching VNC Viewer on your computer...
   ```

3. **Expected Result:**
   - VNC Viewer launches on YOUR computer (not server)
   - Connection dialog shows: `10.110.99.99:5900`
   - Browser may show URI security prompt (allow it)

**Verify:**
- ✓ VNC Viewer opened on client PC
- ✓ Connection details pre-filled
- ✓ Server didn't launch VNC

---

### Test 3: Custom URI Handler

**Manual URI Test:**
1. Open Run dialog: `Win + R`
2. Type: `autotech-vnc://10.110.21.87:5900`
3. Press Enter

**Expected:**
- VNC Viewer launches with IP 10.110.21.87:5900

**Test Other URIs:**
```
autotech-ssh://mms@10.110.19.107:22
autotech-sftp://mms:password@10.110.19.107:22
```

---

### Test 4: Real Equipment (Online Mode)

**Prerequisites:**
- Be on production network
- Have real equipment name (e.g., AHG69)

**Test Steps:**
1. Enter equipment: `AHG69`
2. Click "Find Details"
3. Verify IP lookup:
   ```
   [DEBUG] Looking up IP for equipment: AHG69
   [DEBUG] Found PTX IP: 10.110.21.87
   [DEBUG] Equipment status: ONLINE
   ```

4. Click "Start PTX VNC"
5. **Expected:**
   - VNC Viewer launches
   - Connects to actual equipment IP
   - Equipment buttons remain enabled

---

### Test 5: Offline Equipment Detection

**Test Steps:**
1. Enter equipment: `BROKEN`
2. Click "Find Details"
3. Check status:
   ```
   [DEBUG] Equipment status: OFFLINE
   Equipment Status: OFFLINE
   ```

**Expected:**
- Equipment status badge turns RED
- All equipment tool buttons become DISABLED/greyed out
- Start PTX VNC button disabled

---

### Test 6: Multiple Remote Clients

**Setup:**
- 2-3 PCs with AutoTech Client installed
- All connected to same Flask server

**Test Steps:**
1. **PC 1:** Launch VNC to AHG69
2. **PC 2:** Launch VNC to RD35
3. **PC 3:** Launch PuTTY to MMS server

**Expected:**
- Each PC launches their OWN local application
- Applications run independently on each PC
- Server doesn't slow down or crash
- All connections work simultaneously

---

### Test 7: File Download (PTX Uptime Report)

**Test Steps:**
1. Click "PTX Uptime Report" (sidebar)
2. Check terminal:
   ```
   Downloaded: PTX_Uptime_Report.html
   Preparing file for your browser...
   File will download to your computer.
   ```

3. **Expected:**
   - File downloads to YOUR Downloads folder (not server)
   - Browser download notification appears
   - File can be opened in Edge/Chrome

---

## Error Testing

### Test 8: No Client Setup Installed

**Test Steps:**
1. On a PC WITHOUT AutoTech Client installed
2. Try to launch VNC
3. Click custom URI

**Expected:**
- Browser shows "Unknown protocol" error
- Terminal shows: "If the application didn't launch, you may need to install AutoTech Client."

---

### Test 9: Uninstallation

**Test Steps:**
1. Run: `C:\AutoTech_Client\Uninstall.bat`
2. **Expected:**
   ```
   Uninstalling AutoTech Client...
   Registry entries removed
   Folder deleted: C:\AutoTech_Client\
   ```

3. **Verify:**
   - Folder deleted
   - Registry keys removed
   - Custom URIs no longer work

---

## Success Criteria

✅ **Installation:**
- Installer completes without errors
- All files copied correctly
- Registry entries created

✅ **VNC Launch:**
- Launches on client PC (not server)
- Pre-fills connection details
- Works with TEST and real equipment

✅ **Multi-Client:**
- 3+ PCs can use simultaneously
- Each runs own applications
- No server performance issues

✅ **File Downloads:**
- Downloads to client PC
- Works from remote PCs
- No files left on server

✅ **Error Handling:**
- Graceful failure without client setup
- Clear error messages
- Equipment offline detection works

---

## Troubleshooting

### VNC Doesn't Launch
1. Check: `C:\AutoTech_Client\vncviewer.exe` exists
2. Test URI manually: `Win+R` → `autotech-vnc://10.110.21.87:5900`
3. Check registry: `regedit` → `HKEY_CLASSES_ROOT\autotech-vnc`

### Browser Blocks URI
- Chrome/Edge may ask for permission
- Click "Allow" or "Open"
- Check browser security settings

### Wrong PC Launches App
- Check: Are you RDP'd into the server?
- Launch should happen on YOUR physical PC
- Not on the server hosting Flask

---

## Next Steps After Successful Testing

1. ✅ Document installation process for users
2. ✅ Create installer distribution package
3. ✅ Update web interface with setup instructions
4. ✅ Train users on AutoTech Client setup
5. ✅ Monitor for issues in production

---

## Testing Complete!

Good night! All implementation is complete and ready for testing tomorrow.
