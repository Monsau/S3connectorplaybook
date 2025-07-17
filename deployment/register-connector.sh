#!/bin/bash
# OpenMetadata S3 Connector Registration Script

echo "🔌 Registering S3 Connector with OpenMetadata..."

# 1. Copy connector to ingestion container
echo "Deploying to ingestion container..."
sudo docker cp dist/openmetadata_s3_connector-0.9-py3-none-any.whl openmetadata_ingestion:/tmp/

# 2. Install in ingestion environment
echo "Installing in ingestion environment..."
sudo docker exec openmetadata_ingestion bash -c "
    pip install /tmp/openmetadata_s3_connector-0.9-py3-none-any.whl --user
    python -c 'import om_s3_connector; print(\"✅ S3 Connector installed:\", om_s3_connector.__version__)'
"

# 3. Create connector registration
echo "Creating connector registration..."
sudo docker exec openmetadata_ingestion bash -c "
    mkdir -p /opt/airflow/custom_connectors
    cat > /opt/airflow/custom_connectors/s3_connector.py << 'EOF'
from metadata.ingestion.api.source import Source
from om_s3_connector.core.s3_connector import S3Source

class CustomS3Source(S3Source, Source):
    '''Custom S3 connector implementation'''
    pass

# Register the connector
def register_s3_connector():
    from metadata.ingestion.source.source_registry import SourceRegistry
    SourceRegistry.register('s3-custom', CustomS3Source)
    return True

if __name__ == '__main__':
    register_s3_connector()
    print('✅ S3 Connector registered successfully')
EOF
"

# 4. Test registration
echo "Testing connector registration..."
sudo docker exec openmetadata_ingestion bash -c "
    cd /opt/airflow/custom_connectors
    python s3_connector.py
"

echo "✅ S3 Connector registration completed!"
echo ""
echo "📝 Next steps:"
echo "1. Use the manual ingestion workflow: config/manual-s3-ingestion.yaml"
echo "2. Or register via REST API using the connector service"
echo "3. For full UI integration, follow Option 2 (proper integration)"
