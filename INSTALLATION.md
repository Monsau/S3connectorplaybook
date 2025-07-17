# 🚀 OpenMetadata S3/MinIO Connector - Complete Installation Guide

[![Production Ready](https://img.shields.io/badge/status-production%20ready-green.svg)](#installation-options)
[![Manual Ingestion](https://img.shields.io/badge/manual%20ingestion-supported-blue.svg)](#manual-ingestion-setup)
[![Hot Deploy](https://img.shields.io/badge/hot%20deploy-zero%20downtime-green.svg)](#hot-deployment)

This guide provides comprehensive installation instructions for the OpenMetadata S3/MinIO Connector with full support for **manual ingestion**, **RBAC/IAM**, and **hot deployment**.

## 📋 Table of Contents

- [🎯 Installation Options](#-installation-options)
- [🚀 Quick Installation (5 minutes)](#-quick-installation-5-minutes)
- [🔐 Manual Ingestion Setup](#-manual-ingestion-setup)
- [🐳 Hot Deployment (Existing Containers)](#-hot-deployment-existing-containers)
- [🏗️ Production Installation](#️-production-installation)
- [✅ Verification & Testing](#-verification--testing)
- [🔧 Troubleshooting](#-troubleshooting)

---

## 🎯 Installation Options

| Installation Method | Use Case | Time Required | Features |
|-------------------|----------|---------------|----------|
| **[Quick Install](#-quick-installation-5-minutes)** | Development, Testing | 5 minutes | Basic connector functionality |
| **[Manual Ingestion](#-manual-ingestion-setup)** | Enterprise, RBAC | 15 minutes | UI-bypass, RBAC, PII detection |
| **[Hot Deploy](#-hot-deployment-existing-containers)** | Existing OpenMetadata | 10 minutes | Zero-downtime deployment |
| **[Production](#️-production-installation)** | Enterprise Production | 30 minutes | Full security, monitoring, HA |

---

## 🚀 Quick Installation (5 minutes)

### Prerequisites
- Python 3.8+ with pip
- Access to S3-compatible storage
- OpenMetadata instance (local or hosted)

### Step 1: Clone and Install
```bash
git clone https://github.com/Monsau/S3connectorplaybook.git
cd S3connectorplaybook

# Install dependencies
pip install --upgrade pip setuptools
pip install "openmetadata-ingestion==1.8.1"
pip install -r requirements.txt
pip install -e .
```

### Step 2: Quick Test
```bash
# Test installation
python -c "import connectors.s3.s3_connector; print('✅ S3 Connector installed successfully')"

# Run basic validation
python validate_parsers.py
```

### Step 3: Basic Configuration
```bash
# Copy example configuration
cp config/manual-s3-ingestion.yaml config/my-s3-config.yaml

# Edit with your credentials
nano config/my-s3-config.yaml
```

### Step 4: First Ingestion
```bash
# Set Python path
export PYTHONPATH=$(pwd)

# Run ingestion
metadata ingest -c config/my-s3-config.yaml
```

**✅ Quick Install Complete!** Visit your OpenMetadata instance to see the ingested metadata.

---

## 🔐 Manual Ingestion Setup

**🎯 For Enterprise Environments**: Complete UI-bypass workflow with advanced RBAC, IAM validation, and compliance features.

### Prerequisites
- IAM roles with appropriate S3 permissions
- OpenMetadata server with API access
- Security policies and compliance requirements

### Step 1: Environment Setup
```bash
# Copy environment template
cp config/.env.example config/.env

# Configure environment variables
nano config/.env
```

**Example `.env` configuration:**
```bash
# AWS Configuration (use IAM roles in production)
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-data-bucket

# OpenMetadata Configuration
OPENMETADATA_HOST_PORT=http://localhost:8585/api
OPENMETADATA_JWT_TOKEN=your_jwt_token

# Security Settings
ENABLE_RBAC=true
ENABLE_PII_DETECTION=true
COMPLIANCE_FRAMEWORK=GDPR,SOX,HIPAA
AUDIT_LEVEL=comprehensive
```

### Step 2: Security Validation
```bash
# Make scripts executable
chmod +x scripts/*.sh

# Test S3 connectivity and permissions
./scripts/test-s3-connection.sh

# Validate RBAC and IAM configuration
./scripts/test-rbac-security.sh
```

### Step 3: Configure Manual Ingestion
```bash
# Use production RBAC configuration
cp config/prod-s3-ingestion-rbac.yaml config/production-config.yaml

# Customize for your environment
nano config/production-config.yaml
```

### Step 4: Run Manual Ingestion
```bash
# Execute manual ingestion workflow
./scripts/run-manual-ingestion.sh config/production-config.yaml

# Monitor progress and logs
tail -f /var/log/openmetadata/ingestion.log
```

**✅ Manual Ingestion Features:**
- ✅ Complete UI bypass
- ✅ Advanced RBAC validation
- ✅ IAM role integration
- ✅ PII detection and classification
- ✅ Comprehensive audit logging
- ✅ Compliance framework support

---

## 🐳 Hot Deployment (Existing Containers)

**🎯 Zero-downtime deployment** to existing OpenMetadata Docker containers without rebuilding.

### Prerequisites
- Running OpenMetadata Docker containers
- Docker access and permissions
- Network connectivity to containers

### Step 1: Prepare Deployment
```bash
cd deployment/docker-hotdeploy/

# Make deployment scripts executable
chmod +x *.sh

# Verify OpenMetadata containers are running
docker ps | grep openmetadata
```

### Step 2: Hot Deploy
```bash
# Deploy connector to existing containers
./hot-deploy.sh

# Monitor deployment progress
docker logs openmetadata_server -f
```

### Step 3: Verify Deployment
```bash
# Run comprehensive health check
./health-check.sh

# Test connector functionality
./scripts/test-s3-connection.sh --container-mode
```

**✅ Hot Deployment Benefits:**
- ✅ Zero downtime
- ✅ No container rebuild required
- ✅ Preserves existing configurations
- ✅ Automatic rollback on failure
- ✅ Real-time health monitoring

---

## 🏗️ Production Installation

**🎯 Enterprise-grade deployment** with high availability, monitoring, and security.

### Prerequisites
- Production OpenMetadata environment
- Load balancer and SSL certificates
- Monitoring infrastructure (Prometheus/Grafana)
- Security scanning and compliance tools

### Step 1: Security Hardening
```bash
# Install security dependencies
pip install cryptography>=3.4.8
pip install pyjwt>=2.4.0

# Configure SSL/TLS
cp config/ssl-example.yaml config/production-ssl.yaml
nano config/production-ssl.yaml
```

### Step 2: High Availability Setup
```bash
# Deploy with multiple workers
export MAX_WORKER_THREADS=10
export ENABLE_RETRY=true
export MAX_RETRIES=3

# Configure load balancing
cp config/ha-example.yaml config/production-ha.yaml
```

### Step 3: Monitoring Integration
```bash
# Enable metrics and monitoring
export ENABLE_METRICS=true
export PROMETHEUS_ENDPOINT=http://prometheus:9090

# Configure audit logging
export AUDIT_LEVEL=comprehensive
export AUDIT_OUTPUT_PATH=/var/log/openmetadata/audit.log
```

### Step 4: Production Deployment
```bash
# Deploy with production configuration
./scripts/run-manual-ingestion.sh config/production-ha.yaml

# Verify all components
./scripts/test-rbac-security.sh --production-mode
```

---

## ✅ Verification & Testing

### Basic Verification
```bash
# Test connector import
python -c "import connectors.s3.s3_connector; print('✅ Connector imported')"

# Validate all parsers
python validate_parsers.py

# Test additional formats
python test_additional_formats.py
```

### Security Testing
```bash
# S3 connectivity and permissions
./scripts/test-s3-connection.sh

# RBAC and IAM validation
./scripts/test-rbac-security.sh

# Manual ingestion workflow
./scripts/run-manual-ingestion.sh --dry-run
```

### Production Health Checks
```bash
# Container health (for Docker deployments)
./deployment/docker-hotdeploy/health-check.sh

# End-to-end integration test
python simple_test.py

# Performance testing
python -m pytest tests/test_performance.py --benchmark-only
```

### Comprehensive Test Suite
```bash
# Run all tests
python -m pytest tests/ -v --cov=connectors

# Test specific components
python -m pytest tests/test_connector.py -v
python -m pytest tests/test_parsers.py -v
python -m pytest tests/test_security.py -v
```

---

## 🔧 Troubleshooting

### Common Issues

#### Installation Issues
```bash
# Fix dependency conflicts
pip install --upgrade --force-reinstall openmetadata-ingestion==1.8.1

# Clear Python cache
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} +

# Reinstall in development mode
pip uninstall openmetadata-s3-connector
pip install -e .
```

#### Connection Issues
```bash
# Test S3 connectivity
aws s3 ls s3://your-bucket-name/ --region us-east-1

# Verify IAM permissions
aws sts get-caller-identity

# Test OpenMetadata API
curl -H "Authorization: Bearer $OPENMETADATA_JWT_TOKEN" \
     "$OPENMETADATA_HOST_PORT/api/v1/services/databaseServices"
```

#### Manual Ingestion Issues
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Check script permissions
chmod +x scripts/*.sh

# Verify environment variables
source config/.env && env | grep -E "(AWS|OPENMETADATA)"
```

#### Hot Deployment Issues
```bash
# Check container status
docker ps -a | grep openmetadata

# Verify package installation in container
docker exec openmetadata_server python -c "import connectors.s3.s3_connector"

# Check container logs
docker logs openmetadata_server --tail=100
```

### Getting Help

1. **📖 Documentation**: Check our [comprehensive guides](docs/)
2. **🔧 Common Issues**: Visit [troubleshooting guide](docs/user-guides/troubleshooting.md)
3. **🔍 Debug Mode**: Enable debug logging with `export LOG_LEVEL=DEBUG`
4. **💬 Support**: Create an issue on GitHub or contact [mfonsau@talentys.eu](mailto:mfonsau@talentys.eu)

---

## 📚 Next Steps

### After Installation
1. **[📖 Manual Ingestion Guide](docs/MANUAL_INGESTION.md)** - Complete RBAC/IAM setup
2. **[🔒 Security Checklist](docs/SECURITY_CHECKLIST.md)** - Production security validation
3. **[⚙️ Configuration Guide](docs/user-guides/configuration.md)** - Advanced configuration options
4. **[🚀 Deployment Guide](docs/deployment/deployment-guide.md)** - Production deployment best practices

### Advanced Features
- **[🗂️ Hierarchical Folders](docs/reference/hierarchical-folders.md)** - Complex folder structures
- **[📊 Supported Formats](docs/reference/supported-formats.md)** - All supported file types
- **[🔐 Security & Authentication](docs/reference/security-authentication.md)** - Enterprise security
- **[🧩 Architecture Overview](docs/developer-guides/architecture.md)** - System design details

---

*🚀 **Installation complete!** Your OpenMetadata S3/MinIO Connector is ready for production use with enterprise-grade security and manual ingestion capabilities.*
