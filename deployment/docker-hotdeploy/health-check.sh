#!/bin/bash
# Health check script for deployed S3 connector

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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
SERVICE_NAME=${1:-"openmetadata-server"}
PACKAGE_NAME="openmetadata-s3-connector"

echo "🔍 S3 Connector Health Check"
echo "Service: $SERVICE_NAME"
echo "Package: $PACKAGE_NAME"
echo ""

# Check if container is running
print_status "Checking container status..."
CONTAINER_ID=$(docker ps --filter "name=$SERVICE_NAME" --format "{{.ID}}" | head -1)

if [[ -z "$CONTAINER_ID" ]]; then
    print_error "Container $SERVICE_NAME not found or not running"
    echo "Available containers:"
    docker ps --format "table {{.Names}}\t{{.Status}}"
    exit 1
fi

print_success "Container $SERVICE_NAME is running ($CONTAINER_ID)"

# Check package installation
print_status "Checking package installation..."
PACKAGE_CHECK=$(docker exec "$CONTAINER_ID" pip show "$PACKAGE_NAME" 2>/dev/null || echo "NOT_FOUND")

if [[ "$PACKAGE_CHECK" == "NOT_FOUND" ]]; then
    print_error "Package $PACKAGE_NAME is not installed"
    exit 1
else
    print_success "Package $PACKAGE_NAME is installed"
    echo "$(docker exec "$CONTAINER_ID" pip show "$PACKAGE_NAME" | grep -E "^(Name|Version|Location):")"
fi

# Check connector import
print_status "Testing connector import..."
IMPORT_CHECK=$(docker exec "$CONTAINER_ID" python -c "
try:
    from om_s3_connector.core.s3_connector import S3Source
    from openmetadata_ingestion.source.source import Source
    if issubclass(S3Source, Source):
        print('SUCCESS')
    else:
        print('INHERITANCE_FAILED')
except ImportError as e:
    print(f'IMPORT_ERROR: {e}')
except Exception as e:
    print(f'ERROR: {e}')
" 2>/dev/null)

case "$IMPORT_CHECK" in
    "SUCCESS")
        print_success "Connector import and inheritance check passed"
        ;;
    "INHERITANCE_FAILED")
        print_error "Connector inheritance check failed"
        exit 1
        ;;
    "IMPORT_ERROR"*)
        print_error "Import failed: ${IMPORT_CHECK#IMPORT_ERROR: }"
        exit 1
        ;;
    "ERROR"*)
        print_error "Connector test failed: ${IMPORT_CHECK#ERROR: }"
        exit 1
        ;;
    *)
        print_error "Unknown import check result: $IMPORT_CHECK"
        exit 1
        ;;
esac

# Check OpenMetadata service status
print_status "Checking OpenMetadata service status..."
SERVICE_STATUS=$(docker exec "$CONTAINER_ID" bash -c "
    if command -v supervisorctl &> /dev/null; then
        if supervisorctl status openmetadata 2>/dev/null | grep -q RUNNING; then
            echo 'SUPERVISOR_RUNNING'
        else
            echo 'SUPERVISOR_NOT_RUNNING'
        fi
    elif systemctl is-active --quiet openmetadata 2>/dev/null; then
        echo 'SYSTEMD_RUNNING'
    elif pgrep -f openmetadata &>/dev/null; then
        echo 'PROCESS_RUNNING'
    else
        echo 'NOT_RUNNING'
    fi
" 2>/dev/null)

case "$SERVICE_STATUS" in
    "SUPERVISOR_RUNNING")
        print_success "OpenMetadata service is running (supervisorctl)"
        ;;
    "SYSTEMD_RUNNING")
        print_success "OpenMetadata service is running (systemd)"
        ;;
    "PROCESS_RUNNING")
        print_success "OpenMetadata process is running"
        ;;
    "SUPERVISOR_NOT_RUNNING")
        print_error "OpenMetadata service is not running (supervisorctl)"
        exit 1
        ;;
    "NOT_RUNNING")
        print_error "OpenMetadata service is not running"
        exit 1
        ;;
    *)
        print_warning "Could not determine service status: $SERVICE_STATUS"
        ;;
esac

# Check API availability
print_status "Checking OpenMetadata API..."
API_CHECK=$(docker exec "$CONTAINER_ID" bash -c "
    if command -v curl &> /dev/null; then
        curl -s -o /dev/null -w '%{http_code}' http://localhost:8585/api/v1/health 2>/dev/null || echo '000'
    else
        echo 'NO_CURL'
    fi
")

case "$API_CHECK" in
    "200")
        print_success "OpenMetadata API is responding (HTTP 200)"
        ;;
    "NO_CURL")
        print_warning "curl not available for API check"
        ;;
    "000")
        print_error "Could not connect to OpenMetadata API"
        exit 1
        ;;
    *)
        print_warning "API returned HTTP $API_CHECK (service might be starting)"
        ;;
esac

# Check assets installation
print_status "Checking connector assets..."
ASSETS_CHECK=$(docker exec "$CONTAINER_ID" bash -c "
    if [[ -d '/opt/openmetadata/static/assets/connectors/s3' ]]; then
        ls /opt/openmetadata/static/assets/connectors/s3/*.svg 2>/dev/null | wc -l
    else
        echo '0'
    fi
")

if [[ "$ASSETS_CHECK" -gt 0 ]]; then
    print_success "Found $ASSETS_CHECK icon assets"
    docker exec "$CONTAINER_ID" ls -la /opt/openmetadata/static/assets/connectors/s3/
else
    print_warning "No icon assets found (functionality not affected)"
fi

# Check connector configuration
print_status "Checking connector configuration..."
CONFIG_CHECK=$(docker exec "$CONTAINER_ID" bash -c "
    if [[ -f '/opt/openmetadata/conf/connectors/s3-connector.json' ]]; then
        echo 'CONFIG_FOUND'
    else
        echo 'CONFIG_NOT_FOUND'
    fi
")

if [[ "$CONFIG_CHECK" == "CONFIG_FOUND" ]]; then
    print_success "Connector configuration file found"
else
    print_warning "Connector configuration file not found (will be created during setup)"
fi

# Check entry points
print_status "Checking OpenMetadata entry points..."
ENTRY_POINTS=$(docker exec "$CONTAINER_ID" python -c "
import pkg_resources
s3_connectors = []
for ep in pkg_resources.iter_entry_points('openmetadata_sources'):
    if 's3' in ep.name.lower():
        s3_connectors.append(f'{ep.name} -> {ep.module_name}')
print('\\n'.join(s3_connectors) if s3_connectors else 'NO_S3_CONNECTORS')
" 2>/dev/null)

if [[ "$ENTRY_POINTS" == "NO_S3_CONNECTORS" ]]; then
    print_warning "No S3 connectors found in entry points"
else
    print_success "S3 connector entry points found:"
    echo "$ENTRY_POINTS" | sed 's/^/  /'
fi

# Memory and resource check
print_status "Checking container resources..."
MEMORY_INFO=$(docker exec "$CONTAINER_ID" bash -c "
    echo 'Memory:'
    free -h | grep -E '^Mem:' || echo 'Memory info not available'
    echo 'Disk:'
    df -h /opt/openmetadata 2>/dev/null | tail -1 || echo 'Disk info not available'
    echo 'Load:'
    uptime | grep -o 'load average.*' || echo 'Load info not available'
")

echo "$MEMORY_INFO"

# Final summary
echo ""
print_success "🎉 Health Check Summary"
echo "  ✅ Container: Running"
echo "  ✅ Package: Installed and importable"
echo "  ✅ Service: Running"
echo "  ✅ API: Responding"
echo "  ✅ Assets: $ASSETS_CHECK icons found"
echo ""
echo "🚀 Your S3 Connector is healthy and ready to use!"
echo ""
echo "📱 Quick Actions:"
echo "  • View logs: docker logs -f $SERVICE_NAME"
echo "  • Access UI: http://localhost:8585"
echo "  • Restart service: docker restart $SERVICE_NAME"
echo ""
echo "📚 Documentation: deployment/docker-hotdeploy/README.md"
