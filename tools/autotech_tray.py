#!/usr/bin/env python3
"""
AutoTech System Tray Application
Runs AutoTech web server in background with taskbar tray icon
"""

import os
import sys
import subprocess
import webbrowser
import time
from pathlib import Path

try:
    import pystray
    from PIL import Image, ImageDraw
except ImportError:
    print("ERROR: Required packages not installed!")
    print("Run: pip install pystray pillow")
    input("Press Enter to exit...")
    sys.exit(1)

# Configuration
AUTOTECH_EXE = "AutoTech.exe"
AUTOTECH_URL = "http://localhost:8888"
PORT = 8888

class AutoTechTray:
    def __init__(self):
        self.autotech_process = None
        self.icon = None
        self.running = False

    def create_icon_image(self, color='green'):
        """Create a simple icon for the system tray"""
        # Create 64x64 icon with wrench/tool symbol
        img = Image.new('RGB', (64, 64), color='white')
        draw = ImageDraw.Draw(img)

        # Draw a simple tool/wrench icon
        if color == 'green':
            fill_color = (34, 197, 94)  # Green when running
        elif color == 'red':
            fill_color = (239, 68, 68)  # Red when stopped
        else:
            fill_color = (156, 163, 175)  # Gray

        # Draw wrench shape
        draw.ellipse([20, 15, 44, 39], fill=fill_color)
        draw.rectangle([28, 35, 36, 55], fill=fill_color)
        draw.rectangle([25, 50, 39, 58], fill=fill_color)

        return img

    def find_autotech_exe(self):
        """Find AutoTech.exe in common locations"""
        search_paths = [
            Path.cwd() / AUTOTECH_EXE,                           # Current directory
            Path.cwd() / "dist" / AUTOTECH_EXE,                  # Build directory
            Path("E:/") / AUTOTECH_EXE,                          # USB root
            Path("E:/AutoTech") / AUTOTECH_EXE,                  # USB AutoTech folder
            Path("C:/AutoTech") / AUTOTECH_EXE,                  # Installed location
            Path(sys.executable).parent / AUTOTECH_EXE,          # Same dir as tray exe
        ]

        for path in search_paths:
            if path.exists():
                return str(path.resolve())

        return None

    def is_port_in_use(self):
        """Check if AutoTech is already running"""
        try:
            result = subprocess.run(
                ['netstat', '-an'],
                capture_output=True,
                text=True,
                timeout=2,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            return f':{PORT}' in result.stdout and 'LISTENING' in result.stdout
        except:
            return False

    def start_autotech(self):
        """Start AutoTech.exe in background"""
        if self.running:
            return "Already running"

        if self.is_port_in_use():
            self.running = True
            self.update_icon('green')
            return "AutoTech already running"

        exe_path = self.find_autotech_exe()
        if not exe_path:
            return f"Error: {AUTOTECH_EXE} not found!\n\nSearched:\n- Current directory\n- E:\\ USB drive\n- C:\\AutoTech"

        try:
            # Start AutoTech.exe hidden (no window)
            self.autotech_process = subprocess.Popen(
                [exe_path],
                creationflags=subprocess.CREATE_NO_WINDOW,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            # Wait for server to start
            time.sleep(2)

            if self.is_port_in_use():
                self.running = True
                self.update_icon('green')
                return "AutoTech started successfully"
            else:
                return "Error: AutoTech started but not responding"

        except Exception as e:
            return f"Error starting AutoTech: {str(e)}"

    def stop_autotech(self):
        """Stop AutoTech.exe"""
        if not self.running:
            return "Not running"

        try:
            # Kill AutoTech.exe process
            subprocess.run(
                ['taskkill', '/F', '/IM', AUTOTECH_EXE],
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            if self.autotech_process:
                self.autotech_process.terminate()
                self.autotech_process = None

            time.sleep(1)
            self.running = False
            self.update_icon('red')
            return "AutoTech stopped"

        except Exception as e:
            return f"Error stopping AutoTech: {str(e)}"

    def restart_autotech(self):
        """Restart AutoTech.exe"""
        self.stop_autotech()
        time.sleep(1)
        return self.start_autotech()

    def open_browser(self):
        """Open AutoTech dashboard in default browser"""
        if not self.is_port_in_use():
            return "AutoTech is not running!"

        try:
            webbrowser.open(AUTOTECH_URL)
            return "Opening dashboard..."
        except Exception as e:
            return f"Error opening browser: {str(e)}"

    def update_icon(self, color):
        """Update tray icon color"""
        if self.icon:
            self.icon.icon = self.create_icon_image(color)

    def show_notification(self, message):
        """Show system notification"""
        if self.icon:
            self.icon.notify(message, "AutoTech")

    # Menu actions
    def action_open(self, icon, item):
        """Open dashboard"""
        msg = self.open_browser()
        self.show_notification(msg)

    def action_start(self, icon, item):
        """Start AutoTech"""
        msg = self.start_autotech()
        self.show_notification(msg)

    def action_stop(self, icon, item):
        """Stop AutoTech"""
        msg = self.stop_autotech()
        self.show_notification(msg)

    def action_restart(self, icon, item):
        """Restart AutoTech"""
        msg = self.restart_autotech()
        self.show_notification(msg)

    def action_exit(self, icon, item):
        """Exit tray application"""
        self.stop_autotech()
        icon.stop()

    def create_menu(self):
        """Create system tray menu"""
        return pystray.Menu(
            pystray.MenuItem("Open Dashboard", self.action_open, default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Start Server", self.action_start),
            pystray.MenuItem("Stop Server", self.action_stop),
            pystray.MenuItem("Restart Server", self.action_restart),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit", self.action_exit)
        )

    def run(self):
        """Run the system tray application"""
        # Auto-start AutoTech on launch
        start_msg = self.start_autotech()

        # Create system tray icon
        icon_image = self.create_icon_image('green' if self.running else 'red')
        self.icon = pystray.Icon(
            "AutoTech",
            icon_image,
            "AutoTech Dashboard",
            menu=self.create_menu()
        )

        # Show startup notification
        self.icon.notify(start_msg, "AutoTech")

        # Run the icon (blocking)
        self.icon.run()


def main():
    """Main entry point"""
    # Check if already running
    try:
        result = subprocess.run(
            ['tasklist'],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        if result.stdout.count('AutoTech_Tray.exe') > 1:
            print("AutoTech Tray is already running!")
            print("Check your system tray (next to clock)")
            time.sleep(3)
            sys.exit(0)
    except:
        pass

    # Run tray application
    app = AutoTechTray()
    app.run()


if __name__ == '__main__':
    main()
