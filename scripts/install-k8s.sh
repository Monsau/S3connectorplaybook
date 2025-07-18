#!/bin/bash
# 🚀 S3 Connector Kubernetes Quick Install Script
# This script automates the installation of the S3 connector on Kubernetes

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/home/mustapha.fonsau/projects/S3connectorplaybook"
NAMESPACE="openmetadata"
APP_NAME="s3-connector"
VERSION="v0.9"

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

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check if kubectl is available
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl is not installed or not in PATH"
        exit 1
    fi
    
    # Check if docker is available
    if ! command -v docker &> /dev/null; then
        print_error "docker is not installed or not in PATH"
        exit 1
    fi
    
    # Check if Python 3.10+ is available
    if ! python3 -c "import sys; assert sys.version_info >= (3, 10)" 2>/dev/null; then
        print_error "Python 3.10+ is required"
        exit 1
    fi
    
    # Check Kubernetes cluster connectivity
    if ! kubectl cluster-info &> /dev/null; then
        print_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

# Function to setup environment
setup_environment() {
    print_status "Setting up environment..."
    
    cd "$PROJECT_DIR"
    
    # Activate virtual environment
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        print_success "Virtual environment activated"
    else
        print_error "Virtual environment not found. Please run the environment setup first."
        exit 1
    fi
    
    # Install build dependencies
    pip install build twine > /dev/null 2>&1
    print_success "Build dependencies installed"
}

# Function to build package
build_package() {
    print_status "Building wheel package..."
    
    # Clean previous builds
    rm -rf build/ dist/
    
    # Build wheel
    python -m build --wheel > /dev/null 2>&1
    
    # Verify build
    if [ -f "dist/openmetadata_s3_connector-"*".whl" ]; then
        print_success "Wheel package built successfully"
        ls -la dist/
    else
        print_error "Failed to build wheel package"
        exit 1
    fi
}

# Function to build container image
build_container() {
    print_status "Building container image..."
    
    # Get registry from user input or use default
    read -p "Enter your container registry (e.g., docker.io/username, your-registry.com): " REGISTRY
    if [ -z "$REGISTRY" ]; then
        print_warning "No registry provided, using local tag only"
        REGISTRY="local"
    fi
    
    IMAGE_TAG="${REGISTRY}/${APP_NAME}:${VERSION}"
    
    # Build image
    docker build -f deployment/Dockerfile.prod -t "$IMAGE_TAG" .
    
    # Tag as latest
    docker tag "$IMAGE_TAG" "${REGISTRY}/${APP_NAME}:latest"
    
    print_success "Container image built: $IMAGE_TAG"
    
    # Ask if user wants to push
    if [ "$REGISTRY" != "local" ]; then
        read -p "Push image to registry? (y/N): " PUSH_IMAGE
        if [[ $PUSH_IMAGE =~ ^[Yy]$ ]]; then
            print_status "Pushing image to registry..."
            docker push "$IMAGE_TAG"
            docker push "${REGISTRY}/${APP_NAME}:latest"
            print_success "Image pushed to registry"
        fi
    fi
    
    # Update deployment manifest with image
    sed -i "s|your-registry/s3-connector:v0.9|${IMAGE_TAG}|g" deployment/k8s/deployment.yaml
    print_success "Deployment manifest updated with image: $IMAGE_TAG"
}

# Function to create namespace
create_namespace() {
    print_status "Creating Kubernetes namespace..."
    
    if kubectl get namespace "$NAMESPACE" &> /dev/null; then
        print_warning "Namespace $NAMESPACE already exists"
    else
        kubectl create namespace "$NAMESPACE"
        print_success "Namespace $NAMESPACE created"
    fi
}

# Function to configure secrets
configure_secrets() {
    print_status "Configuring Kubernetes secrets..."
    
    # Check if secret template exists
    if [ ! -f "deployment/k8s/secret.yaml.template" ]; then
        print_error "Secret template not found"
        exit 1
    fi
    
    # Copy template
    cp deployment/k8s/secret.yaml.template deployment/k8s/secret.yaml
    
    print_warning "You need to edit deployment/k8s/secret.yaml with your credentials"
    print_status "Required credentials:"
    echo "  - AWS Access Key ID"
    echo "  - AWS Secret Access Key"
    echo "  - S3 Bucket Name"
    echo "  - OpenMetadata Server URL"
    echo ""
    print_status "Encode values using: echo -n 'your-value' | base64"
    
    read -p "Have you configured the secrets file? (y/N): " SECRETS_CONFIGURED
    if [[ ! $SECRETS_CONFIGURED =~ ^[Yy]$ ]]; then
        print_warning "Please configure deployment/k8s/secret.yaml and run the script again"
        exit 0
    fi
}

# Function to deploy to Kubernetes
deploy_to_kubernetes() {
    print_status "Deploying to Kubernetes..."
    
    cd deployment/k8s
    
    # Apply manifests in order
    print_status "Applying RBAC..."
    kubectl apply -f rbac.yaml
    
    print_status "Applying ConfigMap..."
    kubectl apply -f configmap.yaml
    
    print_status "Applying Secrets..."
    kubectl apply -f secret.yaml
    
    print_status "Applying Deployment..."
    kubectl apply -f deployment.yaml
    
    print_status "Applying Service..."
    kubectl apply -f service.yaml
    
    print_status "Applying CronJob..."
    kubectl apply -f cronjob.yaml
    
    # Optional: Apply network policy
    read -p "Apply network policy for enhanced security? (y/N): " APPLY_NETPOL
    if [[ $APPLY_NETPOL =~ ^[Yy]$ ]]; then
        kubectl apply -f network-policy.yaml
        print_success "Network policy applied"
    fi
    
    print_success "All manifests applied successfully"
}

# Function to validate deployment
validate_deployment() {
    print_status "Validating deployment..."
    
    # Wait for deployment to be ready
    print_status "Waiting for deployment to be ready..."
    kubectl rollout status deployment/"$APP_NAME" -n "$NAMESPACE" --timeout=300s
    
    # Check pod status
    print_status "Checking pod status..."
    kubectl get pods -n "$NAMESPACE" -l app="$APP_NAME"
    
    # Get logs
    print_status "Recent logs:"
    kubectl logs -n "$NAMESPACE" deployment/"$APP_NAME" --tail=20
    
    # Test import
    print_status "Testing connector import..."
    if kubectl exec -n "$NAMESPACE" deployment/"$APP_NAME" -- python -c "import om_s3_connector; print('✅ Import successful')" 2>/dev/null; then
        print_success "Connector import test passed"
    else
        print_warning "Connector import test failed - check logs"
    fi
    
    print_success "Deployment validation completed"
}

# Function to show post-installation info
show_post_install_info() {
    print_success "🎉 S3 Connector installation completed!"
    echo ""
    echo "📊 Deployment Status:"
    kubectl get all -n "$NAMESPACE" -l app="$APP_NAME"
    echo ""
    echo "🔧 Useful Commands:"
    echo "  View logs:      kubectl logs -n $NAMESPACE deployment/$APP_NAME -f"
    echo "  Check status:   kubectl get pods -n $NAMESPACE -l app=$APP_NAME"
    echo "  Shell access:   kubectl exec -it -n $NAMESPACE deployment/$APP_NAME -- bash"
    echo "  Restart:        kubectl rollout restart deployment/$APP_NAME -n $NAMESPACE"
    echo ""
    echo "📚 Next Steps:"
    echo "  1. Configure your ingestion workflows"
    echo "  2. Set up monitoring and alerting"
    echo "  3. Review security settings"
    echo "  4. Test S3 connectivity and data ingestion"
    echo ""
    echo "📖 Documentation: ./KUBERNETES_INSTALLATION_PLAYBOOK.md"
    echo "🔧 Troubleshooting: ./deployment/KUBERNETES_DEPLOYMENT_COMPLETE.md"
}

# Main execution
main() {
    echo "🚀 S3 Connector Kubernetes Installation Script"
    echo "=============================================="
    echo ""
    
    check_prerequisites
    setup_environment
    build_package
    build_container
    create_namespace
    configure_secrets
    deploy_to_kubernetes
    validate_deployment
    show_post_install_info
}

# Handle script interruption
trap 'print_error "Installation interrupted"; exit 1' INT

# Run main function
main "$@"
