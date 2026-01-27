# AutoTech Web Dashboard

## Project Overview

The AutoTech Web Dashboard is a Python Flask application designed as a mining equipment remote access system specifically for Komatsu equipment. It provides a web-based interface for managing T1 Legacy scripts and GRM (Global Remote Monitoring) equipment. The system aims to offer enhanced functionality and a modern user experience for remote operations.

## Technologies Used

This project is built using Python with the Flask web framework. Key dependencies include:

*   **Web Framework:** Flask
*   **CORS Support:** `flask-cors`
*   **Network & SSH:** `paramiko`, `requests`, `urllib3`, `ping3`, `scp`
*   **System Monitoring:** `psutil`
*   **HTML/XML Parsing:** `beautifulsoup4`, `lxml`
*   **Cryptography:** `cryptography`, `PyNaCl`, `bcrypt`, `cffi`, `pycparser`
*   **Build Tools (for PyInstaller):** `pyinstaller`, `pyinstaller-hooks-contrib`, `altgraph`, `pefile`, `packaging`
*   **Windows Specific:** `pywin32-ctypes`, `colorama`
*   **System Tray Support:** `pystray`, `pillow`

For a complete list of dependencies and their exact versions, refer to `requirements.txt`.

## Building and Running

### Running the Development Server

To run the Flask application in development mode:

```bash
python main.py
```

### Building the Executable

The project can be packaged into a standalone Windows executable using `BUILD_WEBSERVER.bat`.

*   **Option 9:** Builds the executable.
*   **Option 11:** Performs a full build pipeline, including deployment to a connected USB drive.

### Accessing the Application

Once running, the web dashboard can be accessed via a web browser at:

`http://localhost:8888`

The default login password is: `komatsu`

## Development Conventions

Based on the available documentation, no explicit coding style guidelines, testing practices, or contribution conventions are detailed. Adherence to Python's PEP 8 and standard Flask project structures is recommended.

## Key File Structure

*   `main.py`: The main Flask application file, defining routes and business logic.
*   `templates/`: Contains Jinja2 HTML templates for the web interface.
*   `static/`: Stores static assets like CSS, JavaScript, and images.
*   `tools/`: Houses Python utility modules used by the Flask application.
*   `autotech_client/`: Contains the installer package and associated tools for remote client PCs.
*   `requirements.txt`: Lists all Python dependencies.
*   `BUILD_WEBSERVER.bat`: Script for building and deploying the web server.

## AutoTech Client Installation (for Remote PCs)

For full functionality (e.g., VNC/SSH/SFTP tools opening on the *local* remote PC rather than the server), remote users **must** install the AutoTech Client.

### Installation Steps:

1.  Copy the `autotech_client/` folder from the USB drive to the remote PC.
2.  Run `Install_AutoTech_Client.bat` as an administrator.
3.  The installer sets up tools in `C:\AutoTech_Client\` and registers custom URI handlers (e.g., `autotech-vnc://`, `autotech-ssh://`).

This client does not require Python or external dependencies on the remote PC.
