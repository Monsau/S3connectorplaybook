# Quick Start Commands for OpenMetadata Docker Hot Deploy

## 🚀 One-Command Deployment

### Deploy S3 Connector to Running Container
```bash
# If you have OpenMetadata already running
./deployment/docker-hotdeploy/hot-deploy.sh

# Or specify custom container name
./deployment/docker-hotdeploy/hot-deploy.sh my-openmetadata-container
```

### Deploy with Docker Compose (Full Stack)
```bash
cd deployment/docker-hotdeploy/
docker-compose up -d
```

### Deploy with Hot Deploy Service
```bash
cd deployment/docker-hotdeploy/
docker-compose --profile hot-deploy up -d
```

## 🔧 Manual Installation Commands

### Direct Container Installation
```bash
# 1. Find your OpenMetadata container
docker ps | grep openmetadata

# 2. Copy installation script
docker cp deployment/docker-hotdeploy/install-connector.sh openmetadata-server:/tmp/

# 3. Execute installation
docker exec -it openmetadata-server bash /tmp/install-connector.sh
```

### Local Package Installation
```bash
# 1. Build package
python setup.py sdist bdist_wheel

# 2. Copy to container
docker cp dist/openmetadata-s3-connector-*.whl openmetadata-server:/tmp/

# 3. Install in container
docker exec -it openmetadata-server pip install /tmp/openmetadata-s3-connector-*.whl

# 4. Restart service
docker exec -it openmetadata-server supervisorctl restart openmetadata
```

## 🔍 Verification Commands

### Check Installation
```bash
./deployment/docker-hotdeploy/health-check.sh
```

### Manual Verification
```bash
# Check package
docker exec openmetadata-server pip show openmetadata-s3-connector

# Test import
docker exec openmetadata-server python -c "from om_s3_connector.core.s3_connector import S3Source; print('✅ Import successful')"

# Check API
curl http://localhost:8585/api/v1/health
```

## 🐳 Docker Compose Commands

### Start with S3 Connector
```bash
cd deployment/docker-hotdeploy/
docker-compose up -d
```

### Hot Deploy to Running Stack
```bash
cd deployment/docker-hotdeploy/
docker-compose exec openmetadata-server pip install openmetadata-s3-connector
docker-compose restart openmetadata-server
```

### View Logs
```bash
docker-compose logs -f openmetadata-server
```

### Restart Services
```bash
docker-compose restart openmetadata-server
```

### Cleanup
```bash
docker-compose down -v
```

## 🔄 Update Commands

### Update Connector
```bash
# Rebuild and redeploy
./deployment/docker-hotdeploy/hot-deploy.sh
```

### Update with New Version
```bash
# Install specific version
docker exec openmetadata-server pip install openmetadata-s3-connector==2.0.1
docker exec openmetadata-server supervisorctl restart openmetadata
```

## 🚨 Troubleshooting Commands

### Reset Installation
```bash
# Uninstall and reinstall
docker exec openmetadata-server pip uninstall -y openmetadata-s3-connector
./deployment/docker-hotdeploy/hot-deploy.sh
```

### Check Logs
```bash
# OpenMetadata logs
docker logs -f openmetadata-server

# Installation logs
docker exec openmetadata-server tail -f /opt/openmetadata/logs/openmetadata.log
```

### Debug Mode
```bash
# Enter container for debugging
docker exec -it openmetadata-server bash

# Check Python path
python -c "import sys; print('\n'.join(sys.path))"

# List installed packages
pip list | grep -i openmetadata
```

## 📊 Monitoring Commands

### Health Check
```bash
# Full health check
./deployment/docker-hotdeploy/health-check.sh

# Quick API check
curl -f http://localhost:8585/api/v1/health
```

### Resource Usage
```bash
# Container stats
docker stats openmetadata-server

# Disk usage
docker exec openmetadata-server df -h

# Memory usage
docker exec openmetadata-server free -h
```

## 🎯 Configuration Commands

### Test Configuration
```bash
# Validate connector config
docker exec openmetadata-server python -c "
import yaml
with open('/opt/openmetadata/conf/connectors/s3-connector.json') as f:
    config = yaml.safe_load(f)
    print('✅ Configuration is valid')
"
```

### Update Configuration
```bash
# Copy new config
docker cp config/s3-connector-with-icon.yaml openmetadata-server:/opt/openmetadata/conf/

# Restart to apply changes
docker exec openmetadata-server supervisorctl restart openmetadata
```

---

**📚 Full Documentation**: [deployment/docker-hotdeploy/README.md](README.md)
**🔧 Troubleshooting**: Run `./deployment/docker-hotdeploy/health-check.sh`
**📧 Support**: [mfonsau@talentys.eu](mailto:mfonsau@talentys.eu)
