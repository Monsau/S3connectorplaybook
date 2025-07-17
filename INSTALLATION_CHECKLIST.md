# 📋 OpenMetadata S3/MinIO Connector - Installation Checklist

## 🎯 Pre-Installation Checklist

### Environment Assessment
- [ ] **Python 3.8+** installed (`python --version`)
- [ ] **pip** package manager available (`pip --version`)
- [ ] **Git** installed (`git --version`)
- [ ] **Network access** to S3/MinIO storage
- [ ] **Network access** to OpenMetadata instance
- [ ] **Docker access** (if using hot deployment)

### Credentials & Access
- [ ] **S3 Credentials** ready (Access Key/Secret or IAM role)
- [ ] **S3 Bucket** exists and accessible
- [ ] **OpenMetadata** instance running
- [ ] **OpenMetadata API** credentials (JWT token, etc.)
- [ ] **Permissions** verified for all components

---

## 🔧 Installation Steps Checklist

### Step 1: Repository Setup
- [ ] `git clone https://github.com/Monsau/S3connectorplaybook.git`
- [ ] `cd S3connectorplaybook`
- [ ] Verify structure: `ls -la` (config/, scripts/, docs/ present)

### Step 2: Dependencies
- [ ] `pip install --upgrade pip setuptools`
- [ ] `pip install "openmetadata-ingestion==1.8.1"`
- [ ] `pip install -r requirements.txt`
- [ ] `pip install -e .`
- [ ] Test import: `python -c "import connectors.s3.s3_connector; print('✅ Success')"`

### Step 3: Configuration Selection

**Choose ONE installation type:**

#### Option A: Basic Development (5 min)
- [ ] `cp config/ingestion.yaml config/my-config.yaml`
- [ ] Edit `my-config.yaml` with S3 and OpenMetadata settings
- [ ] Test: `export PYTHONPATH=$(pwd) && metadata ingest -c config/my-config.yaml --dry-run`

#### Option B: Manual Ingestion Enterprise (15 min)
- [ ] `cp config/.env.example config/.env`
- [ ] `cp config/manual-s3-ingestion.yaml config/my-config.yaml`
- [ ] Edit `.env` with credentials
- [ ] Edit `my-config.yaml` for your environment
- [ ] `chmod +x scripts/*.sh`
- [ ] Test: `./scripts/test-s3-connection.sh`
- [ ] Test: `./scripts/test-rbac-security.sh`

#### Option C: Hot Deployment (10 min)
- [ ] Verify containers: `docker ps | grep openmetadata`
- [ ] `./deployment/docker-hotdeploy/hot-deploy.sh`
- [ ] Verify: `./deployment/docker-hotdeploy/health-check.sh`

#### Option D: Production (30+ min)
- [ ] `cp config/prod-s3-ingestion-rbac.yaml config/production.yaml`
- [ ] Configure advanced RBAC, IAM, and compliance settings
- [ ] Complete security validation
- [ ] Run production deployment

---

## ✅ Verification Checklist

### Basic Functionality
- [ ] **Import Test**: `python -c "import connectors.s3.s3_connector"`
- [ ] **Parser Test**: `python validate_parsers.py`
- [ ] **Format Test**: `python test_additional_formats.py`

### Connectivity Tests
- [ ] **S3 Connection**: `./scripts/test-s3-connection.sh`
- [ ] **OpenMetadata API**: `curl $OPENMETADATA_HOST_PORT/api/v1/system/version`

### Security Tests (Production Only)
- [ ] **RBAC Validation**: `./scripts/test-rbac-security.sh`
- [ ] **IAM Permission**: Verify cross-account access
- [ ] **SSL/TLS**: Verify encrypted connections
- [ ] **Audit Logs**: Check log generation

### Functional Tests
- [ ] **Basic Ingestion**: Run with small dataset
- [ ] **Schema Detection**: Verify schema inference
- [ ] **Metadata Visibility**: Check OpenMetadata UI
- [ ] **Performance**: Monitor resource usage

---

## 🚨 Troubleshooting Quick Fixes

### Installation Issues
- [ ] **Dependency Conflicts**: `pip install --upgrade --force-reinstall openmetadata-ingestion==1.8.1`
- [ ] **Python Cache**: `find . -name "*.pyc" -delete && find . -name "__pycache__" -type d -exec rm -rf {} +`
- [ ] **Package Issues**: `pip uninstall openmetadata-s3-connector && pip install -e .`

### Connection Issues
- [ ] **S3 Access**: `aws s3 ls s3://your-bucket/ --region us-east-1`
- [ ] **IAM Identity**: `aws sts get-caller-identity`
- [ ] **Network**: `ping your-openmetadata-host`
- [ ] **Credentials**: Verify all environment variables are set

### Configuration Issues
- [ ] **YAML Syntax**: `python -c "import yaml; yaml.safe_load(open('config/my-config.yaml'))"`
- [ ] **Environment Variables**: `source config/.env && env | grep -E "(AWS|OPENMETADATA)"`
- [ ] **Permissions**: `chmod +x scripts/*.sh`

---

## 📊 Success Criteria

### Installation Complete When:
- [ ] ✅ All imports work without errors
- [ ] ✅ Test scripts pass successfully
- [ ] ✅ Configuration validates correctly
- [ ] ✅ Connectivity tests succeed
- [ ] ✅ Sample ingestion completes
- [ ] ✅ Metadata appears in OpenMetadata UI

### Production Ready When:
- [ ] ✅ Security validation passes
- [ ] ✅ RBAC configuration verified
- [ ] ✅ Performance requirements met
- [ ] ✅ Monitoring configured
- [ ] ✅ Backup procedures tested
- [ ] ✅ Documentation updated

---

## 🎯 Quick Command Reference

### Essential Commands

**Basic Installation:**
```bash
git clone https://github.com/Monsau/S3connectorplaybook.git
cd S3connectorplaybook
pip install -r requirements.txt && pip install -e .
cp config/ingestion.yaml config/my-config.yaml
# Edit my-config.yaml, then:
export PYTHONPATH=$(pwd)
metadata ingest -c config/my-config.yaml
```

**Manual Ingestion:**
```bash
cp config/.env.example config/.env  # Edit with credentials
chmod +x scripts/*.sh
./scripts/test-s3-connection.sh
./scripts/run-manual-ingestion.sh config/manual-s3-ingestion.yaml
```

**Hot Deployment:**
```bash
./deployment/docker-hotdeploy/hot-deploy.sh
./deployment/docker-hotdeploy/health-check.sh
```

**Verification:**
```bash
python -c "import connectors.s3.s3_connector; print('✅ Ready')"
python validate_parsers.py
./scripts/test-s3-connection.sh
```

---

## 📚 Documentation Links

- **[Complete Installation Guide](INSTALLATION.md)** - Detailed instructions for all scenarios
- **[Manual Ingestion Guide](docs/MANUAL_INGESTION.md)** - Enterprise RBAC setup
- **[Security Checklist](docs/SECURITY_CHECKLIST.md)** - Production security validation
- **[Configuration Examples](config/)** - Ready-to-use templates
- **[Troubleshooting Guide](docs/user-guides/troubleshooting.md)** - Common issues and solutions

---

**💡 Pro Tip**: Print this checklist and check off items as you complete them. If any step fails, refer to the troubleshooting section before proceeding to the next step.
