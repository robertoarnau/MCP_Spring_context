#!/usr/bin/env python3
"""
Script to run unit tests for the MCP Server system.
This script provides a convenient way to run tests and verify system functionality.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle the result."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False

def main():
    """Main function to run tests."""
    print("MCP Server Test Runner")
    print("Testing system functionality before making new implementations")
    
    # Check if we're in the right directory
    if not Path("mcp_server").exists():
        print("Error: Please run this script from the project root directory")
        sys.exit(1)
    
    tests_run = 0
    tests_passed = 0
    
    # Test 1: Import test
    if run_command([
        "docker-compose", "run", "--rm", "cline-mcp-server", 
        "python", "-c", 
        "from mcp_server.main import CLineMCPServer; print('✓ Import successful')"
    ], "Import Test"):
        tests_passed += 1
    tests_run += 1
    
    # Test 2: Main server tests
    if run_command([
        "docker-compose", "run", "--rm", "cline-mcp-server", 
        "python", "-m", "pytest", "tests/test_main.py", "-v", "--tb=short"
    ], "Main Server Tests"):
        tests_passed += 1
    tests_run += 1
    
    # Test 3: Core functionality tests
    if run_command([
        "docker-compose", "run", "--rm", "cline-mcp-server", 
        "python", "-m", "pytest", 
        "tests/test_code_analyzer.py::TestCodeAnalyzer::test_analyze_file_structure_java",
        "tests/test_file_manager.py::TestFileManager::test_read_file_text",
        "tests/test_documentation.py::TestDocumentation::test_extract_comments",
        "-v", "--tb=short"
    ], "Core Functionality Tests"):
        tests_passed += 1
    tests_run += 1
    
    # Summary
    print(f"\n{'='*60}")
    print("Test Summary")
    print(f"{'='*60}")
    print(f"Tests run: {tests_run}")
    print(f"Tests passed: {tests_passed}")
    print(f"Tests failed: {tests_run - tests_passed}")
    
    if tests_passed == tests_run:
        print("\n🎉 All tests passed! System is ready for new implementations.")
        print("✅ The MCP Server system is functioning correctly.")
    else:
        print(f"\n⚠️  {tests_run - tests_passed} test(s) failed.")
        print("❌ Please fix the issues before proceeding with new implementations.")
        sys.exit(1)

if __name__ == "__main__":
    main()
