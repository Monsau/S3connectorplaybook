# 🐳 OpenMetadata Docker Hot Deployment Guide

Deploy the S3 connector to an existing OpenMetadata Docker container without rebuilding the image.

## 🎯 Overview

This approach allows you to:
- ✅ Install the connector in a running OpenMetadata container
- ✅ Avoid image rebuilds and lengthy deployment cycles
- ✅ Test quickly in development and staging environments
- ✅ Deploy updates without downtime

## 📋 Prerequisites

- OpenMetadata Docker container running
- Docker access (docker exec permissions)
- Network access to PyPI or local package repository
- OpenMetadata admin credentials

## 🚀 Quick Deployment

### Method 1: Direct pip install from PyPI

```bash
# 1. Access the OpenMetadata container
docker exec -it openmetadata-server bash

# 2. Install the S3 connector
pip install openmetadata-s3-connector

# 3. Restart OpenMetadata service
supervisorctl restart openmetadata
```

### Method 2: Install from local package

```bash
# 1. Build the package locally
python setup.py sdist bdist_wheel

# 2. Copy package to container
docker cp dist/openmetadata-s3-connector-*.whl openmetadata-server:/tmp/

# 3. Install in container
docker exec -it openmetadata-server bash
pip install /tmp/openmetadata-s3-connector-*.whl

# 4. Restart service
supervisorctl restart openmetadata
```

### Method 3: Mount source code (Development)

```bash
# 1. Mount source directory
docker run -v $(pwd):/workspace/s3-connector \
  -it openmetadata/server bash

# 2. Install in development mode
cd /workspace/s3-connector
pip install -e .

# 3. Restart OpenMetadata
supervisorctl restart openmetadata
```

## 🔧 Detailed Installation Steps

### Step 1: Prepare the Package

```bash
# Build distribution packages
python setup.py sdist bdist_wheel

# Verify package contents
tar -tzf dist/openmetadata-s3-connector-*.tar.gz | head -20

# Check wheel contents
unzip -l dist/openmetadata-s3-connector-*.whl | head -20
```

### Step 2: Container Access and Installation

```bash
# Get container ID
CONTAINER_ID=$(docker ps --filter "name=openmetadata" --format "{{.ID}}")
echo "OpenMetadata Container: $CONTAINER_ID"

# Copy installation script
docker cp deployment/docker-hotdeploy/install-connector.sh $CONTAINER_ID:/tmp/

# Execute installation
docker exec -it $CONTAINER_ID bash /tmp/install-connector.sh
```

### Step 3: Verify Installation

```bash
# Check installed packages
docker exec -it openmetadata-server pip list | grep openmetadata

# Verify connector files
docker exec -it openmetadata-server find /opt/openmetadata -name "*s3*connector*"

# Check OpenMetadata logs
docker logs openmetadata-server --tail 50
```

## 📁 Installation Script

Create `install-connector.sh`:

```bash
#!/bin/bash
set -e

echo "🚀 Installing OpenMetadata S3 Connector..."

# Update pip
pip install --upgrade pip

# Install the connector
pip install openmetadata-s3-connector

# Verify installation
echo "📦 Installed packages:"
pip show openmetadata-s3-connector

# Copy icon assets to OpenMetadata static directory
echo "🎨 Installing icons..."
mkdir -p /opt/openmetadata/static/assets/connectors/s3/
cp -r /usr/local/lib/python*/site-packages/assets/icons/* \
    /opt/openmetadata/static/assets/connectors/s3/ 2>/dev/null || true

# Update connector registry
echo "🔧 Updating connector registry..."
cat > /tmp/s3-connector-config.json << 'EOF'
{
  "name": "s3-connector",
  "displayName": "S3/MinIO Connector", 
  "serviceType": "Database",
  "connectorType": "Storage",
  "python_module": "om_s3_connector.core.s3_connector",
  "className": "S3Source",
  "iconPath": "assets/connectors/s3/s3-connector-icon.svg"
}
EOF

# Restart OpenMetadata service
echo "🔄 Restarting OpenMetadata service..."
if command -v supervisorctl &> /dev/null; then
    supervisorctl restart openmetadata
elif systemctl is-active --quiet openmetadata; then
    systemctl restart openmetadata
else
    echo "⚠️  Please restart OpenMetadata service manually"
fi

echo "✅ S3 Connector installation completed!"
echo "🌐 Access OpenMetadata UI to configure the connector"
```

## 🐳 Docker Compose Integration

### Update existing docker-compose.yml

```yaml
version: '3.8'

services:
  openmetadata-server:
    image: openmetadata/server:latest
    # ... existing configuration ...
    
    # Add volume for hot-deployed connectors
    volumes:
      - ./connectors:/opt/openmetadata/connectors
      - ./config:/opt/openmetadata/config
      - connector-data:/var/openmetadata
    
    # Environment variables for S3 connector
    environment:
      - CONNECTOR_S3_ENABLED=true
      - CONNECTOR_S3_MODULE=om_s3_connector.core.s3_connector
      - CONNECTOR_S3_CLASS=S3Source
    
    # Install script on startup
    command: >
      bash -c "
        pip install openmetadata-s3-connector &&
        python -m openmetadata_ingestion.core.cli --version &&
        /opt/openmetadata/bin/openmetadata-server-start.sh
      "

volumes:
  connector-data:
```

### Hot-deploy script for Docker Compose

```bash
#!/bin/bash
# hot-deploy.sh

set -e

echo "🔥 Hot-deploying S3 connector to OpenMetadata..."

# Build the package
echo "📦 Building package..."
python setup.py sdist bdist_wheel

# Get the service name
SERVICE_NAME="openmetadata-server"

# Copy package to container
echo "📁 Copying package to container..."
docker-compose exec $SERVICE_NAME mkdir -p /tmp/connector-install
docker cp dist/ ${SERVICE_NAME}:/tmp/connector-install/

# Install in container
echo "⚙️  Installing connector..."
docker-compose exec $SERVICE_NAME bash -c "
    cd /tmp/connector-install/dist &&
    pip install openmetadata-s3-connector-*.whl &&
    echo '✅ Connector installed successfully'
"

# Copy assets
echo "🎨 Installing assets..."
docker-compose exec $SERVICE_NAME bash -c "
    mkdir -p /opt/openmetadata/static/assets/connectors/s3/ &&
    python -c '
import pkg_resources
import shutil
import os

try:
    # Find the installed package
    dist = pkg_resources.get_distribution(\"openmetadata-s3-connector\")
    assets_path = os.path.join(dist.location, \"assets\")
    
    if os.path.exists(assets_path):
        shutil.copytree(assets_path, \"/opt/openmetadata/static/assets/connectors/s3/\", dirs_exist_ok=True)
        print(\"Assets copied successfully\")
    else:
        print(\"No assets found in package\")
except Exception as e:
    print(f\"Error copying assets: {e}\")
'
"

# Restart service
echo "🔄 Restarting OpenMetadata..."
docker-compose restart $SERVICE_NAME

# Wait for service to be ready
echo "⏳ Waiting for OpenMetadata to start..."
sleep 30

# Verify installation
echo "✅ Verifying installation..."
docker-compose exec $SERVICE_NAME bash -c "
    pip show openmetadata-s3-connector &&
    echo 'Connector verification completed'
"

echo "🎉 Hot deployment completed successfully!"
echo "🌐 OpenMetadata should now be available with S3 connector"
```

## 🔍 Verification and Testing

### Verify Connector Installation

```bash
# Check if connector is loaded
docker exec openmetadata-server python -c "
from openmetadata_ingestion.source.database.s3.metadata import S3Source
print('✅ S3 Connector loaded successfully')
"

# List available connectors
docker exec openmetadata-server python -c "
import pkg_resources
for ep in pkg_resources.iter_entry_points('openmetadata_sources'):
    print(f'Connector: {ep.name} -> {ep.module_name}:{ep.attrs[0]}')
"

# Check icon assets
docker exec openmetadata-server ls -la /opt/openmetadata/static/assets/connectors/s3/
```

### Test Connector Functionality

```bash
# Create test configuration
cat > test-s3-config.yaml << 'EOF'
source:
  type: s3
  serviceName: test-s3-service
  serviceConnection:
    config:
      type: S3
      awsConfig:
        awsRegion: us-west-2
        awsAccessKeyId: test-key
        awsSecretAccessKey: test-secret
      bucketName: test-bucket

sink:
  type: metadata-rest
  config: {}

workflowConfig:
  openMetadataServerConfig:
    hostPort: http://localhost:8585/api
    authProvider: openmetadata
    securityConfig:
      jwtToken: ${OM_JWT_TOKEN}
EOF

# Test configuration validation
docker exec openmetadata-server python -c "
import yaml
with open('/tmp/test-s3-config.yaml') as f:
    config = yaml.safe_load(f)
print('✅ Configuration is valid')
"
```

## 🚨 Troubleshooting

### Common Issues

1. **Permission Denied**:
   ```bash
   # Fix container permissions
   docker exec -u root openmetadata-server chown -R openmetadata:openmetadata /opt/openmetadata
   ```

2. **Module Not Found**:
   ```bash
   # Check Python path
   docker exec openmetadata-server python -c "import sys; print('\\n'.join(sys.path))"
   
   # Reinstall connector
   docker exec openmetadata-server pip uninstall -y openmetadata-s3-connector
   docker exec openmetadata-server pip install openmetadata-s3-connector
   ```

3. **Icons Not Appearing**:
   ```bash
   # Check asset permissions
   docker exec openmetadata-server ls -la /opt/openmetadata/static/assets/connectors/s3/
   
   # Copy assets manually
   docker cp assets/ openmetadata-server:/opt/openmetadata/static/assets/connectors/s3/
   ```

### Debug Mode

Enable debug logging:

```bash
# Enable debug logging
docker exec openmetadata-server bash -c "
    echo 'logging.level.org.openmetadata=DEBUG' >> /opt/openmetadata/conf/application.yml
"

# Restart with debug logs
docker-compose restart openmetadata-server

# Monitor logs
docker logs -f openmetadata-server | grep -i s3
```

## 📊 Monitoring Deployment

### Health Check Script

```bash
#!/bin/bash
# health-check.sh

echo "🔍 Checking S3 Connector Health..."

# Check service status
if docker exec openmetadata-server supervisorctl status openmetadata | grep -q RUNNING; then
    echo "✅ OpenMetadata service is running"
else
    echo "❌ OpenMetadata service is not running"
    exit 1
fi

# Check connector installation
if docker exec openmetadata-server pip show openmetadata-s3-connector > /dev/null 2>&1; then
    echo "✅ S3 Connector package is installed"
else
    echo "❌ S3 Connector package not found"
    exit 1
fi

# Check API availability
if docker exec openmetadata-server curl -f http://localhost:8585/api/v1/health > /dev/null 2>&1; then
    echo "✅ OpenMetadata API is accessible"
else
    echo "❌ OpenMetadata API is not accessible"
    exit 1
fi

# Check connector registration
CONNECTOR_CHECK=$(docker exec openmetadata-server curl -s http://localhost:8585/api/v1/services/databaseServices/name/s3-service 2>/dev/null || echo "not found")
if [[ "$CONNECTOR_CHECK" != "not found" ]]; then
    echo "✅ S3 Connector is registered"
else
    echo "ℹ️  S3 Connector not yet configured (this is normal for first deployment)"
fi

echo "🎉 Health check completed!"
```

## 🎯 Best Practices

### Development Workflow

1. **Local Testing**:
   ```bash
   # Test locally first
   pip install -e .
   python -m pytest tests/
   ```

2. **Package and Deploy**:
   ```bash
   # Build package
   python setup.py sdist bdist_wheel
   
   # Hot deploy
   ./deployment/docker-hotdeploy/hot-deploy.sh
   ```

3. **Verify and Test**:
   ```bash
   # Run health check
   ./deployment/docker-hotdeploy/health-check.sh
   
   # Test connector functionality
   python test-connector.py
   ```

### Production Considerations

- **Backup Configuration**: Always backup OpenMetadata configuration before deployment
- **Rolling Updates**: Use blue-green deployment for production
- **Monitoring**: Set up alerts for connector health
- **Rollback Plan**: Keep previous package versions for quick rollback

---

**🐳 Ready for Hot Deployment**: Your S3 connector can now be deployed to existing OpenMetadata Docker containers without image rebuilds!

**📧 Support**: [mfonsau@talentys.eu](mailto:mfonsau@talentys.eu)
