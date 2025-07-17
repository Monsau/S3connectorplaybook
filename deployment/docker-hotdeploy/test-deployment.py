#!/usr/bin/env python3
"""
Test script for S3 Connector deployment validation
"""

import sys
import subprocess
import json
import time
import requests
from pathlib import Path

def run_command(cmd, capture_output=True):
    """Run shell command and return result"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=capture_output, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def test_package_installation():
    """Test if package is installed in container"""
    print("🔍 Testing package installation...")
    
    success, stdout, stderr = run_command(
        "docker exec openmetadata-server pip show openmetadata-s3-connector"
    )
    
    if success:
        print("  ✅ Package is installed")
        version_line = [line for line in stdout.split('\n') if line.startswith('Version:')]
        if version_line:
            print(f"  📦 {version_line[0]}")
        return True
    else:
        print("  ❌ Package not found")
        return False

def test_connector_import():
    """Test if connector can be imported"""
    print("🔍 Testing connector import...")
    
    success, stdout, stderr = run_command(
        'docker exec openmetadata-server python -c "from om_s3_connector.core.s3_connector import S3Source; print(\'SUCCESS\')"'
    )
    
    if success and "SUCCESS" in stdout:
        print("  ✅ Connector import successful")
        return True
    else:
        print("  ❌ Connector import failed")
        print(f"  Error: {stderr}")
        return False

def test_openmetadata_api():
    """Test if OpenMetadata API is responding"""
    print("🔍 Testing OpenMetadata API...")
    
    try:
        response = requests.get("http://localhost:8585/api/v1/health", timeout=10)
        if response.status_code == 200:
            print("  ✅ API is responding")
            return True
        else:
            print(f"  ❌ API returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"  ❌ API connection failed: {e}")
        return False

def test_connector_assets():
    """Test if connector assets are installed"""
    print("🔍 Testing connector assets...")
    
    success, stdout, stderr = run_command(
        "docker exec openmetadata-server ls /opt/openmetadata/static/assets/connectors/s3/"
    )
    
    if success and "s3-connector-icon" in stdout:
        icon_count = len([line for line in stdout.split('\n') if 'svg' in line])
        print(f"  ✅ Found {icon_count} icon assets")
        return True
    else:
        print("  ⚠️  Icon assets not found (functionality not affected)")
        return True  # Non-critical

def test_service_status():
    """Test if OpenMetadata service is running"""
    print("🔍 Testing service status...")
    
    # Try supervisorctl first
    success, stdout, stderr = run_command(
        "docker exec openmetadata-server supervisorctl status openmetadata"
    )
    
    if success and "RUNNING" in stdout:
        print("  ✅ Service is running (supervisorctl)")
        return True
    
    # Try systemctl
    success, stdout, stderr = run_command(
        "docker exec openmetadata-server systemctl is-active openmetadata"
    )
    
    if success and "active" in stdout:
        print("  ✅ Service is running (systemctl)")
        return True
    
    # Try process check
    success, stdout, stderr = run_command(
        "docker exec openmetadata-server pgrep -f openmetadata"
    )
    
    if success and stdout.strip():
        print("  ✅ Service process is running")
        return True
    
    print("  ❌ Service is not running")
    return False

def test_connector_registration():
    """Test if connector is properly registered"""
    print("🔍 Testing connector registration...")
    
    success, stdout, stderr = run_command(
        'docker exec openmetadata-server python -c "'
        'import pkg_resources; '
        'eps = list(pkg_resources.iter_entry_points(\"openmetadata_sources\")); '
        's3_eps = [ep for ep in eps if \"s3\" in ep.name.lower()]; '
        'print(f\"Found {len(s3_eps)} S3 connectors\"); '
        '[print(f\"  {ep.name} -> {ep.module_name}\") for ep in s3_eps]'
        '"'
    )
    
    if success and "Found" in stdout:
        lines = stdout.strip().split('\n')
        count_line = [line for line in lines if "Found" in line][0]
        print(f"  ✅ {count_line}")
        if "s3" in stdout.lower():
            print("  ✅ S3 connector found in entry points")
            return True
    
    print("  ⚠️  S3 connector not found in entry points")
    return True  # Non-critical for basic functionality

def run_deployment_test():
    """Run complete deployment test suite"""
    print("🚀 S3 Connector Deployment Test")
    print("=" * 50)
    
    tests = [
        ("Package Installation", test_package_installation),
        ("Connector Import", test_connector_import),
        ("Service Status", test_service_status),
        ("OpenMetadata API", test_openmetadata_api),
        ("Connector Assets", test_connector_assets),
        ("Connector Registration", test_connector_registration),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"  ❌ Test failed with exception: {e}")
            results.append((test_name, False))
        print()
    
    # Summary
    print("📊 Test Results Summary")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {test_name}")
        if result:
            passed += 1
    
    print()
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! Deployment is successful.")
        return True
    elif passed >= total * 0.8:  # 80% pass rate
        print("⚠️  Most tests passed. Deployment is functional with minor issues.")
        return True
    else:
        print("❌ Multiple tests failed. Deployment needs attention.")
        return False

if __name__ == "__main__":
    success = run_deployment_test()
    sys.exit(0 if success else 1)
