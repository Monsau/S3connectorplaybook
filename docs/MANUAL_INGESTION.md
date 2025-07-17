# S3 Connector Manual Ingestion Guide

This guide shows how to use the S3 connector for metadata ingestion **without using the OpenMetadata web interface**.

## 🚀 Quick Start

### 1. Test S3 Connection
```bash
# Basic connectivity test
./scripts/test-s3-connection.sh

# Advanced RBAC and security validation
./scripts/test-rbac-security.sh
```

### 2. Configure Credentials
Choose one of these methods:

**Option A: Environment File**
```bash
cp config/.env.example config/.env
# Edit config/.env with your credentials
```

**Option B: Environment Variables**
```bash
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_REGION="us-east-1"
export S3_ENDPOINT_URL="http://localhost:9000"  # For MinIO
export S3_BUCKET_NAME="your-bucket"
```

**Option C: Direct Configuration**
```bash
# Edit config/manual-s3-ingestion.yaml directly
```

### 3. Run Ingestion
```bash
./scripts/run-manual-ingestion.sh
```

## 📋 Configuration Examples

### AWS S3
```yaml
source:
  serviceConnection:
    config:
      awsAccessKeyId: "AKIA..."
      awsSecretAccessKey: "secret..."
      awsRegion: "us-west-2"
      endPointURL: ""  # Empty for AWS S3
      verifySSL: true
      bucketName: "my-data-bucket"
```

### MinIO
```yaml
source:
  serviceConnection:
    config:
      awsAccessKeyId: "minioadmin"
      awsSecretAccessKey: "minioadmin"
      awsRegion: "us-east-1"
      endPointURL: "http://localhost:9000"
      verifySSL: false
      bucketName: "my-minio-bucket"
```

### File Filtering
```yaml
source:
  sourceConfig:
    config:
      tableFilterPattern:
        includes:
          - ".*\\.csv$"      # CSV files
          - ".*\\.parquet$"  # Parquet files
          - ".*\\.json$"     # JSON files
          - "data/.*"        # Files in data/ folder
        excludes:
          - ".*\\.tmp$"      # Exclude temp files
          - ".*/backup/.*"   # Exclude backup folder
```

## 🔧 Advanced Usage

### Custom Script Integration
The manual ingestion can be integrated into your workflows:

```bash
# Run with custom config
./scripts/run-manual-ingestion.sh path/to/custom-config.yaml

# Schedule with cron
0 2 * * * /path/to/S3connectorplaybook/scripts/run-manual-ingestion.sh

# Integration with CI/CD
- name: Run S3 Metadata Ingestion
  run: |
    cd S3connectorplaybook
    ./scripts/test-s3-connection.sh
    ./scripts/run-manual-ingestion.sh
```

### Output Processing
The ingestion generates metadata JSON files:
```bash
# Generated file: s3_metadata_YYYYMMDD_HHMMSS.json
{
  "service": {
    "name": "s3-manual-connector",
    "type": "S3",
    "description": "S3 storage service with 150 files"
  },
  "tables": [
    {
      "name": "s3_csv_files",
      "displayName": "S3 CSV Files",
      "description": "Collection of 45 csv files from S3",
      "columns": [...],
      "files": [...]
    }
  ]
}
```

## 🛠 Troubleshooting

### Connection Issues
```bash
# Debug S3 connection
./scripts/test-s3-connection.sh

# Check container logs
sudo docker logs openmetadata_ingestion

# Verify network connectivity
sudo docker exec openmetadata_ingestion ping your-minio-host
```

### Common Solutions

**1. MinIO Connection Issues**
- Use `http://host.docker.internal:9000` for local MinIO
- Set `verifySSL: false` for self-signed certificates
- Ensure MinIO is accessible from container

**2. AWS S3 Issues**
- Verify IAM permissions include `s3:ListBucket`, `s3:GetObject`
- Check region settings match bucket region
- Ensure credentials are not expired
- See [RBAC & IAM Configuration](#rbac--iam-configuration) for detailed permissions

**3. File Discovery Issues**
- Check bucket name spelling
- Verify regex patterns in `tableFilterPattern`
- Ensure bucket has readable objects

## � RBAC & IAM Configuration

### AWS IAM Setup

#### Required IAM Permissions
Create an IAM policy with the following minimum permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket",
        "s3:GetBucketLocation",
        "s3:GetBucketVersioning"
      ],
      "Resource": [
        "arn:aws:s3:::your-bucket-name"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:GetObjectVersion",
        "s3:GetObjectAttributes"
      ],
      "Resource": [
        "arn:aws:s3:::your-bucket-name/*"
      ]
    }
  ]
}
```

#### Enhanced Permissions (Optional)
For advanced features like schema detection and data profiling:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket",
        "s3:GetBucketLocation",
        "s3:GetBucketVersioning",
        "s3:GetBucketTagging",
        "s3:GetBucketPolicy",
        "s3:GetBucketAcl",
        "s3:GetBucketNotification"
      ],
      "Resource": [
        "arn:aws:s3:::your-bucket-name"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:GetObjectVersion",
        "s3:GetObjectAttributes",
        "s3:GetObjectTagging",
        "s3:GetObjectAcl",
        "s3:ListMultipartUploadParts"
      ],
      "Resource": [
        "arn:aws:s3:::your-bucket-name/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:ListAllMyBuckets"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "s3:ExistingObjectTag/Environment": ["prod", "staging"]
        }
      }
    }
  ]
}
```

#### IAM User Creation
```bash
# Create IAM user for the connector
aws iam create-user --user-name openmetadata-s3-connector

# Attach the policy
aws iam attach-user-policy \
  --user-name openmetadata-s3-connector \
  --policy-arn arn:aws:iam::YOUR-ACCOUNT:policy/OpenMetadata-S3-ReadOnly

# Create access key
aws iam create-access-key --user-name openmetadata-s3-connector
```

### AWS IAM Roles (Recommended)

#### For EC2/ECS Deployments
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ec2.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

#### For Cross-Account Access
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::TRUSTED-ACCOUNT:root"
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": {
          "sts:ExternalId": "unique-external-id"
        }
      }
    }
  ]
}
```

#### Configuration with IAM Roles
```yaml
source:
  serviceConnection:
    config:
      # Option 1: EC2 Instance Profile
      awsConfig:
        awsRegion: "us-west-2"
        
      # Option 2: Assume Role
      awsConfig:
        awsRegion: "us-west-2"
        assumeRoleArn: "arn:aws:iam::123456789012:role/OpenMetadata-S3-Role"
        assumeRoleExternalId: "unique-external-id"
        
      # Option 3: STS Token
      awsSessionToken: "temporary-session-token"
```

### MinIO RBAC Configuration

#### Create MinIO Service Account
```bash
# Using MinIO client (mc)
mc admin user add myminio openmetadata-connector SecurePassword123

# Create policy for metadata access
cat > s3-metadata-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket",
        "s3:GetBucketLocation"
      ],
      "Resource": [
        "arn:aws:s3:::data-*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject"
      ],
      "Resource": [
        "arn:aws:s3:::data-*/*"
      ]
    }
  ]
}
EOF

# Add policy to MinIO
mc admin policy add myminio s3-metadata-readonly s3-metadata-policy.json

# Assign policy to user
mc admin policy set myminio s3-metadata-readonly user=openmetadata-connector
```

#### MinIO Group-Based Access
```bash
# Create group
mc admin group add myminio metadata-readers

# Add user to group
mc admin group add myminio metadata-readers openmetadata-connector

# Assign policy to group
mc admin policy set myminio s3-metadata-readonly group=metadata-readers
```

### Security Best Practices

#### Credential Management
```bash
# Option 1: AWS Secrets Manager
export AWS_SECRET_NAME="openmetadata/s3-credentials"
export AWS_REGION="us-west-2"

# Option 2: Environment variables (less secure)
export AWS_ACCESS_KEY_ID="$(aws secretsmanager get-secret-value --secret-id $AWS_SECRET_NAME --query SecretString --output text | jq -r .access_key)"
export AWS_SECRET_ACCESS_KEY="$(aws secretsmanager get-secret-value --secret-id $AWS_SECRET_NAME --query SecretString --output text | jq -r .secret_key)"

# Option 3: Kubernetes secrets
kubectl create secret generic s3-credentials \
  --from-literal=access-key="AKIA..." \
  --from-literal=secret-key="secret..."
```

#### Network Security
```yaml
source:
  serviceConnection:
    config:
      # VPC Endpoint for S3 (recommended for production)
      endPointURL: "https://s3.us-west-2.amazonaws.com"
      
      # Custom CA certificates
      customCACertPath: "/path/to/custom-ca.pem"
      
      # SSL verification
      verifySSL: true
      
      # Connection timeout and retries
      connectionConfig:
        timeout: 30
        maxRetries: 3
        retryMode: "adaptive"
```

#### Bucket-Level Security
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "OpenMetadataReadAccess",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::YOUR-ACCOUNT:user/openmetadata-s3-connector"
      },
      "Action": [
        "s3:ListBucket",
        "s3:GetObject"
      ],
      "Resource": [
        "arn:aws:s3:::your-bucket",
        "arn:aws:s3:::your-bucket/*"
      ],
      "Condition": {
        "IpAddress": {
          "aws:SourceIp": ["203.0.113.0/24"]
        },
        "DateGreaterThan": {
          "aws:CurrentTime": "2024-01-01T00:00:00Z"
        }
      }
    }
  ]
}
```

### Multi-Environment Configuration

#### Development Environment
```yaml
# config/dev-s3-ingestion.yaml
source:
  serviceConnection:
    config:
      awsAccessKeyId: "${DEV_AWS_ACCESS_KEY_ID}"
      awsSecretAccessKey: "${DEV_AWS_SECRET_ACCESS_KEY}"
      awsRegion: "us-east-1"
      bucketName: "dev-data-bucket"
      # Relaxed security for development
      verifySSL: false
```

#### Production Environment
```yaml
# config/prod-s3-ingestion.yaml
source:
  serviceConnection:
    config:
      # Use IAM roles in production
      awsConfig:
        awsRegion: "us-west-2"
        assumeRoleArn: "arn:aws:iam::PROD-ACCOUNT:role/OpenMetadata-Prod-Role"
      bucketName: "prod-data-bucket"
      # Strict security for production
      verifySSL: true
      connectionConfig:
        useSSL: true
        sslMode: "require"
```

### Compliance & Auditing

#### CloudTrail Integration
```json
{
  "eventVersion": "1.05",
  "userIdentity": {
    "type": "IAMUser",
    "principalId": "AIDACKCEVSQ6C2EXAMPLE",
    "arn": "arn:aws:iam::123456789012:user/openmetadata-s3-connector",
    "accountId": "123456789012",
    "userName": "openmetadata-s3-connector"
  },
  "eventTime": "2024-07-17T14:30:00Z",
  "eventSource": "s3.amazonaws.com",
  "eventName": "GetObject",
  "requestParameters": {
    "bucketName": "data-bucket",
    "key": "data/file.csv"
  }
}
```

#### Monitoring Access Patterns
```bash
# Monitor S3 access logs
aws logs filter-log-events \
  --log-group-name /aws/s3/access-logs \
  --filter-pattern "openmetadata-s3-connector" \
  --start-time $(date -d "1 hour ago" +%s)000

# Set up CloudWatch alarms
aws cloudwatch put-metric-alarm \
  --alarm-name "S3-Unusual-Access-Pattern" \
  --alarm-description "Detect unusual S3 access patterns" \
  --metric-name NumberOfObjects \
  --namespace AWS/S3 \
  --statistic Sum \
  --period 300 \
  --threshold 1000 \
  --comparison-operator GreaterThanThreshold
```

### Troubleshooting RBAC Issues

#### Permission Denied Errors
```bash
# Test specific permissions
aws s3api head-bucket --bucket your-bucket-name
aws s3api list-objects-v2 --bucket your-bucket-name --max-items 1

# Check IAM policy simulation
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::123456789012:user/openmetadata-s3-connector \
  --action-names s3:ListBucket s3:GetObject \
  --resource-arns arn:aws:s3:::your-bucket arn:aws:s3:::your-bucket/*
```

#### Role Assumption Issues
```bash
# Test role assumption
aws sts assume-role \
  --role-arn arn:aws:iam::123456789012:role/OpenMetadata-S3-Role \
  --role-session-name openmetadata-test \
  --external-id unique-external-id

# Check trust relationship
aws iam get-role --role-name OpenMetadata-S3-Role
```

## �📊 Metadata Schema

The connector discovers and catalogs:

### File Types Supported
- **CSV**: Comma-separated values
- **JSON/JSONL**: JSON documents
- **Parquet**: Columnar storage format
- **Avro**: Schema evolution support
- **ORC**: Optimized row columnar
- **Excel**: .xlsx, .xls files
- **TSV**: Tab-separated values
- **Feather**: Fast serialization
- **Delta**: Delta Lake format

### Generated Metadata
- **Service**: S3 storage service definition
- **Tables**: Logical groupings by file type
- **Columns**: Standard schema (file_path, file_size, last_modified)
- **Files**: Complete file inventory with metadata

## 🔄 Integration Options

### Option 1: Standalone Usage
Use the generated metadata files in your own systems:
```python
import json

with open('s3_metadata_20250717_143022.json') as f:
    metadata = json.load(f)
    
for table in metadata['tables']:
    print(f"Table: {table['name']}")
    print(f"Files: {len(table['files'])}")
```

### Option 2: OpenMetadata API Integration
Push metadata to OpenMetadata via REST API:
```bash
# Example API call (requires authentication setup)
curl -X POST http://localhost:8585/api/v1/services/storageServices \
  -H "Content-Type: application/json" \
  -d @s3_metadata_20250717_143022.json
```

### Option 3: Custom Processing
Extend the ingestion script for your needs:
- Add custom file parsers
- Implement schema detection
- Generate data quality reports
- Create lineage information

## 📚 Related Files

- `config/manual-s3-ingestion.yaml` - Basic configuration
- `config/prod-s3-ingestion-rbac.yaml` - Production RBAC configuration
- `config/.env.example` - Environment template
- `scripts/run-manual-ingestion.sh` - Main runner
- `scripts/test-s3-connection.sh` - Basic connection tester
- `scripts/test-rbac-security.sh` - RBAC and security validator
- `docs/SECURITY_CHECKLIST.md` - Comprehensive security checklist
- `deployment/docker-hotdeploy/` - Container deployment tools

## 🔐 Security Commands Quick Reference

```bash
# Security testing and validation
./scripts/test-rbac-security.sh

# Production deployment with RBAC
./scripts/run-manual-ingestion.sh config/prod-s3-ingestion-rbac.yaml

# AWS IAM policy simulation
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::ACCOUNT:user/openmetadata-s3-connector \
  --action-names s3:ListBucket s3:GetObject \
  --resource-arns arn:aws:s3:::bucket arn:aws:s3:::bucket/*
```

---

**Note**: This manual approach bypasses the OpenMetadata web interface while providing comprehensive S3 metadata discovery, cataloging capabilities, and enterprise-grade security controls.
