#!/bin/bash
# S3 Connector Manual Ingestion Runner
# This script runs the S3 connector outside the web interface

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Configuration
CONFIG_FILE="${1:-config/manual-s3-ingestion.yaml}"
CONTAINER="${2:-openmetadata_ingestion}"

echo "🚀 S3 Connector Manual Ingestion"
echo "================================="
echo "Config file: $CONFIG_FILE"
echo "Container: $CONTAINER"
echo ""

# Validate config file exists
if [[ ! -f "$CONFIG_FILE" ]]; then
    print_error "Configuration file not found: $CONFIG_FILE"
    exit 1
fi

# Copy config to container
print_status "Copying configuration to container..."
sudo docker cp "$CONFIG_FILE" "$CONTAINER:/tmp/s3-ingestion.yaml"

# Copy our connector to the container if not already there
print_status "Ensuring connector is available..."
if [[ -f "dist/openmetadata_s3_connector-0.9-py3-none-any.whl" ]]; then
    sudo docker cp "dist/openmetadata_s3_connector-0.9-py3-none-any.whl" "$CONTAINER:/tmp/"
fi

# Create a simplified connector runner
print_status "Creating ingestion runner..."
sudo docker exec "$CONTAINER" bash -c "cat > /tmp/run_s3_ingestion.py << 'EOF'
#!/usr/bin/env python3
import sys
import yaml
import boto3
import pandas as pd
from pathlib import Path
import json
import os

def validate_s3_connection(config):
    '''Validate S3 connection with provided credentials'''
    try:
        session = boto3.Session(
            aws_access_key_id=config.get('awsAccessKeyId'),
            aws_secret_access_key=config.get('awsSecretAccessKey'),
            region_name=config.get('awsRegion', 'us-east-1')
        )
        
        client_kwargs = {}
        if config.get('endPointURL'):
            client_kwargs['endpoint_url'] = config['endPointURL']
        if 'verifySSL' in config:
            client_kwargs['verify'] = config['verifySSL']
            
        s3_client = session.client('s3', **client_kwargs)
        
        # Test connection
        s3_client.list_buckets()
        print('✅ S3 connection successful')
        return s3_client
        
    except Exception as e:
        print(f'❌ S3 connection failed: {e}')
        return None

def discover_files(s3_client, bucket_name, patterns):
    '''Discover files in S3 bucket matching patterns'''
    try:
        print(f'🔍 Discovering files in bucket: {bucket_name}')
        
        response = s3_client.list_objects_v2(Bucket=bucket_name)
        if 'Contents' not in response:
            print('No objects found in bucket')
            return []
            
        files = []
        for obj in response['Contents']:
            key = obj['Key']
            size = obj['Size']
            modified = obj['LastModified']
            
            # Check if file matches include patterns
            import re
            for pattern in patterns.get('includes', ['.*']):
                if re.match(pattern, key):
                    files.append({
                        'key': key,
                        'size': size,
                        'last_modified': modified.isoformat(),
                        'bucket': bucket_name,
                        'format': key.split('.')[-1].lower() if '.' in key else 'unknown'
                    })
                    break
                    
        print(f'📁 Found {len(files)} files')
        return files
        
    except Exception as e:
        print(f'❌ File discovery failed: {e}')
        return []

def generate_metadata(files, service_name):
    '''Generate metadata from discovered files'''
    print('📊 Generating metadata...')
    
    # Group files by format
    formats = {}
    for file in files:
        fmt = file['format']
        if fmt not in formats:
            formats[fmt] = []
        formats[fmt].append(file)
    
    metadata = {
        'service': {
            'name': service_name,
            'type': 'S3',
            'description': f'S3 storage service with {len(files)} files'
        },
        'tables': []
    }
    
    # Create table metadata for each format group
    for fmt, fmt_files in formats.items():
        table = {
            'name': f's3_{fmt}_files',
            'displayName': f'S3 {fmt.upper()} Files',
            'description': f'Collection of {len(fmt_files)} {fmt} files from S3',
            'tableType': 'External',
            'columns': [
                {
                    'name': 'file_path',
                    'dataType': 'VARCHAR',
                    'description': 'S3 object key/path'
                },
                {
                    'name': 'file_size',
                    'dataType': 'BIGINT', 
                    'description': 'File size in bytes'
                },
                {
                    'name': 'last_modified',
                    'dataType': 'TIMESTAMP',
                    'description': 'Last modification time'
                }
            ],
            'files': fmt_files
        }
        metadata['tables'].append(table)
    
    return metadata

def run_ingestion():
    '''Main ingestion function'''
    print('🔄 Starting S3 metadata ingestion...')
    
    # Load configuration
    with open('/tmp/s3-ingestion.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    source_config = config['source']['serviceConnection']['config']
    source_filters = config['source']['sourceConfig']['config']
    service_name = config['source']['serviceName']
    
    print(f'Service: {service_name}')
    print(f'Bucket: {source_config.get("bucketName", "Not specified")}')
    
    # Validate S3 connection
    s3_client = validate_s3_connection(source_config)
    if not s3_client:
        return False
    
    # Discover files
    files = discover_files(
        s3_client, 
        source_config['bucketName'],
        source_filters.get('tableFilterPattern', {})
    )
    
    if not files:
        print('No files found matching criteria')
        return False
    
    # Generate metadata
    metadata = generate_metadata(files, service_name)
    
    # Save metadata to file
    output_file = f'/tmp/{service_name}_metadata.json'
    with open(output_file, 'w') as f:
        json.dump(metadata, f, indent=2, default=str)
    
    print(f'💾 Metadata saved to: {output_file}')
    print(f'📈 Summary:')
    print(f'  - Service: {metadata["service"]["name"]}')
    print(f'  - Tables: {len(metadata["tables"])}')
    print(f'  - Total files: {len(files)}')
    
    # Display file summary
    for table in metadata['tables']:
        print(f'  - {table["name"]}: {len(table["files"])} files')
    
    return True

if __name__ == '__main__':
    try:
        success = run_ingestion()
        if success:
            print('✅ Ingestion completed successfully!')
            sys.exit(0)
        else:
            print('❌ Ingestion failed')
            sys.exit(1)
    except Exception as e:
        print(f'💥 Ingestion error: {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)
EOF"

# Run the ingestion
print_status "Running S3 metadata ingestion..."
sudo docker exec "$CONTAINER" python3 /tmp/run_s3_ingestion.py

# Copy results back
print_status "Copying results..."
sudo docker exec "$CONTAINER" bash -c "ls -la /tmp/*metadata.json 2>/dev/null || echo 'No metadata files found'"

# Copy metadata file back to host if it exists
sudo docker exec "$CONTAINER" bash -c "
    for file in /tmp/*metadata.json; do
        if [[ -f \$file ]]; then
            echo \"Copying \$file to host...\"
            cp \$file /tmp/
        fi
    done
"

if sudo docker exec "$CONTAINER" test -f "/tmp/s3-manual-connector_metadata.json"; then
    sudo docker cp "$CONTAINER:/tmp/s3-manual-connector_metadata.json" "./s3_metadata_$(date +%Y%m%d_%H%M%S).json"
    print_success "Metadata file copied to host"
fi

print_success "🎉 S3 ingestion workflow completed!"
echo ""
echo "📋 Next steps:"
echo "1. Review the generated metadata file"
echo "2. Optionally import metadata to OpenMetadata via REST API"
echo "3. Set up automated ingestion scheduling"
