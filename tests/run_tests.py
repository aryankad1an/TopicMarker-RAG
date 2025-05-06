#!/usr/bin/env python3
"""
Test runner for TopicMarker-RAG.
"""

import unittest
import os
import sys

# Add the parent directory to the path so we can import from the root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def run_unit_tests():
    """Run all unit tests."""
    print("Running unit tests...")
    unit_tests = unittest.TestLoader().discover('unit', pattern='test_*.py')
    unittest.TextTestRunner(verbosity=2).run(unit_tests)

def run_integration_tests():
    """Run all integration tests."""
    print("Running integration tests...")
    integration_tests = unittest.TestLoader().discover('integration', pattern='test_*.py')
    unittest.TextTestRunner(verbosity=2).run(integration_tests)

def run_api_tests():
    """Run all API tests."""
    print("Running API tests...")

    # Check if the API server is running
    import socket
    try:
        socket.create_connection(("localhost", 8000), timeout=2)
        print("API server is running. Proceeding with tests...")
    except (socket.timeout, socket.error):
        print("ERROR: API server is not running. Please start the API server first.")
        print("Run: python -m app.main")
        return

    # Run tests individually to prevent one test from affecting others
    import subprocess
    import glob
    import time

    api_test_files = glob.glob(os.path.join('api', 'test_*.py'))

    if not api_test_files:
        print("No API test files found.")
        return

    print(f"Found {len(api_test_files)} API test files.")

    for test_file in api_test_files:
        print(f"\n{'='*50}")
        print(f"Running {test_file}...")
        print(f"{'='*50}\n")

        # Run the test file as a separate process
        result = subprocess.run([sys.executable, test_file],
                               capture_output=True,
                               text=True)

        # Print the output
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)

        # Add a small delay between tests to allow resources to be released
        time.sleep(1)

def run_all_tests():
    """Run all tests."""
    print("Running all tests...")
    all_tests = unittest.TestLoader().discover('.', pattern='test_*.py')
    unittest.TextTestRunner(verbosity=2).run(all_tests)

def run_specific_api_test(test_name):
    """Run a specific API test file."""
    print(f"Running API test: {test_name}")

    # Check if the API server is running
    import socket
    try:
        socket.create_connection(("localhost", 8000), timeout=2)
        print("API server is running. Proceeding with test...")
    except (socket.timeout, socket.error):
        print("ERROR: API server is not running. Please start the API server first.")
        print("Run: python -m app.main")
        return

    # Find the test file
    import glob

    test_file = None
    for file in glob.glob(os.path.join('api', 'test_*.py')):
        if test_name in file:
            test_file = file
            break

    if not test_file:
        print(f"ERROR: No test file found matching '{test_name}'.")
        print("Available test files:")
        for file in glob.glob(os.path.join('api', 'test_*.py')):
            print(f"  - {os.path.basename(file)}")
        return

    # Run the test file
    print(f"\n{'='*50}")
    print(f"Running {test_file}...")
    print(f"{'='*50}\n")

    import subprocess
    result = subprocess.run([sys.executable, test_file],
                           capture_output=False)  # Show output in real-time

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Run tests for TopicMarker-RAG')
    parser.add_argument('--unit', action='store_true', help='Run unit tests')
    parser.add_argument('--integration', action='store_true', help='Run integration tests')
    parser.add_argument('--api', action='store_true', help='Run API tests')
    parser.add_argument('--api-test', type=str, help='Run a specific API test file (e.g., refine_routes)')
    parser.add_argument('--all', action='store_true', help='Run all tests')

    args = parser.parse_args()

    if args.unit:
        run_unit_tests()
    elif args.integration:
        run_integration_tests()
    elif args.api:
        run_api_tests()
    elif args.api_test:
        run_specific_api_test(args.api_test)
    elif args.all:
        run_all_tests()
    else:
        # Default to running all tests
        run_all_tests()
