# 🔐 S3 Connector Security & RBAC Checklist

## Pre-Deployment Security Checklist

### ✅ AWS IAM Configuration
- [ ] **IAM User Created** - Dedicated user for OpenMetadata S3 connector
- [ ] **Minimal Permissions** - Only required S3 permissions granted
- [ ] **MFA Enabled** - Multi-factor authentication for IAM user (if using access keys)
- [ ] **Access Key Rotation** - Plan for regular access key rotation
- [ ] **Policy Validation** - IAM policy simulator tested

### ✅ AWS S3 Bucket Security
- [ ] **Bucket Policy** - Restrictive bucket policy in place
- [ ] **Public Access Blocked** - All public access blocked
- [ ] **Versioning Enabled** - Bucket versioning for data protection
- [ ] **Encryption Enabled** - Server-side encryption configured
- [ ] **Access Logging** - S3 access logging enabled
- [ ] **CloudTrail Enabled** - API calls logged to CloudTrail

### ✅ Network Security
- [ ] **VPC Endpoints** - Using VPC endpoints for S3 access (production)
- [ ] **SSL/TLS** - All connections use HTTPS/SSL
- [ ] **Custom CA** - Custom certificate authority configured (if needed)
- [ ] **Network ACLs** - Appropriate network access controls
- [ ] **Security Groups** - Restrictive security group rules

### ✅ Credential Management
- [ ] **No Hardcoded Secrets** - No credentials in code/configs
- [ ] **Environment Variables** - Secrets in environment variables or secret managers
- [ ] **AWS Secrets Manager** - Using AWS Secrets Manager (recommended)
- [ ] **IAM Roles** - Using IAM roles instead of access keys (recommended)
- [ ] **Session Tokens** - Temporary credentials with session tokens

### ✅ MinIO Security (if applicable)
- [ ] **Strong Passwords** - Complex passwords for MinIO users
- [ ] **Service Accounts** - Dedicated service accounts, not admin accounts
- [ ] **Policy-Based Access** - Granular policies for different access levels
- [ ] **TLS Configuration** - HTTPS enabled with valid certificates
- [ ] **Audit Logging** - MinIO audit logging enabled

## Production Deployment Checklist

### ✅ Authentication Methods (Choose One)

#### Option 1: IAM Roles (Recommended)
- [ ] **Cross-Account Role** - Set up if accessing buckets in different accounts
- [ ] **External ID** - Configured for additional security
- [ ] **Session Name** - Descriptive session names for auditing
- [ ] **Role Permissions** - Minimal required permissions only
- [ ] **Trust Policy** - Restrictive trust relationship

#### Option 2: IAM User with Access Keys
- [ ] **Dedicated User** - Separate user just for this connector
- [ ] **Programmatic Access** - Console access disabled
- [ ] **Key Rotation** - Automated key rotation scheduled
- [ ] **Key Storage** - Keys stored in secure secret management system

#### Option 3: STS Temporary Credentials
- [ ] **Token Duration** - Appropriate session duration configured
- [ ] **Token Refresh** - Automatic token refresh mechanism
- [ ] **Fallback Mechanism** - Backup authentication method available

### ✅ Permission Validation

#### Required S3 Permissions
- [ ] **s3:ListBucket** - Can list objects in target buckets
- [ ] **s3:GetObject** - Can read object content
- [ ] **s3:GetBucketLocation** - Can determine bucket region
- [ ] **s3:GetObjectVersion** - Can access object versions (if versioning enabled)

#### Optional S3 Permissions (for advanced features)
- [ ] **s3:GetBucketVersioning** - For versioning information
- [ ] **s3:GetBucketTagging** - For bucket-level tags
- [ ] **s3:GetObjectTagging** - For object-level tags
- [ ] **s3:GetBucketPolicy** - For policy analysis
- [ ] **s3:ListAllMyBuckets** - For service discovery

### ✅ Data Protection

#### Access Controls
- [ ] **Bucket Restrictions** - Access limited to specific buckets
- [ ] **Path Restrictions** - Access limited to specific prefixes/folders
- [ ] **IP Restrictions** - Source IP address restrictions
- [ ] **Time Restrictions** - Time-based access controls
- [ ] **Conditional Access** - IAM conditions for additional security

#### Data Classification
- [ ] **PII Detection** - Enabled for sensitive data discovery
- [ ] **Data Classification** - Automatic classification rules configured
- [ ] **Sensitive Data Exclusion** - Sensitive folders/files excluded from processing
- [ ] **File Size Limits** - Large file processing limits configured
- [ ] **Sampling Rules** - Data sampling for performance and security

## Monitoring & Compliance

### ✅ Audit & Logging
- [ ] **CloudTrail Logs** - All API calls logged and monitored
- [ ] **S3 Access Logs** - Detailed access logging enabled
- [ ] **Application Logs** - Connector activity logged
- [ ] **Error Monitoring** - Failed access attempts monitored
- [ ] **Alert Configuration** - Alerts for suspicious activity

### ✅ Compliance Requirements
- [ ] **Data Residency** - Data processing location compliance
- [ ] **Retention Policies** - Log retention according to requirements
- [ ] **Privacy Regulations** - GDPR/CCPA compliance measures
- [ ] **Industry Standards** - SOX/HIPAA/PCI compliance (if applicable)
- [ ] **Documentation** - Security controls documented

### ✅ Performance & Reliability
- [ ] **Rate Limiting** - API rate limits configured
- [ ] **Timeout Configuration** - Appropriate timeouts set
- [ ] **Retry Logic** - Exponential backoff retry mechanism
- [ ] **Circuit Breaker** - Failure handling mechanisms
- [ ] **Resource Limits** - Memory and CPU limits configured

## Testing & Validation

### ✅ Security Testing
- [ ] **Permission Testing** - All required permissions tested
- [ ] **Negative Testing** - Unauthorized access attempts fail
- [ ] **Network Testing** - SSL/TLS configuration validated
- [ ] **Token Expiration** - Credential expiration handling tested
- [ ] **Error Handling** - Security error responses appropriate

### ✅ Operational Testing
- [ ] **Connection Testing** - Basic connectivity verified
- [ ] **File Discovery** - File listing and filtering working
- [ ] **Metadata Extraction** - Schema detection functioning
- [ ] **Large Dataset Testing** - Performance with large datasets
- [ ] **Failure Recovery** - Recovery from various failure scenarios

## Security Commands Reference

### Test Commands
```bash
# Test RBAC and security configuration
./scripts/test-rbac-security.sh

# Test with production configuration
./scripts/test-s3-connection.sh config/prod-s3-ingestion-rbac.yaml

# Run security-focused ingestion
./scripts/run-manual-ingestion.sh config/prod-s3-ingestion-rbac.yaml
```

### AWS CLI Validation
```bash
# Test IAM permissions
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::123456789012:user/openmetadata-s3-connector \
  --action-names s3:ListBucket s3:GetObject \
  --resource-arns arn:aws:s3:::your-bucket arn:aws:s3:::your-bucket/*

# Test role assumption
aws sts assume-role \
  --role-arn arn:aws:iam::123456789012:role/OpenMetadata-S3-Role \
  --role-session-name test-session

# Test bucket access
aws s3api head-bucket --bucket your-bucket-name
aws s3api list-objects-v2 --bucket your-bucket-name --max-items 1
```

### MinIO Client Validation
```bash
# Test MinIO access
mc alias set minio http://localhost:9000 minioadmin minioadmin
mc ls minio/your-bucket
mc stat minio/your-bucket/sample-file.csv
```

## Security Incident Response

### ✅ Incident Response Plan
- [ ] **Detection Procedures** - How to detect security incidents
- [ ] **Response Team** - Designated incident response team
- [ ] **Communication Plan** - Internal and external communication procedures
- [ ] **Containment Steps** - Immediate actions to contain incidents
- [ ] **Recovery Procedures** - Steps to restore normal operations
- [ ] **Post-Incident Review** - Process for learning from incidents

### ✅ Emergency Procedures
- [ ] **Credential Revocation** - How to quickly revoke compromised credentials
- [ ] **Access Disabling** - How to disable connector access
- [ ] **Backup Authentication** - Alternative authentication methods
- [ ] **Escalation Procedures** - When and how to escalate issues
- [ ] **Documentation Updates** - How to update security documentation

---

**Note**: This checklist should be customized based on your organization's specific security requirements and compliance needs.
