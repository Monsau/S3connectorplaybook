#!/bin/bash
set -e

echo "🚀 Installing OpenMetadata S3 Connector..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
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

# Check if running inside OpenMetadata container
if ! command -v python &> /dev/null; then
    print_error "Python not found. Are you running inside the OpenMetadata container?"
    exit 1
fi

# Update pip to latest version
print_status "Updating pip..."
pip install --upgrade pip setuptools wheel

# Install the S3 connector
print_status "Installing OpenMetadata S3 Connector..."
if pip install openmetadata-s3-connector; then
    print_success "S3 Connector package installed successfully"
else
    print_error "Failed to install S3 Connector package"
    exit 1
fi

# Verify installation
print_status "Verifying installation..."
if pip show openmetadata-s3-connector > /dev/null 2>&1; then
    print_success "Package verification successful"
    pip show openmetadata-s3-connector | head -10
else
    print_error "Package verification failed"
    exit 1
fi

# Create directories for assets
print_status "Setting up directories..."
mkdir -p /opt/openmetadata/static/assets/connectors/s3/
mkdir -p /opt/openmetadata/conf/connectors/

# Copy icon assets to OpenMetadata static directory
print_status "Installing connector icons..."
python -c "
import pkg_resources
import shutil
import os

try:
    # Find the installed package
    dist = pkg_resources.get_distribution('openmetadata-s3-connector')
    print(f'Package location: {dist.location}')
    
    # Look for assets in the package
    assets_paths = [
        os.path.join(dist.location, 'assets'),
        os.path.join(dist.location, 'openmetadata_s3_connector', 'assets'),
        os.path.join(dist.location, 'om_s3_connector', 'assets')
    ]
    
    assets_found = False
    for assets_path in assets_paths:
        if os.path.exists(assets_path):
            print(f'Found assets at: {assets_path}')
            
            # Copy icons
            icons_src = os.path.join(assets_path, 'icons')
            icons_dst = '/opt/openmetadata/static/assets/connectors/s3/'
            
            if os.path.exists(icons_src):
                shutil.copytree(icons_src, icons_dst, dirs_exist_ok=True)
                print('✅ Icons copied successfully')
                assets_found = True
                break
    
    if not assets_found:
        print('⚠️  No assets found in package - icons will need to be copied manually')
        
except Exception as e:
    print(f'⚠️  Error handling assets: {e}')
"

# Create connector configuration
print_status "Creating connector configuration..."
cat > /opt/openmetadata/conf/connectors/s3-connector.json << 'EOF'
{
  "name": "s3-connector",
  "displayName": "S3/MinIO Connector",
  "description": "Enterprise-grade metadata connector for S3-compatible storage systems",
  "serviceType": "Database",
  "connectorType": "Storage",
  "python_module": "om_s3_connector.core.s3_connector",
  "className": "S3Source",
  "iconPath": "assets/connectors/s3/s3-connector-icon.svg",
  "version": "0.9",
  "author": "Mustapha Fonsau",
  "license": "MIT"
}
EOF

print_success "Connector configuration created"

# Test connector import
print_status "Testing connector import..."
python -c "
try:
    from om_s3_connector.core.s3_connector import S3Source
    print('✅ S3Source class imported successfully')
    
    # Check if it's properly inheriting from OpenMetadata Source
    from openmetadata_ingestion.source.source import Source
    if issubclass(S3Source, Source):
        print('✅ S3Source properly inherits from OpenMetadata Source')
    else:
        print('⚠️  S3Source inheritance check failed')
        
except ImportError as e:
    print(f'❌ Import failed: {e}')
    exit(1)
except Exception as e:
    print(f'⚠️  Warning during import test: {e}')
"

# Check OpenMetadata ingestion CLI
print_status "Checking OpenMetadata ingestion CLI..."
if command -v metadata &> /dev/null; then
    print_success "OpenMetadata CLI available"
    metadata --version
else
    print_warning "OpenMetadata CLI not found in PATH"
fi

# List all installed connectors
print_status "Listing available connectors..."
python -c "
try:
    import pkg_resources
    print('Available OpenMetadata connectors:')
    for ep in pkg_resources.iter_entry_points('openmetadata_sources'):
        print(f'  - {ep.name} -> {ep.module_name}')
except Exception as e:
    print(f'Could not list connectors: {e}')
"

# Check if OpenMetadata service needs restart
print_status "Checking service status..."
if command -v supervisorctl &> /dev/null; then
    if supervisorctl status openmetadata | grep -q RUNNING; then
        print_status "Restarting OpenMetadata service..."
        supervisorctl restart openmetadata
        print_success "OpenMetadata service restarted"
    else
        print_warning "OpenMetadata service not running via supervisorctl"
    fi
elif systemctl is-active --quiet openmetadata 2>/dev/null; then
    print_status "Restarting OpenMetadata systemd service..."
    systemctl restart openmetadata
    print_success "OpenMetadata service restarted"
else
    print_warning "Could not detect service manager. Please restart OpenMetadata manually."
fi

# Final verification
print_status "Performing final verification..."
sleep 5

# Check if OpenMetadata API is responding
if command -v curl &> /dev/null; then
    if curl -f http://localhost:8585/api/v1/health > /dev/null 2>&1; then
        print_success "OpenMetadata API is responding"
    else
        print_warning "OpenMetadata API not responding yet (may need more time)"
    fi
else
    print_warning "curl not available for API health check"
fi

print_success "🎉 S3 Connector installation completed successfully!"
echo ""
echo "📝 Next Steps:"
echo "1. Access OpenMetadata UI at http://localhost:8585"
echo "2. Navigate to Settings > Services > Databases"
echo "3. Click 'Add New Service' and select 'S3/MinIO Connector'"
echo "4. Configure your S3 connection details"
echo ""
echo "📚 Documentation: /opt/openmetadata/docs/s3-connector/"
echo "🔧 Configuration: /opt/openmetadata/conf/connectors/s3-connector.json"
echo "🎨 Icons: /opt/openmetadata/static/assets/connectors/s3/"
echo ""
print_success "Happy metadata ingesting! 🚀"
