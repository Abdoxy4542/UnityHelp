#!/usr/bin/env python3
"""
Test runner for UnityAid MCP servers
"""

import sys
import os
import pytest
from pathlib import Path

# Add the Django project to the path
BASE_DIR = Path(__file__).resolve().parent
DJANGO_DIR = BASE_DIR.parent
sys.path.append(str(DJANGO_DIR))

def setup_test_environment():
    """Set up the test environment"""
    # Set environment variables for testing
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
    os.environ.setdefault('TESTING', 'True')

    # Initialize Django
    try:
        import django
        django.setup()
        print("Django test environment initialized successfully")
        return True
    except Exception as e:
        print(f"Failed to initialize Django test environment: {e}")
        return False

def run_all_tests():
    """Run all tests"""
    test_args = [
        'tests/',
        '-v',
        '--tb=short',
        '--maxfail=5'
    ]

    print("Running UnityAid MCP Server tests...")
    return pytest.main(test_args)

def run_specific_test(test_file):
    """Run a specific test file"""
    if not test_file.startswith('tests/'):
        test_file = f'tests/{test_file}'

    if not test_file.endswith('.py'):
        test_file = f'{test_file}.py'

    test_args = [test_file, '-v', '--tb=short']
    return pytest.main(test_args)

def main():
    """Main test runner function"""
    print("UnityAid MCP Server Test Runner")
    print("=" * 50)

    # Setup test environment
    if not setup_test_environment():
        sys.exit(1)

    # Check command line arguments
    if len(sys.argv) > 1:
        test_target = sys.argv[1]

        if test_target == '--help':
            print_help()
            return
        elif test_target == '--list':
            list_tests()
            return
        else:
            # Run specific test
            exit_code = run_specific_test(test_target)
    else:
        # Run all tests
        exit_code = run_all_tests()

    if exit_code == 0:
        print("\n✅ All tests passed!")
    else:
        print(f"\n❌ Tests failed (exit code: {exit_code})")

    sys.exit(exit_code)

def print_help():
    """Print help message"""
    print("""
Usage: python run_tests.py [OPTIONS] [TEST_TARGET]

Options:
    --help      Show this help message
    --list      List available test files

Test Targets:
    (none)      Run all tests
    test_base   Run base functionality tests
    test_sites_server  Run sites server tests
    test_integration   Run integration tests

Examples:
    python run_tests.py                    # Run all tests
    python run_tests.py test_base          # Run base tests only
    python run_tests.py tests/test_sites_server.py  # Run specific file
    """)

def list_tests():
    """List available test files"""
    test_dir = BASE_DIR / 'tests'
    test_files = []

    if test_dir.exists():
        for file in test_dir.glob('test_*.py'):
            test_files.append(file.name)

    print("Available test files:")
    for test_file in sorted(test_files):
        print(f"  - {test_file}")

    if not test_files:
        print("  No test files found")

if __name__ == "__main__":
    main()