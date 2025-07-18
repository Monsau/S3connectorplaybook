#!/usr/bin/env python3
"""
Simple test script to verify the S3 Connector installation.
"""

import sys
import os

# Add src to path for development
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Test basic imports."""
    print("🧪 Testing basic imports...")
    
    try:
        import boto3
        print("  ✅ boto3 imported successfully")
    except ImportError as e:
        print(f"  ❌ boto3 import failed: {e}")
        return False
    
    try:
        import pandas as pd
        print("  ✅ pandas imported successfully")
    except ImportError as e:
        print(f"  ❌ pandas import failed: {e}")
        return False
    
    try:
        import pyarrow
        print("  ✅ pyarrow imported successfully")
    except ImportError as e:
        print(f"  ❌ pyarrow import failed: {e}")
        return False
    
    try:
        import om_s3_connector
        print("  ✅ om_s3_connector imported successfully")
    except ImportError as e:
        print(f"  ❌ om_s3_connector import failed: {e}")
        return False
    
    return True

def test_connector_classes():
    """Test importing connector classes."""
    print("🔧 Testing connector classes...")
    
    try:
        from om_s3_connector.core import S3Connector, S3ConnectorConfig, S3SecurityManager
        print("  ✅ Core classes imported successfully")
    except ImportError as e:
        print(f"  ❌ Core classes import failed: {e}")
        return False
    
    try:
        from om_s3_connector.parsers import ParserFactory
        print("  ✅ ParserFactory imported successfully")
    except ImportError as e:
        print(f"  ❌ ParserFactory import failed: {e}")
        return False
    
    return True

def test_basic_functionality():
    """Test basic functionality."""
    print("⚙️  Testing basic functionality...")
    
    try:
        from om_s3_connector.core import S3ConnectorConfig, S3ConnectionConfig, S3SecurityConfig
        
        # Test config creation with proper structure
        security_config = S3SecurityConfig(
            awsAccessKeyId="test_key",
            awsSecretAccessKey="test_secret"
        )
        
        connection_config = S3ConnectionConfig(
            bucketName="test-bucket",
            awsRegion="us-east-1",
            securityConfig=security_config
        )
        
        config = S3ConnectorConfig(
            connection=connection_config
        )
        
        print("  ✅ S3ConnectorConfig created successfully")
        print(f"  ✅ Bucket name: {config.connection.bucketName}")
        print(f"  ✅ Region: {config.connection.awsRegion}")
        return True
    except Exception as e:
        print(f"  ❌ Basic functionality test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Starting S3 Connector Installation Tests")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_connector_classes,
        test_basic_functionality
    ]
    
    results = []
    for test in tests:
        result = test()
        results.append(result)
        print()
    
    # Summary
    print("📊 Test Summary")
    print("-" * 20)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"🎉 All tests passed! ({passed}/{total})")
        print("✅ S3 Connector is properly installed and ready to use.")
        return 0
    else:
        print(f"⚠️  Some tests failed: {passed}/{total} passed")
        print("❌ Please check the errors above and fix any issues.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
