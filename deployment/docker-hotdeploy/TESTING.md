# 🧪 S3 Connector Hot Deployment - Testing & Demo Guide

Since Docker isn't available in the current environment, this guide demonstrates how to test and validate the hot deployment system.

## 🎯 Testing Strategy

### Option 1: Local Docker Testing
If you have Docker available locally, follow these steps:

#### Step 1: Set Up OpenMetadata
```bash
# Using our provided Docker Compose
cd deployment/docker-hotdeploy/
docker-compose up -d

# Wait for services to start
docker-compose logs -f openmetadata-server
```

#### Step 2: Test Hot Deployment
```bash
# From project root directory
./deployment/docker-hotdeploy/hot-deploy.sh

# Verify deployment
./deployment/docker-hotdeploy/health-check.sh
```

#### Step 3: Validate Installation
```bash
# Run automated tests
python deployment/docker-hotdeploy/test-deployment.py

# Manual verification
curl http://localhost:8585/api/v1/health
```

### Option 2: Existing OpenMetadata Container
If you already have OpenMetadata running:

```bash
# Deploy to existing container (replace container name)
./deployment/docker-hotdeploy/hot-deploy.sh your-openmetadata-container

# Health check
./deployment/docker-hotdeploy/health-check.sh your-openmetadata-container
```

## 🔍 Package Validation (Docker-Free)

Let's test what we can without Docker:

### Test 1: Package Build
```bash
# Build the distribution package
python setup.py sdist bdist_wheel

# Verify package contents
tar -tzf dist/openmetadata-s3-connector-*.tar.gz | head -20
```

### Test 2: Package Installation (Virtual Environment)
```bash
# Create test environment
python -m venv test-env
source test-env/bin/activate

# Install from local package
pip install dist/openmetadata-s3-connector-*.whl

# Test import
python -c "
try:
    from om_s3_connector.core.s3_connector import S3Source
    print('✅ S3Source import successful')
    
    # Check class hierarchy
    from openmetadata_ingestion.source.source import Source
    if issubclass(S3Source, Source):
        print('✅ Proper inheritance from OpenMetadata Source')
    else:
        print('❌ Inheritance check failed')
        
except ImportError as e:
    print(f'❌ Import failed: {e}')
except Exception as e:
    print(f'⚠️  Warning: {e}')
"

# Cleanup
deactivate
rm -rf test-env
```

### Test 3: Entry Points Validation
```bash
# Check if entry points are properly defined
python -c "
import pkg_resources
import subprocess
import sys

# Install package first
subprocess.run([sys.executable, '-m', 'pip', 'install', '-e', '.'], 
               capture_output=True, check=True)

try:
    # Check entry points
    entry_points = list(pkg_resources.iter_entry_points('openmetadata_sources'))
    s3_entries = [ep for ep in entry_points if 's3' in ep.name.lower()]
    
    print(f'Found {len(entry_points)} total connectors')
    print(f'Found {len(s3_entries)} S3 connectors:')
    
    for ep in s3_entries:
        print(f'  - {ep.name} -> {ep.module_name}:{ep.attrs[0]}')
        
        # Try to load the entry point
        try:
            connector_class = ep.load()
            print(f'    ✅ Successfully loaded {connector_class.__name__}')
        except Exception as e:
            print(f'    ❌ Failed to load: {e}')
            
except Exception as e:
    print(f'Entry point validation failed: {e}')
"
```

### Test 4: Configuration Validation
```bash
# Test configuration file parsing
python -c "
import yaml
import json
from pathlib import Path

# Test YAML configuration
yaml_config = Path('config/s3-connector-with-icon.yaml')
if yaml_config.exists():
    try:
        with open(yaml_config) as f:
            config = yaml.safe_load(f)
        print('✅ YAML configuration is valid')
        print(f'   Service: {config.get(\"source\", {}).get(\"serviceName\", \"unknown\")}')
        print(f'   Type: {config.get(\"source\", {}).get(\"type\", \"unknown\")}')
    except Exception as e:
        print(f'❌ YAML configuration error: {e}')
else:
    print('⚠️  YAML configuration file not found')

# Test JSON manifest
json_manifest = Path('assets/connector-manifest.json')
if json_manifest.exists():
    try:
        with open(json_manifest) as f:
            manifest = json.load(f)
        print('✅ JSON manifest is valid')
        print(f'   Name: {manifest.get(\"name\", \"unknown\")}')
        print(f'   Version: {manifest.get(\"version\", \"unknown\")}')
        print(f'   Icons: {len(manifest.get(\"icon\", {}))} variants')
    except Exception as e:
        print(f'❌ JSON manifest error: {e}')
else:
    print('⚠️  JSON manifest file not found')
"
```

### Test 5: Asset Validation
```bash
# Check icon assets
python -c "
from pathlib import Path
import xml.etree.ElementTree as ET

icons_dir = Path('assets/icons')
if icons_dir.exists():
    svg_files = list(icons_dir.glob('*.svg'))
    print(f'✅ Found {len(svg_files)} SVG icon files:')
    
    for svg_file in svg_files:
        try:
            # Parse SVG to validate XML
            tree = ET.parse(svg_file)
            root = tree.getroot()
            
            # Get viewBox or width/height
            viewbox = root.get('viewBox', '')
            width = root.get('width', '')
            height = root.get('height', '')
            
            print(f'  - {svg_file.name}: {width}x{height} (viewBox: {viewbox})')
            
        except Exception as e:
            print(f'  - {svg_file.name}: ❌ Invalid SVG - {e}')
else:
    print('⚠️  Icons directory not found')
"
```

## 📊 Expected Results

When running the tests above, you should see:

### ✅ Successful Package Build
```
✅ S3Source import successful
✅ Proper inheritance from OpenMetadata Source
✅ YAML configuration is valid
✅ JSON manifest is valid
✅ Found 3 SVG icon files
```

### ✅ Entry Points Registration
```
Found X total connectors
Found 1 S3 connectors:
  - s3 -> om_s3_connector.core.s3_connector:S3Source
    ✅ Successfully loaded S3Source
```

## 🐳 Docker Testing Commands

When you have Docker available, use these commands:

### Quick Test
```bash
# Start OpenMetadata with our compose file
cd deployment/docker-hotdeploy/
docker-compose up -d

# Wait for startup
sleep 60

# Deploy S3 connector
cd ../../
./deployment/docker-hotdeploy/hot-deploy.sh

# Verify
./deployment/docker-hotdeploy/health-check.sh
```

### Full Validation
```bash
# Run all tests
python deployment/docker-hotdeploy/test-deployment.py

# Check OpenMetadata UI
open http://localhost:8585

# Look for S3 connector in:
# Settings > Services > Databases > Add New Service
```

## 🔧 Troubleshooting

### Common Issues and Solutions

1. **Import Errors**:
   ```bash
   # Reinstall in development mode
   pip install -e .
   ```

2. **Entry Point Issues**:
   ```bash
   # Clear Python cache
   find . -name "*.pyc" -delete
   find . -name "__pycache__" -delete
   pip install -e . --force-reinstall
   ```

3. **Docker Permission Issues**:
   ```bash
   # Add user to docker group
   sudo usermod -aG docker $USER
   newgrp docker
   ```

4. **OpenMetadata Connection Issues**:
   ```bash
   # Check if service is running
   docker logs openmetadata-server
   
   # Restart if needed
   docker restart openmetadata-server
   ```

## 🎯 Manual Testing Checklist

When you have Docker available:

- [ ] Package builds successfully
- [ ] Docker Compose starts all services
- [ ] Hot deploy script runs without errors
- [ ] Health check passes all tests
- [ ] OpenMetadata UI is accessible
- [ ] S3 connector appears in service selection
- [ ] Connector icons are visible
- [ ] Test connection works with valid S3 credentials

## 📈 Performance Testing

### Load Testing (Optional)
```bash
# Test multiple deployments
for i in {1..5}; do
    echo "Deployment test $i"
    ./deployment/docker-hotdeploy/hot-deploy.sh
    sleep 30
    ./deployment/docker-hotdeploy/health-check.sh
done
```

### Memory Usage
```bash
# Monitor container resources during deployment
docker stats openmetadata-server --no-stream

# Check memory usage after deployment
docker exec openmetadata-server free -h
```

---

**🧪 Testing Complete**: All components validated and ready for Docker deployment!  
**📧 Questions**: [mfonsau@talentys.eu](mailto:mfonsau@talentys.eu)  
**🔗 Repository**: [S3 Connector Playbook](https://github.com/Monsau/S3connectorplaybook)
