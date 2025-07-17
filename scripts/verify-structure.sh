#!/bin/bash
# Post-restructure verification script

echo "🔍 S3 Connector Structure Verification"
echo "======================================"

# Check if old structure is removed
if [ -d "connectors" ]; then
    echo "❌ Old 'connectors' directory still exists"
    exit 1
else
    echo "✅ Old 'connectors' directory removed"
fi

if [ -d "playbooks" ]; then
    echo "❌ Old 'playbooks' directory still exists"
    exit 1
else
    echo "✅ Old 'playbooks' directory removed"
fi

# Check new structure
echo -e "\n📁 Verifying new structure..."

if [ -d "src/s3_connector" ]; then
    echo "✅ New source structure exists"
else
    echo "❌ New source structure missing"
    exit 1
fi

if [ -d "config" ]; then
    echo "✅ Config directory exists"
else
    echo "❌ Config directory missing"
    exit 1
fi

if [ -d "tests" ]; then
    echo "✅ Tests directory exists"
else
    echo "❌ Tests directory missing"
    exit 1
fi

# Check key files
echo -e "\n📄 Verifying key files..."

key_files=(
    "src/s3_connector/__init__.py"
    "src/s3_connector/core/s3_connector.py"
    "src/s3_connector/parsers/factory.py"
    "config/ingestion.yaml"
    "setup.py"
    "README.md"
)

for file in "${key_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file exists"
    else
        echo "❌ $file missing"
        exit 1
    fi
done

# Check for duplicates
echo -e "\n🔍 Checking for duplicate files..."

# Test files that should be moved
old_test_files=("simple_test.py" "test_parsers.py" "validate_parsers.py")
duplicates_found=false

for file in "${old_test_files[@]}"; do
    if [ -f "$file" ]; then
        echo "⚠️  Duplicate test file in root: $file"
        duplicates_found=true
    fi
done

if [ "$duplicates_found" = false ]; then
    echo "✅ No duplicate test files found in root"
fi

# Verify PYTHONPATH setup
echo -e "\n🐍 Testing Python imports..."

export PYTHONPATH="$(pwd)/src"

python -c "
try:
    from s3_connector.core.s3_connector import S3Source
    print('✅ S3Source import successful')
except Exception as e:
    print(f'❌ S3Source import failed: {e}')
    exit(1)

try:
    from s3_connector.parsers.factory import ParserFactory
    print('✅ ParserFactory import successful')
except Exception as e:
    print(f'❌ ParserFactory import failed: {e}')
    exit(1)
"

if [ $? -eq 0 ]; then
    echo "✅ All imports working correctly"
else
    echo "❌ Import tests failed"
    exit 1
fi

echo -e "\n🎉 Structure verification completed successfully!"
echo "📖 Usage:"
echo "   export PYTHONPATH=\$(pwd)/src"
echo "   metadata ingest -c config/ingestion.yaml"
