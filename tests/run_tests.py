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

def run_all_tests():
    """Run all tests."""
    print("Running all tests...")
    all_tests = unittest.TestLoader().discover('.', pattern='test_*.py')
    unittest.TextTestRunner(verbosity=2).run(all_tests)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Run tests for TopicMarker-RAG')
    parser.add_argument('--unit', action='store_true', help='Run unit tests')
    parser.add_argument('--integration', action='store_true', help='Run integration tests')
    parser.add_argument('--all', action='store_true', help='Run all tests')
    
    args = parser.parse_args()
    
    if args.unit:
        run_unit_tests()
    elif args.integration:
        run_integration_tests()
    elif args.all:
        run_all_tests()
    else:
        # Default to running all tests
        run_all_tests()
