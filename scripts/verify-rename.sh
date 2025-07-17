#!/bin/bash

echo "🔍 Verifying Project Rename and Restructure..."
echo

# Set Python path
export PYTHONPATH=$(pwd)/src

echo "📦 Testing package import..."
python3 -c "
try:
    from om_s3_connector import S3Source, S3ConnectorConfig, get_parser
    print('✅ SUCCESS: All main components import correctly')
    print('   - S3Source: OK')
    print('   - S3ConnectorConfig: OK') 
    print('   - get_parser: OK')
except ImportError as e:
    print('❌ FAILED: Import error -', str(e))
    exit(1)
"

echo
echo "🔧 Checking configuration files..."

# Check ingestion.yaml
if grep -q "om_s3_connector.core.s3_connector.S3Source" config/ingestion.yaml; then
    echo "✅ config/ingestion.yaml - Updated correctly"
else
    echo "❌ config/ingestion.yaml - Still has old references"
fi

# Check enhanced examples
if grep -q "om_s3_connector.core.s3_connector.S3Source" config/enhanced_ingestion_examples.yaml; then
    echo "✅ config/enhanced_ingestion_examples.yaml - Updated correctly"
else
    echo "❌ config/enhanced_ingestion_examples.yaml - Still has old references"
fi

echo
echo "📁 Verifying directory structure..."
if [ -d "src/om_s3_connector" ]; then
    echo "✅ src/om_s3_connector/ - Directory exists"
else
    echo "❌ src/om_s3_connector/ - Directory missing"
fi

if [ -d "src/om_s3_connector/core" ]; then
    echo "✅ src/om_s3_connector/core/ - Core module exists"
else
    echo "❌ src/om_s3_connector/core/ - Core module missing"
fi

if [ -d "src/om_s3_connector/parsers" ]; then
    echo "✅ src/om_s3_connector/parsers/ - Parsers module exists"
else
    echo "❌ src/om_s3_connector/parsers/ - Parsers module missing"
fi

echo
echo "🎯 Rename and restructure verification complete!"
