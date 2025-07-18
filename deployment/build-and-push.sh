#!/bin/bash
set -e

# Build and Push Script for S3 Connector
# Usage: ./build-and-push.sh [registry] [tag]

# Configuration
REGISTRY=${1:-"your-registry.com"}
IMAGE_NAME="s3-connector"
TAG=${2:-"v0.9"}
FULL_IMAGE="${REGISTRY}/${IMAGE_NAME}:${TAG}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Building S3 Connector Docker Image${NC}"
echo "Registry: ${REGISTRY}"
echo "Image: ${IMAGE_NAME}"
echo "Tag: ${TAG}"
echo "Full image name: ${FULL_IMAGE}"
echo

# Check if registry is accessible
echo -e "${YELLOW}📡 Checking registry access...${NC}"
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running or accessible${NC}"
    exit 1
fi

# Build the image
echo -e "${YELLOW}🔨 Building Docker image...${NC}"
if docker build -f deployment/Dockerfile.prod -t "${FULL_IMAGE}" .; then
    echo -e "${GREEN}✅ Docker image built successfully${NC}"
else
    echo -e "${RED}❌ Docker build failed${NC}"
    exit 1
fi

# Tag with latest
LATEST_IMAGE="${REGISTRY}/${IMAGE_NAME}:latest"
docker tag "${FULL_IMAGE}" "${LATEST_IMAGE}"
echo -e "${GREEN}🏷️  Tagged as: ${LATEST_IMAGE}${NC}"

# Push to registry
echo -e "${YELLOW}📤 Pushing to registry...${NC}"
if docker push "${FULL_IMAGE}" && docker push "${LATEST_IMAGE}"; then
    echo -e "${GREEN}✅ Images pushed successfully${NC}"
    echo "  - ${FULL_IMAGE}"
    echo "  - ${LATEST_IMAGE}"
else
    echo -e "${RED}❌ Failed to push images${NC}"
    exit 1
fi

# Show image information
echo
echo -e "${GREEN}📋 Image Information:${NC}"
docker images | grep "${IMAGE_NAME}" | head -5

echo
echo -e "${GREEN}🎉 Build and push completed successfully!${NC}"
echo -e "${YELLOW}💡 Next steps:${NC}"
echo "1. Update deployment/k8s/deployment.yaml with image: ${FULL_IMAGE}"
echo "2. Configure secrets: cp deployment/k8s/secret.yaml.template deployment/k8s/secret.yaml"
echo "3. Deploy to Kubernetes: kubectl apply -f deployment/k8s/"
