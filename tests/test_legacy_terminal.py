"""
test_legacy_terminal.py
=======================
Pure unit tests for helpers and the TerminalSession class in
app/blueprints/legacy_terminal.py.

No network, no SSH, no subprocess — all execution paths tested here are the
offline/simulation branches.
"""

import pytest


# ---------------------------------------------------------------------------
# generate_mock_script_output()
# ---------------------------------------------------------------------------

def test_generate_mock_ip_finder():
    from app.blueprints.legacy_terminal import generate_mock_script_output
    output = generate_mock_script_output('ip-finder', 'RD111', '10.110.20.110')
    assert 'RD111' in output
    assert '10.110.20.110' in output


def test_generate_mock_ptx_health():
    from app.blueprints.legacy_terminal import generate_mock_script_output
    output = generate_mock_script_output('ptx-health', 'RD111', '10.110.20.110')
    assert 'CPU Usage' in output
    assert 'Memory Usage' in output


def test_generate_mock_avi_reboot():
    from app.blueprints.legacy_terminal import generate_mock_script_output
    output = generate_mock_script_output('avi-reboot', 'RD111', '10.110.20.110')
    assert 'eboot' in output  # 'Reboot' or 'reboot'


def test_generate_mock_component_tracking():
    from app.blueprints.legacy_terminal import generate_mock_script_output
    output = generate_mock_script_output('component-tracking', 'RD111', '10.110.20.110')
    assert 'RD111' in output


def test_generate_mock_unknown_script():
    """Unknown script names fall back to a generic 'completed' message."""
    from app.blueprints.legacy_terminal import generate_mock_script_output
    output = generate_mock_script_output('not-a-real-script', 'TEST', '10.0.0.1')
    # Default output mentions the script name and some completion indicator
    assert 'not-a-real-script' in output or 'completed' in output.lower()


def test_generate_mock_start_vnc():
    from app.blueprints.legacy_terminal import generate_mock_script_output
    output = generate_mock_script_output('start-vnc', 'TEST', '10.110.99.99')
    assert 'VNC' in output or 'vnc' in output.lower()


def test_generate_mock_watchdog():
    from app.blueprints.legacy_terminal import generate_mock_script_output
    output = generate_mock_script_output('watchdog', 'TEST', '10.110.99.99')
    assert 'TEST' in output
    assert '10.110.99.99' in output


# ---------------------------------------------------------------------------
# TerminalSession._simulate_command()
# ---------------------------------------------------------------------------

def _make_session(session_id='test-id'):
    from app.blueprints.legacy_terminal import TerminalSession
    ts = TerminalSession(session_id)
    ts.running = True
    ts.offline_mode = True
    return ts


def test_simulate_help_command():
    ts = _make_session()
    ts._simulate_command('help')
    output = ts.get_output()
    assert 'help' in output.lower()


def test_simulate_status_command():
    ts = _make_session()
    ts._simulate_command('status')
    output = ts.get_output()
    assert 'status' in output.lower() or 'mode' in output.lower()


def test_simulate_clear_command():
    ts = _make_session()
    ts._simulate_command('clear')
    output = ts.get_output()
    # ANSI clear sequence should be present
    assert '\033[2J' in output or len(output) > 0


def test_simulate_unknown_command():
    ts = _make_session()
    ts._simulate_command('some-unknown-command')
    output = ts.get_output()
    assert 'OFFLINE' in output or 'simulation' in output.lower() or 'Simulated' in output


def test_simulate_empty_command():
    ts = _make_session()
    ts._simulate_command('')
    output = ts.get_output()
    # Empty command puts a single newline
    assert output == '\n'


# ---------------------------------------------------------------------------
# TerminalSession.get_output()
# ---------------------------------------------------------------------------

def test_get_output_empty():
    ts = _make_session()
    assert ts.get_output() == ''


def test_get_output_drains_queue():
    ts = _make_session()
    ts.output_queue.put('line1')
    ts.output_queue.put('line2')
    ts.output_queue.put('line3')
    output = ts.get_output()
    assert 'line1' in output
    assert 'line2' in output
    assert 'line3' in output
    # Queue should now be empty
    assert ts.get_output() == ''


def test_get_output_join_order():
    ts = _make_session()
    ts.output_queue.put('alpha')
    ts.output_queue.put('beta')
    output = ts.get_output()
    # alpha should appear before beta
    assert output.index('alpha') < output.index('beta')


# ---------------------------------------------------------------------------
# get_equipment_ips()
# ---------------------------------------------------------------------------

def test_get_equipment_ips_found(tmp_path, monkeypatch):
    import app.blueprints.legacy_terminal as lt
    from app.blueprints.legacy_terminal import get_equipment_ips

    # Create IP_list.dat at tmp_path (second candidate path)
    ip_list = tmp_path / 'IP_list.dat'
    ip_list.write_text("# header\nAHG135 10.110.21.87 10.111.20.87\n")

    # Point BASE_DIR / TOOLS_DIR to tmp_path so paths resolve here
    monkeypatch.setattr(lt, 'BASE_DIR', str(tmp_path))
    monkeypatch.setattr(lt, 'TOOLS_DIR', str(tmp_path))

    ptx_ip, avi_ip = get_equipment_ips('AHG135')
    assert ptx_ip == '10.110.21.87'
    assert avi_ip == '10.111.20.87'


def test_get_equipment_ips_case_insensitive(tmp_path, monkeypatch):
    import app.blueprints.legacy_terminal as lt
    from app.blueprints.legacy_terminal import get_equipment_ips

    ip_list = tmp_path / 'IP_list.dat'
    ip_list.write_text("# header\nAHG135 10.110.21.87 10.111.20.87\n")
    monkeypatch.setattr(lt, 'BASE_DIR', str(tmp_path))
    monkeypatch.setattr(lt, 'TOOLS_DIR', str(tmp_path))

    # Lookup with lowercase should still find it
    ptx_ip, avi_ip = get_equipment_ips('ahg135')
    assert ptx_ip == '10.110.21.87'


def test_get_equipment_ips_not_found(tmp_path, monkeypatch):
    import app.blueprints.legacy_terminal as lt
    from app.blueprints.legacy_terminal import get_equipment_ips

    ip_list = tmp_path / 'IP_list.dat'
    ip_list.write_text("# header\nAHG135 10.110.21.87 10.111.20.87\n")
    monkeypatch.setattr(lt, 'BASE_DIR', str(tmp_path))
    monkeypatch.setattr(lt, 'TOOLS_DIR', str(tmp_path))

    ptx_ip, avi_ip = get_equipment_ips('NONEXISTENT')
    assert ptx_ip is None
    assert avi_ip is None


def test_get_equipment_ips_missing_file(tmp_path, monkeypatch):
    """When no IP_list.dat file exists, returns (None, None) gracefully."""
    import app.blueprints.legacy_terminal as lt
    from app.blueprints.legacy_terminal import get_equipment_ips

    # Point to empty tmp dir (no dat file)
    monkeypatch.setattr(lt, 'BASE_DIR', str(tmp_path))
    monkeypatch.setattr(lt, 'TOOLS_DIR', str(tmp_path))

    ptx_ip, avi_ip = get_equipment_ips('AHG135')
    assert ptx_ip is None
    assert avi_ip is None


# ---------------------------------------------------------------------------
# TerminalSession.start() — offline (no bat file)
# ---------------------------------------------------------------------------

def test_terminal_session_offline_mode(mocker):
    """When T1_Tools.bat is not found anywhere, start() enters simulation mode."""
    from app.blueprints.legacy_terminal import TerminalSession

    # Ensure no bat file is "found"
    mocker.patch('os.path.exists', return_value=False)

    ts = TerminalSession('test-uuid')
    success, message = ts.start()

    assert success is True
    assert ts.offline_mode is True
    assert 'simulation' in message.lower()


def test_terminal_session_simulation_queues_message(mocker):
    """Simulation mode immediately queues an introductory message."""
    from app.blueprints.legacy_terminal import TerminalSession

    mocker.patch('os.path.exists', return_value=False)

    ts = TerminalSession('test-uuid-2')
    ts.start()

    output = ts.get_output()
    assert len(output) > 0  # Something was queued
    assert 'SIMULATION' in output or 'simulation' in output.lower()
