#!/bin/bash
# Test S3 connectivity before running ingestion

echo "🧪 Testing S3 Connector Setup"
echo "=============================="

# Load environment if .env exists
if [[ -f "config/.env" ]]; then
    echo "Loading environment from config/.env"
    export $(cat config/.env | grep -v '^#' | xargs)
fi

# Test connection using the ingestion container
echo "Testing S3 connection..."

sudo docker exec openmetadata_ingestion python3 -c "
import boto3
import sys
import os

# Get credentials from environment
access_key = os.environ.get('AWS_ACCESS_KEY_ID', 'your-access-key')
secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY', 'your-secret-key')
region = os.environ.get('AWS_REGION', 'us-east-1')
endpoint = os.environ.get('S3_ENDPOINT_URL', '')
verify_ssl = os.environ.get('S3_VERIFY_SSL', 'true').lower() == 'true'
bucket = os.environ.get('S3_BUCKET_NAME', 'test-bucket')

print(f'Access Key: {access_key[:8]}...')
print(f'Region: {region}')
print(f'Endpoint: {endpoint or \"AWS S3\"}')
print(f'Verify SSL: {verify_ssl}')
print(f'Bucket: {bucket}')
print()

try:
    # Create session
    session = boto3.Session(
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=region
    )
    
    # Create client
    client_kwargs = {'verify': verify_ssl}
    if endpoint:
        client_kwargs['endpoint_url'] = endpoint
        
    s3_client = session.client('s3', **client_kwargs)
    
    # Test 1: List buckets
    print('🔍 Testing bucket listing...')
    response = s3_client.list_buckets()
    buckets = [b['Name'] for b in response['Buckets']]
    print(f'✅ Found {len(buckets)} buckets: {buckets}')
    
    # Test 2: Check specific bucket
    if bucket in buckets:
        print(f'🔍 Testing bucket access: {bucket}')
        response = s3_client.list_objects_v2(Bucket=bucket, MaxKeys=5)
        if 'Contents' in response:
            files = [obj['Key'] for obj in response['Contents']]
            print(f'✅ Bucket accessible, found {len(files)} objects (showing first 5): {files}')
        else:
            print(f'✅ Bucket accessible but empty')
    else:
        print(f'⚠️  Bucket \"{bucket}\" not found in: {buckets}')
        
    print()
    print('✅ S3 connectivity test PASSED!')
    
except Exception as e:
    print(f'❌ S3 connectivity test FAILED: {e}')
    sys.exit(1)
"

echo ""
echo "🎯 If the test passed, you can run:"
echo "   ./scripts/run-manual-ingestion.sh"
echo ""
echo "📝 Configuration options:"
echo "   1. Copy config/.env.example to config/.env and update values"
echo "   2. Or export environment variables directly"
echo "   3. Or edit config/manual-s3-ingestion.yaml directly"
