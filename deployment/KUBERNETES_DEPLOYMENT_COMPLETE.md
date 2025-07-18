# Complete Kubernetes Deployment Guide for S3 Connector

This guide provides a comprehensive process for deploying the S3 Connector to Kubernetes, from development to production.

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Project Build & Package](#project-build--package)
3. [Container Image Creation](#container-image-creation)
4. [Kubernetes Configuration](#kubernetes-configuration)
5. [Deployment Process](#deployment-process)
6. [Configuration Management](#configuration-management)
7. [Monitoring & Troubleshooting](#monitoring--troubleshooting)
8. [Production Considerations](#production-considerations)

## Prerequisites

### Environment Requirements
- Kubernetes cluster (v1.20+)
- kubectl configured and connected to cluster
- Docker or Podman for container building
- Container registry access (Docker Hub, ECR, GCR, etc.)
- OpenMetadata instance (can be in-cluster or external)

### Project Requirements
- Python 3.10+
- All dependencies from `requirements.txt`
- Valid S3/MinIO credentials
- OpenMetadata API access

## Project Build & Package

### Step 1: Build the Wheel Package

```bash
# 1. Setup build environment
cd /home/mustapha.fonsau/projects/S3connectorplaybook
source venv/bin/activate  # or use activate.sh

# 2. Install build tools
pip install build twine

# 3. Build wheel package
python -m build --wheel

# 4. Verify package
ls -la dist/
# Should see: openmetadata_s3_connector-0.9-py3-none-any.whl
```

### Step 2: Validate Package Installation

```bash
# Test wheel installation
pip install dist/openmetadata_s3_connector-*.whl
python -c "import om_s3_connector; print('✅ Package validated')"
```

## Container Image Creation

### Step 1: Production Dockerfile

Create `deployment/Dockerfile.k8s`:

```dockerfile
# Multi-stage build for production Kubernetes deployment
FROM python:3.10-slim as builder

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Copy and build the package
COPY requirements.txt setup.py ./
COPY src/ ./src/
COPY config/ ./config/

# Build wheel package
RUN pip install build && python -m build --wheel

# Production stage
FROM openmetadata/openmetadata-ingestion:1.8.0

# Create application user
USER root
RUN groupadd -r s3connector && useradd -r -g s3connector s3connector

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    jq \
    && rm -rf /var/lib/apt/lists/*

# Switch to application user
USER s3connector
WORKDIR /app

# Copy wheel package and install
COPY --from=builder --chown=s3connector:s3connector /build/dist/*.whl /tmp/
RUN pip install --user /tmp/*.whl && rm -f /tmp/*.whl

# Copy configuration templates
COPY --chown=s3connector:s3connector config/ /app/config/
COPY --chown=s3connector:s3connector scripts/ /app/scripts/

# Set environment
ENV PYTHONPATH="/app:${PYTHONPATH}"
ENV PATH="/home/s3connector/.local/bin:${PATH}"
ENV CONNECTOR_TYPE="s3"
ENV LOG_LEVEL="INFO"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import om_s3_connector; print('OK')" || exit 1

# Labels
LABEL maintainer="mfonsau@talentys.eu"
LABEL version="0.9"
LABEL description="S3/MinIO OpenMetadata Connector for Kubernetes"

# Default command
CMD ["metadata", "ingest", "--help"]
```

### Step 2: Build and Push Container

```bash
# 1. Build container image
docker build -f deployment/Dockerfile.k8s -t your-registry/s3-connector:v0.9 .

# 2. Tag for latest
docker tag your-registry/s3-connector:v0.9 your-registry/s3-connector:latest

# 3. Push to registry
docker push your-registry/s3-connector:v0.9
docker push your-registry/s3-connector:latest

# 4. Verify image
docker run --rm your-registry/s3-connector:v0.9 python -c "import om_s3_connector; print('✅ Image ready')"
```

## Kubernetes Configuration

### Step 1: Namespace and RBAC

Create `deployment/k8s/00-namespace.yaml`:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: s3-connector
  labels:
    name: s3-connector
    component: data-ingestion
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: s3-connector
  namespace: s3-connector
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: s3-connector
  name: s3-connector-role
rules:
- apiGroups: [""]
  resources: ["configmaps", "secrets", "pods", "events"]
  verbs: ["get", "list", "create"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: s3-connector-binding
  namespace: s3-connector
subjects:
- kind: ServiceAccount
  name: s3-connector
  namespace: s3-connector
roleRef:
  kind: Role
  name: s3-connector-role
  apiGroup: rbac.authorization.k8s.io
```

### Step 2: Configuration Management

Create `deployment/k8s/01-configmap.yaml`:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: s3-connector-config
  namespace: s3-connector
data:
  # Basic ingestion configuration
  ingestion.yaml: |
    source:
      type: S3
      serviceName: "s3-data-lake"
      serviceConnection:
        config:
          type: S3
          connection:
            awsRegion: "${AWS_REGION}"
            bucketName: "${S3_BUCKET_NAME}"
            securityConfig:
              protocol: access_key
              awsAccessKeyId: "${AWS_ACCESS_KEY_ID}"
              awsSecretAccessKey: "${AWS_SECRET_ACCESS_KEY}"
            fileFormats: ["csv", "json", "parquet", "tsv", "orc", "avro"]
            enablePartitionParsing: true
            sampleSize: 50
      sourceConfig:
        config:
          type: DatabaseMetadata
          markDeletedTables: true
          includeTables: true
          includeViews: false
    sink:
      type: metadata-rest
      config:
        openMetadataServerConfig:
          hostPort: "${OPENMETADATA_HOST_PORT}"
          authProvider: "${OPENMETADATA_AUTH_PROVIDER}"
          apiToken: "${OPENMETADATA_API_TOKEN}"
    workflowConfig:
      loggerLevel: "${LOG_LEVEL}"
      openMetadataServerConfig:
        hostPort: "${OPENMETADATA_HOST_PORT}"
        authProvider: "${OPENMETADATA_AUTH_PROVIDER}"
        apiToken: "${OPENMETADATA_API_TOKEN}"

  # Production RBAC configuration
  production.yaml: |
    source:
      type: S3
      serviceName: "s3-production-lake"
      serviceConnection:
        config:
          type: S3
          connection:
            awsRegion: "${AWS_REGION}"
            bucketName: "${S3_BUCKET_NAME}"
            securityConfig:
              protocol: iam_role
              roleArn: "${IAM_ROLE_ARN}"
              roleSessionName: "openmetadata-s3-connector"
            fileFormats: ["csv", "json", "parquet", "tsv", "orc", "avro"]
            enablePartitionParsing: true
            sampleSize: 100
            piiDetection:
              enabled: true
              sensitivity: "medium"
            rbacValidation:
              enabled: true
              validatePermissions: true
      sourceConfig:
        config:
          type: DatabaseMetadata
          markDeletedTables: true
          includeTables: true
          includeViews: true
          enableAuditLogging: true
          complianceFrameworks: ["GDPR", "SOX", "HIPAA"]
    sink:
      type: metadata-rest
      config:
        openMetadataServerConfig:
          hostPort: "${OPENMETADATA_HOST_PORT}"
          authProvider: "${OPENMETADATA_AUTH_PROVIDER}"
          apiToken: "${OPENMETADATA_API_TOKEN}"
          verifySSL: true
    workflowConfig:
      loggerLevel: "INFO"
      enableProfiling: true
      auditConfig:
        enabled: true
        level: "comprehensive"
```

### Step 3: Secrets Management

Create `deployment/k8s/02-secrets.yaml`:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: s3-connector-secrets
  namespace: s3-connector
type: Opaque
stringData:
  # AWS/S3 Credentials
  AWS_ACCESS_KEY_ID: "your-access-key"
  AWS_SECRET_ACCESS_KEY: "your-secret-key"
  AWS_REGION: "us-east-1"
  S3_BUCKET_NAME: "your-data-bucket"
  IAM_ROLE_ARN: "arn:aws:iam::account:role/S3ConnectorRole"
  
  # OpenMetadata Configuration
  OPENMETADATA_HOST_PORT: "http://openmetadata:8585/api"
  OPENMETADATA_AUTH_PROVIDER: "no-auth"
  OPENMETADATA_API_TOKEN: "your-api-token"
  
  # Connector Configuration
  LOG_LEVEL: "INFO"
  CONNECTOR_TYPE: "s3"
```

### Step 4: Deployment Manifests

Create `deployment/k8s/03-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: s3-connector
  namespace: s3-connector
  labels:
    app: s3-connector
    version: v0.9
spec:
  replicas: 1
  selector:
    matchLabels:
      app: s3-connector
  template:
    metadata:
      labels:
        app: s3-connector
        version: v0.9
    spec:
      serviceAccountName: s3-connector
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
      containers:
      - name: s3-connector
        image: your-registry/s3-connector:v0.9
        imagePullPolicy: Always
        
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "4Gi"
            cpu: "2"
        
        env:
        - name: PYTHONPATH
          value: "/app"
        - name: CONNECTOR_TYPE
          value: "s3"
        envFrom:
        - secretRef:
            name: s3-connector-secrets
        
        volumeMounts:
        - name: config
          mountPath: /app/config
          readOnly: true
        - name: tmp
          mountPath: /tmp
        
        livenessProbe:
          exec:
            command:
            - python
            - -c
            - "import om_s3_connector; print('OK')"
          initialDelaySeconds: 30
          periodSeconds: 30
        
        readinessProbe:
          exec:
            command:
            - python
            - -c
            - "import om_s3_connector; print('OK')"
          initialDelaySeconds: 10
          periodSeconds: 10
        
        command: ["sleep"]
        args: ["infinity"]  # Keep container running for manual execution
        
      volumes:
      - name: config
        configMap:
          name: s3-connector-config
      - name: tmp
        emptyDir: {}
```

### Step 5: CronJob for Scheduled Ingestion

Create `deployment/k8s/04-cronjob.yaml`:

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: s3-connector-scheduled
  namespace: s3-connector
spec:
  schedule: "0 */6 * * *"  # Every 6 hours
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 3
  concurrencyPolicy: Forbid
  
  jobTemplate:
    spec:
      completions: 1
      parallelism: 1
      backoffLimit: 2
      activeDeadlineSeconds: 3600  # 1 hour timeout
      
      template:
        metadata:
          labels:
            app: s3-connector-job
            type: scheduled
        spec:
          serviceAccountName: s3-connector
          restartPolicy: OnFailure
          
          containers:
          - name: s3-connector
            image: your-registry/s3-connector:v0.9
            
            resources:
              requests:
                memory: "2Gi"
                cpu: "1"
              limits:
                memory: "8Gi"
                cpu: "4"
            
            envFrom:
            - secretRef:
                name: s3-connector-secrets
            
            volumeMounts:
            - name: config
              mountPath: /app/config
              readOnly: true
            
            command: ["metadata"]
            args: ["ingest", "-c", "/app/config/production.yaml", "--verbose"]
          
          volumes:
          - name: config
            configMap:
              name: s3-connector-config
```

## Deployment Process

### Step 1: Environment Preparation

```bash
# 1. Ensure kubectl is configured
kubectl cluster-info

# 2. Create deployment directory
mkdir -p deployment/k8s
cd deployment/k8s

# 3. Customize secrets
cp 02-secrets.yaml 02-secrets-local.yaml
nano 02-secrets-local.yaml  # Edit with your actual credentials

# 4. Update image references
sed -i 's/your-registry/your-actual-registry/g' *.yaml
```

### Step 2: Deploy to Kubernetes

```bash
# 1. Deploy in order
kubectl apply -f 00-namespace.yaml
kubectl apply -f 01-configmap.yaml
kubectl apply -f 02-secrets-local.yaml
kubectl apply -f 03-deployment.yaml

# 2. Verify deployment
kubectl get pods -n s3-connector
kubectl logs -n s3-connector deployment/s3-connector

# 3. Test connector
kubectl exec -n s3-connector deployment/s3-connector -- python -c "import om_s3_connector; print('✅ Ready')"
```

### Step 3: Manual Ingestion Test

```bash
# 1. Run test ingestion
kubectl exec -n s3-connector deployment/s3-connector -- \
  metadata ingest -c /app/config/ingestion.yaml --dry-run

# 2. Run actual ingestion
kubectl exec -n s3-connector deployment/s3-connector -- \
  metadata ingest -c /app/config/ingestion.yaml

# 3. Check logs
kubectl logs -n s3-connector deployment/s3-connector -f
```

### Step 4: Deploy Scheduled Jobs (Optional)

```bash
# 1. Deploy CronJob
kubectl apply -f 04-cronjob.yaml

# 2. Verify CronJob
kubectl get cronjobs -n s3-connector

# 3. Manually trigger job for testing
kubectl create job -n s3-connector manual-test --from=cronjob/s3-connector-scheduled

# 4. Check job status
kubectl get jobs -n s3-connector
kubectl logs -n s3-connector job/manual-test
```

## Configuration Management

### Environment-Specific Configurations

**Development Environment:**
```bash
# Use basic configuration
kubectl create configmap s3-connector-config-dev \
  --from-file=config/ingestion.yaml \
  -n s3-connector
```

**Staging Environment:**
```bash
# Use enhanced configuration
kubectl create configmap s3-connector-config-staging \
  --from-file=config/enhanced_ingestion_examples.yaml \
  -n s3-connector
```

**Production Environment:**
```bash
# Use production RBAC configuration
kubectl create configmap s3-connector-config-prod \
  --from-file=config/prod-s3-ingestion-rbac.yaml \
  -n s3-connector
```

### Dynamic Configuration Updates

```bash
# 1. Update configuration
kubectl create configmap s3-connector-config \
  --from-file=config/ \
  --dry-run=client -o yaml | kubectl apply -f -

# 2. Restart deployment to pick up changes
kubectl rollout restart deployment/s3-connector -n s3-connector

# 3. Verify update
kubectl rollout status deployment/s3-connector -n s3-connector
```

## Monitoring & Troubleshooting

### Health Checks

```bash
# 1. Check pod status
kubectl get pods -n s3-connector -o wide

# 2. Check pod events
kubectl describe pods -n s3-connector

# 3. Check logs
kubectl logs -n s3-connector deployment/s3-connector --tail=100

# 4. Get into pod for debugging
kubectl exec -it -n s3-connector deployment/s3-connector -- /bin/bash
```

### Common Issues and Solutions

**1. Image Pull Errors:**
```bash
# Check image accessibility
docker pull your-registry/s3-connector:v0.9

# Verify image registry secrets
kubectl get secrets -n s3-connector
```

**2. Configuration Issues:**
```bash
# Validate YAML syntax
kubectl apply --dry-run=client -f deployment/k8s/

# Check environment variables
kubectl exec -n s3-connector deployment/s3-connector -- env | grep -E "(AWS|OPENMETADATA)"
```

**3. Connection Issues:**
```bash
# Test S3 connectivity
kubectl exec -n s3-connector deployment/s3-connector -- \
  python -c "import boto3; print(boto3.client('s3').list_buckets())"

# Test OpenMetadata connectivity
kubectl exec -n s3-connector deployment/s3-connector -- \
  curl -v $OPENMETADATA_HOST_PORT/api/v1/system/version
```

### Logging and Monitoring

```bash
# 1. Enhanced logging
kubectl logs -n s3-connector deployment/s3-connector -f --timestamps

# 2. Resource monitoring
kubectl top pods -n s3-connector

# 3. Event monitoring
kubectl get events -n s3-connector --sort-by=.metadata.creationTimestamp
```

## Production Considerations

### Security Best Practices

1. **Use IAM Roles instead of Access Keys**
2. **Enable Pod Security Standards**
3. **Implement Network Policies**
4. **Use Secret Management (Vault, etc.)**
5. **Regular security scanning of container images**

### Performance Optimization

1. **Resource Limits and Requests**
2. **Horizontal Pod Autoscaling**
3. **Node Affinity for data locality**
4. **Persistent volumes for large datasets**

### High Availability

1. **Multiple replicas with anti-affinity**
2. **Pod Disruption Budgets**
3. **Health checks and restart policies**
4. **Backup and disaster recovery procedures**

### Example Production Deployment Script

```bash
#!/bin/bash
# deployment/deploy-to-k8s.sh

set -e

ENVIRONMENT=${1:-dev}
REGISTRY=${2:-your-registry}
VERSION=${3:-v0.9}

echo "🚀 Deploying S3 Connector to Kubernetes"
echo "Environment: $ENVIRONMENT"
echo "Registry: $REGISTRY"
echo "Version: $VERSION"

# 1. Build and push image
echo "📦 Building container image..."
docker build -f deployment/Dockerfile.k8s -t $REGISTRY/s3-connector:$VERSION .
docker push $REGISTRY/s3-connector:$VERSION

# 2. Update manifests
echo "📝 Updating Kubernetes manifests..."
sed -i "s|your-registry|$REGISTRY|g" deployment/k8s/*.yaml
sed -i "s|:v0.9|:$VERSION|g" deployment/k8s/*.yaml

# 3. Deploy to cluster
echo "☸️  Deploying to Kubernetes..."
kubectl apply -f deployment/k8s/00-namespace.yaml
kubectl apply -f deployment/k8s/01-configmap.yaml
kubectl apply -f deployment/k8s/02-secrets-$ENVIRONMENT.yaml
kubectl apply -f deployment/k8s/03-deployment.yaml

# 4. Wait for deployment
echo "⏳ Waiting for deployment..."
kubectl wait --for=condition=available --timeout=300s deployment/s3-connector -n s3-connector

# 5. Verify deployment
echo "✅ Verifying deployment..."
kubectl get pods -n s3-connector
kubectl exec -n s3-connector deployment/s3-connector -- python -c "import om_s3_connector; print('🎉 Deployment successful!')"

echo "🏁 Deployment complete!"
```

Make the script executable and use it:
```bash
chmod +x deployment/deploy-to-k8s.sh
./deployment/deploy-to-k8s.sh production your-registry.com v0.9
```

This comprehensive guide provides everything needed to deploy your S3 Connector to Kubernetes, from building the container to production monitoring.
