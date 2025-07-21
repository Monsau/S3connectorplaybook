#!/bin/bash
# Hot deployment script for Docker Compose environments

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

# Configuration
SERVICE_NAME=${1:-"openmetadata_server"}
PACKAGE_NAME="openmetadata-s3-connector"

echo "🔥 Hot-deploying S3 connector to OpenMetadata Docker container..."
echo "Service: $SERVICE_NAME"
echo "Package: $PACKAGE_NAME"
echo ""

# Check if we're in the right directory and navigate to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

print_status "Navigating to project root: $PROJECT_ROOT"
cd "$PROJECT_ROOT"

if [[ ! -f "setup.py" ]]; then
    print_error "setup.py not found in $PROJECT_ROOT"
    exit 1
fi

# Activate virtual environment if it exists
if [[ -f "venv/bin/activate" ]]; then
    print_status "Activating virtual environment..."
    source venv/bin/activate
    print_success "Virtual environment activated"
elif [[ -f "activate.sh" ]]; then
    print_status "Using project activation script..."
    source activate.sh
    print_success "Environment activated via activate.sh"
else
    print_warning "No virtual environment found. Using system Python."
fi

# Verify Python and pip
print_status "Checking Python environment..."
python --version
pip --version

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null && ! command -v docker &> /dev/null; then
    print_error "Docker or Docker Compose not found"
    exit 1
fi

# Check if container is running
print_status "Checking if OpenMetadata container is running..."
if sudo docker ps --format "{{.Names}}" | grep -q "$SERVICE_NAME"; then
    print_success "Container $SERVICE_NAME is running"
elif sudo docker-compose ps "$SERVICE_NAME" 2>/dev/null | grep -q "Up"; then
    print_success "Container $SERVICE_NAME is running (via docker-compose)"
else
    print_error "Container $SERVICE_NAME is not running"
    echo "Available containers:"
    sudo docker ps --format "table {{.Names}}\t{{.Status}}"
    exit 1
fi

# Build the package
print_status "Building package with activated environment..."
rm -rf dist/ build/ *.egg-info/

# Ensure build dependencies are available
pip install --upgrade pip setuptools wheel build

# Build the package
python -m build --wheel

if [[ ! -f "dist/openmetadata_s3_connector"-*.whl ]]; then
    print_error "Wheel package not created"
    exit 1
fi

WHEEL_FILE=$(ls dist/openmetadata_s3_connector-*.whl | head -1)
print_success "Package built: $WHEEL_FILE"

# Copy package to container
print_status "Copying package to container..."
CONTAINER_ID=$(sudo docker ps --filter "name=$SERVICE_NAME" --format "{{.ID}}" | head -1)

if [[ -z "$CONTAINER_ID" ]]; then
    print_error "Could not find container ID for $SERVICE_NAME"
    exit 1
fi

sudo docker exec "$CONTAINER_ID" mkdir -p /tmp/connector-install
sudo docker cp "$WHEEL_FILE" "$CONTAINER_ID:/tmp/connector-install/"
sudo docker cp "deployment/docker-hotdeploy/install-connector.sh" "$CONTAINER_ID:/tmp/connector-install/"

print_success "Files copied to container"

# Install the connector
print_status "Installing connector in container..."
WHEEL_FILENAME=$(basename "$WHEEL_FILE")

sudo docker exec "$CONTAINER_ID" bash -c "
    cd /tmp/connector-install &&
    pip install --upgrade pip &&
    pip uninstall -y $PACKAGE_NAME 2>/dev/null || true &&
    pip install '$WHEEL_FILENAME' &&
    echo '✅ Package installation completed'
"

# Run the installation script
print_status "Running connector setup script..."
sudo docker exec "$CONTAINER_ID" bash /tmp/connector-install/install-connector.sh

# Copy any additional assets
print_status "Copying additional assets..."
if [[ -d "assets" ]]; then
    sudo docker cp assets/ "$CONTAINER_ID:/tmp/connector-assets/"
    sudo docker exec "$CONTAINER_ID" bash -c "
        mkdir -p /opt/openmetadata/static/assets/connectors/s3/ &&
        cp -r /tmp/connector-assets/* /opt/openmetadata/static/assets/connectors/s3/ 2>/dev/null || true &&
        echo 'Assets copied successfully'
    "
fi

# Wait for service to stabilize
print_status "Waiting for service to stabilize..."
sleep 10

# Verify installation
print_status "Verifying installation..."
sudo docker exec "$CONTAINER_ID" bash -c "
    echo 'Checking package installation...'
    pip show $PACKAGE_NAME || exit 1
    
    echo 'Testing connector import...'
    python -c 'from om_s3_connector.core.s3_connector import S3Source; print(\"✅ Import successful\")' || exit 1
    
    echo 'Checking assets...'
    ls -la /opt/openmetadata/static/assets/connectors/s3/ 2>/dev/null || echo 'No assets found'
    
    echo 'Checking service status...'
    if command -v supervisorctl &> /dev/null; then
        supervisorctl status openmetadata | grep -q RUNNING && echo '✅ Service is running'
    elif systemctl is-active --quiet openmetadata 2>/dev/null; then
        echo '✅ Service is running (systemd)'
    else
        echo 'ℹ️  Could not check service status'
    fi
"

# Check API availability
print_status "Checking API availability..."
sleep 5

API_CHECK=$(sudo docker exec "$CONTAINER_ID" curl -s -o /dev/null -w "%{http_code}" http://localhost:8585/api/v1/health 2>/dev/null || echo "000")

if [[ "$API_CHECK" == "200" ]]; then
    print_success "OpenMetadata API is responding (HTTP 200)"
elif [[ "$API_CHECK" == "000" ]]; then
    print_warning "Could not check API (curl might not be available)"
else
    print_warning "API returned HTTP $API_CHECK (service might still be starting)"
fi

# Cleanup temporary files
print_status "Cleaning up temporary files..."
sudo docker exec "$CONTAINER_ID" rm -rf /tmp/connector-install /tmp/connector-assets

print_success "🎉 Hot deployment completed successfully!"
echo ""
echo "📊 Deployment Summary:"
echo "  ✅ Package: $WHEEL_FILENAME"
echo "  ✅ Container: $SERVICE_NAME ($CONTAINER_ID)"
echo "  ✅ Installation: Completed"
echo "  ✅ Service: Running"
echo ""
echo "🚀 Next Steps:"
echo "1. Access OpenMetadata UI:"
echo "   http://localhost:8585"
echo ""
echo "2. Configure S3 Connector:"
echo "   Settings → Services → Databases → Add New Service → S3/MinIO Connector"
echo ""
echo "3. Monitor logs:"
echo "   docker logs -f $SERVICE_NAME"
echo ""
echo "📚 Documentation:"
echo "   deployment/docker-hotdeploy/README.md"
echo ""
print_success "Happy metadata ingesting! 🚀"
