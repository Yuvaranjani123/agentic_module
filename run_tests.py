#!/usr/bin/env python
"""
Test runner script for the RAG Module.

This script provides convenient shortcuts for running different types of tests.

Usage:
    python run_tests.py                    # Run all tests
    python run_tests.py agents             # Run agents tests only (Traditional + ReAct)
    python run_tests.py ingestion          # Run ingestion tests only
    python run_tests.py retriever          # Run retriever tests only
    python run_tests.py --verbose          # Run with verbose output
    python run_tests.py --coverage         # Run with coverage report
    python run_tests.py --fast             # Run only fast unit tests
"""

import sys
import os
import subprocess
from pathlib import Path

# Add backend to path
BASE_DIR = Path(__file__).resolve().parent
BACKEND_DIR = BASE_DIR / 'backend'
sys.path.insert(0, str(BACKEND_DIR))

# Color codes for terminal output
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RED = '\033[91m'
RESET = '\033[0m'
BOLD = '\033[1m'


def print_header(text):
    """Print a formatted header."""
    print(f"\n{BOLD}{BLUE}{'=' * 60}{RESET}")
    print(f"{BOLD}{BLUE}{text:^60}{RESET}")
    print(f"{BOLD}{BLUE}{'=' * 60}{RESET}\n")


def print_success(text):
    """Print success message."""
    print(f"{GREEN}✅ {text}{RESET}")


def print_warning(text):
    """Print warning message."""
    print(f"{YELLOW}⚠️  {text}{RESET}")


def print_error(text):
    """Print error message."""
    print(f"{RED}❌ {text}{RESET}")


def run_command(cmd, description):
    """Run a command and return the result."""
    print(f"\n{BOLD}Running: {description}{RESET}")
    print(f"Command: {' '.join(cmd)}\n")
    
    result = subprocess.run(cmd, cwd=BACKEND_DIR)
    return result.returncode


def main():
    """Main test runner."""
    args = sys.argv[1:]
    
    print_header("RAG Module Test Runner")
    
    # Base command
    base_cmd = [sys.executable, 'manage.py', 'test']
    
    # Parse arguments
    verbose = '--verbose' in args or '-v' in args
    coverage = '--coverage' in args
    fast = '--fast' in args
    
    # Remove flags from args
    test_args = [arg for arg in args if not arg.startswith('--') and not arg.startswith('-')]
    
    # Build test command
    if not test_args:
        # Run all tests
        cmd = base_cmd
        description = "All Tests"
    elif test_args[0] in ['agents', 'ingestion', 'retriever', 'evaluation', 'logs']:
        # Run specific app tests
        cmd = base_cmd + [test_args[0]]
        description = f"{test_args[0].capitalize()} Tests"
    else:
        # Run specific test class or method
        cmd = base_cmd + test_args
        description = f"Specific Test: {' '.join(test_args)}"
    
    # Add verbosity
    if verbose:
        cmd.append('--verbosity=2')
    else:
        cmd.append('--verbosity=1')
    
    # Add keepdb for faster reruns
    cmd.append('--keepdb')
    
    # Run coverage if requested
    if coverage:
        print_warning("Coverage reporting requires 'coverage' package")
        print("Install with: pip install coverage")
        coverage_cmd = ['coverage', 'run', '--source=.'] + cmd[1:]
        returncode = run_command(coverage_cmd, f"{description} (with coverage)")
        
        if returncode == 0:
            print("\n" + "=" * 60)
            subprocess.run(['coverage', 'report'], cwd=BACKEND_DIR)
            print("\n" + "=" * 60)
            print(f"\n{BOLD}For detailed HTML report, run:{RESET}")
            print(f"  cd backend && coverage html && start htmlcov/index.html")
    else:
        returncode = run_command(cmd, description)
    
    # Print summary
    print("\n" + "=" * 60)
    if returncode == 0:
        print_success("All tests passed!")
    else:
        print_error("Some tests failed!")
    print("=" * 60 + "\n")
    
    # Print useful tips
    if returncode != 0:
        print(f"{BOLD}Debugging Tips:{RESET}")
        print("  1. Run with --verbose for more details")
        print("  2. Run specific test: python run_tests.py agents.tests.ReActAgenticTests.test_react_multi_step_query")
        print("  3. Run specific module: python run_tests.py agents")
        print("  4. Check the error messages above for clues")
        print("  5. Ensure all environment variables are set (check .env file)")
        print()
    
    return returncode


if __name__ == '__main__':
    sys.exit(main())
