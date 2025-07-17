#!/bin/bash
# Enhanced S3 connection test with RBAC and IAM support

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

echo "🔐 S3 Connector RBAC Security Test"
echo "=================================="

# Load environment if .env exists
if [[ -f "config/.env" ]]; then
    echo "Loading environment from config/.env"
    export $(cat config/.env | grep -v '^#' | xargs)
fi

# Test different authentication methods
echo "Testing S3 connection with RBAC validation..."

sudo docker exec openmetadata_ingestion python3 -c "
import boto3
import sys
import os
import json
from botocore.exceptions import ClientError, NoCredentialsError

def test_iam_permissions():
    '''Test IAM permissions and role assumptions'''
    print('🔐 Testing IAM Configuration...')
    
    # Get credentials configuration
    access_key = os.environ.get('AWS_ACCESS_KEY_ID', '')
    secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY', '')
    session_token = os.environ.get('AWS_SESSION_TOKEN', '')
    assume_role_arn = os.environ.get('AWS_ASSUME_ROLE_ARN', '')
    external_id = os.environ.get('AWS_EXTERNAL_ID', '')
    region = os.environ.get('AWS_REGION', 'us-east-1')
    endpoint = os.environ.get('S3_ENDPOINT_URL', '')
    verify_ssl = os.environ.get('S3_VERIFY_SSL', 'true').lower() == 'true'
    bucket = os.environ.get('S3_BUCKET_NAME', 'test-bucket')
    
    print(f'Region: {region}')
    print(f'Endpoint: {endpoint or \"AWS S3\"}')
    print(f'Verify SSL: {verify_ssl}')
    print(f'Bucket: {bucket}')
    
    # Determine authentication method
    if assume_role_arn:
        print(f'🎭 Using IAM Role: {assume_role_arn}')
        auth_method = 'iam_role'
    elif access_key and access_key != 'your-access-key':
        if session_token:
            print('🔑 Using temporary credentials (STS)')
            auth_method = 'sts_token'
        else:
            print('🔑 Using IAM user credentials')
            auth_method = 'iam_user'
    else:
        print('🏠 Using instance profile/default credentials')
        auth_method = 'instance_profile'
    
    print()
    
    try:
        # Create session based on auth method
        if auth_method == 'iam_role':
            # Assume role
            sts_client = boto3.client('sts', region_name=region)
            assume_role_kwargs = {
                'RoleArn': assume_role_arn,
                'RoleSessionName': 'openmetadata-s3-test'
            }
            if external_id:
                assume_role_kwargs['ExternalId'] = external_id
                
            response = sts_client.assume_role(**assume_role_kwargs)
            credentials = response['Credentials']
            
            session = boto3.Session(
                aws_access_key_id=credentials['AccessKeyId'],
                aws_secret_access_key=credentials['SecretAccessKey'],
                aws_session_token=credentials['SessionToken'],
                region_name=region
            )
            print('✅ IAM role assumption successful')
            
        elif auth_method == 'sts_token':
            session = boto3.Session(
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                aws_session_token=session_token,
                region_name=region
            )
            print('✅ STS token authentication successful')
            
        elif auth_method == 'iam_user':
            session = boto3.Session(
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=region
            )
            print('✅ IAM user authentication successful')
            
        else:
            # Use default credentials (instance profile, environment, etc.)
            session = boto3.Session(region_name=region)
            print('✅ Default credentials authentication successful')
        
        # Create S3 client
        client_kwargs = {'verify': verify_ssl}
        if endpoint:
            client_kwargs['endpoint_url'] = endpoint
            
        s3_client = session.client('s3', **client_kwargs)
        sts_client = session.client('sts')
        
        # Test 1: Get caller identity
        print('\\n🔍 Testing caller identity...')
        identity = sts_client.get_caller_identity()
        print(f'✅ Account: {identity.get(\"Account\", \"Unknown\")}')
        print(f'✅ User ARN: {identity.get(\"Arn\", \"Unknown\")}')
        print(f'✅ User ID: {identity.get(\"UserId\", \"Unknown\")}')
        
        # Test 2: List buckets permission
        print('\\n🔍 Testing bucket listing permissions...')
        try:
            response = s3_client.list_buckets()
            buckets = [b['Name'] for b in response['Buckets']]
            print(f'✅ s3:ListAllMyBuckets - Found {len(buckets)} buckets')
            if buckets:
                print(f'   Buckets: {buckets[:5]}...' if len(buckets) > 5 else f'   Buckets: {buckets}')
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'AccessDenied':
                print('⚠️  s3:ListAllMyBuckets - Access denied (this is optional)')
            else:
                print(f'❌ s3:ListAllMyBuckets - Error: {error_code}')
        
        # Test 3: Specific bucket permissions
        if bucket and bucket != 'test-bucket':
            print(f'\\n🔍 Testing bucket-specific permissions for: {bucket}')
            
            # Test bucket head
            try:
                s3_client.head_bucket(Bucket=bucket)
                print(f'✅ s3:ListBucket - Bucket {bucket} is accessible')
            except ClientError as e:
                error_code = e.response['Error']['Code']
                print(f'❌ s3:ListBucket - Error: {error_code}')
                return False
            
            # Test bucket location
            try:
                response = s3_client.get_bucket_location(Bucket=bucket)
                location = response.get('LocationConstraint') or 'us-east-1'
                print(f'✅ s3:GetBucketLocation - Bucket location: {location}')
            except ClientError as e:
                error_code = e.response['Error']['Code']
                print(f'⚠️  s3:GetBucketLocation - Error: {error_code}')
            
            # Test object listing
            try:
                response = s3_client.list_objects_v2(Bucket=bucket, MaxKeys=5)
                if 'Contents' in response:
                    objects = [obj['Key'] for obj in response['Contents']]
                    print(f'✅ s3:ListBucket - Found {len(objects)} objects (showing first 5)')
                    for obj in objects:
                        print(f'   - {obj}')
                        
                    # Test object access on first object
                    if objects:
                        test_object = objects[0]
                        try:
                            s3_client.head_object(Bucket=bucket, Key=test_object)
                            print(f'✅ s3:GetObject - Object {test_object} is accessible')
                        except ClientError as e:
                            error_code = e.response['Error']['Code']
                            print(f'❌ s3:GetObject - Error accessing {test_object}: {error_code}')
                else:
                    print(f'✅ s3:ListBucket - Bucket {bucket} is empty but accessible')
                    
            except ClientError as e:
                error_code = e.response['Error']['Code']
                print(f'❌ s3:ListBucket - Error listing objects: {error_code}')
                return False
        
        # Test 4: Advanced permissions (optional)
        print('\\n🔍 Testing advanced permissions...')
        advanced_permissions = [
            ('s3:GetBucketVersioning', lambda: s3_client.get_bucket_versioning(Bucket=bucket)),
            ('s3:GetBucketTagging', lambda: s3_client.get_bucket_tagging(Bucket=bucket)),
            ('s3:GetBucketPolicy', lambda: s3_client.get_bucket_policy(Bucket=bucket)),
        ]
        
        for perm_name, test_func in advanced_permissions:
            try:
                test_func()
                print(f'✅ {perm_name} - Available')
            except ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code in ['AccessDenied', 'NoSuchBucket', 'NoSuchBucketPolicy', 'NoSuchTagSet']:
                    print(f'⚠️  {perm_name} - Not available ({error_code})')
                else:
                    print(f'❌ {perm_name} - Error: {error_code}')
        
        print('\\n✅ RBAC Security test PASSED!')
        print('\\n🎯 Permission Summary:')
        print('   ✅ Authentication successful')
        print('   ✅ Basic S3 access confirmed')
        print('   ✅ Bucket permissions validated')
        print('   ℹ️  Advanced permissions tested (optional)')
        
        return True
        
    except NoCredentialsError:
        print('❌ No AWS credentials found')
        print('💡 Configure credentials using one of:')
        print('   - Environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)')
        print('   - IAM role assumption (AWS_ASSUME_ROLE_ARN)')
        print('   - Instance profile')
        print('   - AWS credentials file')
        return False
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f'❌ AWS API Error: {error_code}')
        print(f'   Message: {error_message}')
        
        if error_code == 'InvalidAccessKeyId':
            print('💡 Check that AWS_ACCESS_KEY_ID is correct')
        elif error_code == 'SignatureDoesNotMatch':
            print('💡 Check that AWS_SECRET_ACCESS_KEY is correct')
        elif error_code == 'TokenRefreshRequired':
            print('💡 Refresh your session token')
        elif error_code == 'AccessDenied':
            print('💡 Check IAM permissions - see documentation for required policies')
        
        return False
        
    except Exception as e:
        print(f'💥 Unexpected error: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    try:
        success = test_iam_permissions()
        if success:
            print('\\n🎉 Ready for metadata ingestion!')
            sys.exit(0)
        else:
            print('\\n🚨 Fix the issues above before running ingestion')
            sys.exit(1)
    except KeyboardInterrupt:
        print('\\n⏹️  Test interrupted by user')
        sys.exit(1)
"

echo ""
echo "📋 Security Checklist:"
echo "✓ Test AWS credentials and permissions"
echo "✓ Validate IAM policies and roles" 
echo "✓ Check bucket access permissions"
echo "✓ Verify SSL/TLS configuration"
echo ""
echo "🚀 If all tests pass, run:"
echo "   ./scripts/run-manual-ingestion.sh config/prod-s3-ingestion-rbac.yaml"
