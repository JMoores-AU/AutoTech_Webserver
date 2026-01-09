#!/usr/bin/env python3
"""
CHECK_MAIN.PY - Verify main.py has all critical components

Usage:
    python check_main.py main.py
    python check_main.py main_COMPLETE_WITH_ROUTES.py
"""
import sys

def check_file(filepath):
    """Verify main.py has all critical components"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"❌ ERROR: File not found: {filepath}")
        return 1
    
    checks = {
        'Critical Imports': {
            'from typing import Optional': 'Type hints import (for Pylance)',
            'import uuid': 'UUID import (for terminal sessions)',
            'import queue': 'Queue import (for terminal output)',
            'import threading': 'Threading import (for terminal)',
        },
        'Terminal Session System': {
            'terminal_sessions = {}': 'Terminal sessions dictionary',
            'class TerminalSession:': 'TerminalSession class',
            'def start(self': 'TerminalSession.start method',
            'def _read_output(self': 'TerminalSession._read_output method',
            'def send_command(self': 'TerminalSession.send_command method',
            'def get_output(self': 'TerminalSession.get_output method',
            'def is_running(self': 'TerminalSession.is_running method',
            'def stop(self': 'TerminalSession.stop method',
        },
        'Flask Routes': {
            "@app.route('/legacy')": '/legacy route (main page)',
            "@app.route('/api/legacy/terminal/start'": 'Terminal start API',
            "@app.route('/api/legacy/terminal/command'": 'Terminal command API',
            "@app.route('/api/legacy/terminal/output'": 'Terminal output API',
            "@app.route('/api/legacy/terminal/stop'": 'Terminal stop API',
            "@app.route('/api/legacy/equipment-list'": 'Equipment list API',
            "@app.route('/api/legacy/execute'": 'Execute commands API',
        },
        'Route Functions': {
            'def legacy_tools()': 'legacy_tools function',
            'def api_legacy_terminal_start()': 'api_legacy_terminal_start function',
            'def api_legacy_terminal_command()': 'api_legacy_terminal_command function',
            'def api_legacy_terminal_output()': 'api_legacy_terminal_output function',
            'def api_legacy_terminal_stop()': 'api_legacy_terminal_stop function',
            'def api_legacy_equipment_list()': 'api_legacy_equipment_list function',
            'def api_legacy_execute()': 'api_legacy_execute function',
            'def get_equipment_ips(': 'get_equipment_ips helper function',
        },
        'Decorators': {
            '@login_required': 'Login required decorator (should appear multiple times)',
        }
    }
    
    all_passed = True
    total_checks = 0
    passed_checks = 0
    failed_checks = 0
    duplicate_checks = 0
    
    print(f"\n{'='*70}")
    print(f"CHECKING: {filepath}")
    print('='*70)
    
    for category, items in checks.items():
        print(f"\n{category}")
        print('-'*70)
        
        for search_str, description in items.items():
            total_checks += 1
            count = content.count(search_str)
            
            # Special case: @login_required should appear many times
            if search_str == '@login_required':
                if count >= 5:
                    print(f"✅ OK ({count}x): {description}")
                    passed_checks += 1
                else:
                    print(f"⚠️  WARNING ({count}x): {description} (expected 5+)")
                    failed_checks += 1
                    all_passed = False
            # Everything else should appear exactly once
            elif count == 0:
                print(f"❌ MISSING: {description}")
                print(f"   Search for: '{search_str}'")
                failed_checks += 1
                all_passed = False
            elif count > 1:
                print(f"⚠️  DUPLICATE ({count}x): {description}")
                print(f"   Search for: '{search_str}'")
                duplicate_checks += 1
                all_passed = False
            else:
                print(f"✅ OK: {description}")
                passed_checks += 1
    
    # Summary
    print(f"\n{'='*70}")
    print(f"SUMMARY")
    print('='*70)
    print(f"Total Checks:  {total_checks}")
    print(f"✅ Passed:     {passed_checks}")
    print(f"❌ Failed:     {failed_checks}")
    print(f"⚠️  Duplicates: {duplicate_checks}")
    
    print(f"\n{'='*70}")
    if all_passed:
        print("✅ ALL CHECKS PASSED - FILE IS GOOD!")
        print('='*70)
        return 0
    else:
        print("❌ SOME CHECKS FAILED - FILE HAS ISSUES!")
        print('='*70)
        print("\nACTIONS:")
        if failed_checks > 0:
            print("  • Fix missing components before using this file")
        if duplicate_checks > 0:
            print("  • Remove duplicate code")
        print("  • Use git diff to see what changed")
        print("  • Compare with last working version")
        return 1

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python check_main.py <filepath>")
        print("Example: python check_main.py main.py")
        sys.exit(1)
    
    filepath = sys.argv[1]
    sys.exit(check_file(filepath))
