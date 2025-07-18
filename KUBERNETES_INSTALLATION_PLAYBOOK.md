# 🚀 S3 Connector Kubernetes Installation Playbook

A comprehensive, step-by-step guide to deploy the S3/MinIO OpenMetadata connector on Kubernetes.

## 📋 Quick Start Checklist

- [ ] **Prerequisites verified**
- [ ] **Environment setup complete**
- [ ] **Package built and tested**
- [ ] **Container image created**
- [ ] **Kubernetes secrets configured**
- [ ] **Manifests applied**
- [ ] **Deployment validated**
- [ ] **Production monitoring setup**

---

## 🔧 Prerequisites

### System Requirements
```bash
# Verify Kubernetes cluster access
kubectl cluster-info
kubectl get nodes

# Check minimum versions
kubectl version --client
docker --version
python3 --version  # Should be 3.10+
```

### Required Access
- Kubernetes cluster with RBAC enabled
- Container registry (Docker Hub, ECR, GCR, etc.)
- OpenMetadata instance (can be external)
- S3/MinIO credentials with read permissions

---

## 🛠️ Step 1: Environment Setup

### Activate Virtual Environment
```bash
cd /home/mustapha.fonsau/projects/S3connectorplaybook
source venv/bin/activate
# Or use the provided script
./activate.sh
```

### Verify Dependencies
```bash
# Ensure all dependencies are installed
pip install -r requirements.txt
pip install build twine

# Test imports
python test_installation.py
```

---

## 📦 Step 2: Build and Package

### Build Wheel Package
```bash
# Clean any previous builds
rm -rf build/ dist/

# Build the wheel package
python -m build --wheel

# Verify package
ls -la dist/
# Expected: openmetadata_s3_connector-0.9-py3-none-any.whl
```

### Test Package Installation
```bash
# Test in clean environment
pip uninstall om_s3_connector -y
pip install dist/openmetadata_s3_connector-*.whl

# Verify installation
python -c "
from om_s3_connector import S3Connector, S3Config
print('✅ Package installation verified')
"
```

---

## 🐳 Step 3: Container Image Creation

### Build Production Image
```bash
# Build using the production Dockerfile
docker build -f deployment/Dockerfile.prod -t s3-connector:v0.9 .

# Tag for your registry
docker tag s3-connector:v0.9 YOUR_REGISTRY/s3-connector:v0.9
docker tag s3-connector:v0.9 YOUR_REGISTRY/s3-connector:latest
```

### Push to Registry
```bash
# Login to your registry
docker login YOUR_REGISTRY

# Push images
docker push YOUR_REGISTRY/s3-connector:v0.9
docker push YOUR_REGISTRY/s3-connector:latest
```

### Verify Container
```bash
# Test container locally
docker run --rm YOUR_REGISTRY/s3-connector:v0.9 \
  python -c "import om_s3_connector; print('✅ Container verified')"
```

---

## 🔐 Step 4: Configure Kubernetes Secrets

### Create Namespace
```bash
kubectl create namespace openmetadata
```

### Prepare Secrets File
```bash
# Copy the template
cp deployment/k8s/secret.yaml.template deployment/k8s/secret.yaml

# Edit with your credentials (use base64 encoding)
# Helper commands for encoding:
echo -n 'YOUR_AWS_ACCESS_KEY' | base64
echo -n 'YOUR_AWS_SECRET_KEY' | base64
echo -n 'your-bucket-name' | base64
echo -n 'http://openmetadata-server:8585/api' | base64
```

### Example Secret Configuration
```yaml
# deployment/k8s/secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: s3-connector-secrets
  namespace: openmetadata
type: Opaque
data:
  aws-access-key-id: "WU9VUl9BV1NfQUNDRVNTX0tFWQ=="  # YOUR_AWS_ACCESS_KEY
  aws-secret-access-key: "WU9VUl9BV1NfU0VDUkVUX0tFWQ=="  # YOUR_AWS_SECRET_KEY
  bucket-name: "eW91ci1idWNrZXQtbmFtZQ=="  # your-bucket-name
  openmetadata-server-url: "aHR0cDovL29wZW5tZXRhZGF0YS1zZXJ2ZXI6ODU4NS9hcGk="  # http://openmetadata-server:8585/api
```

---

## 🚀 Step 5: Deploy to Kubernetes

### Update Image References
```bash
# Update deployment.yaml with your image
sed -i 's|your-registry/s3-connector:v0.9|YOUR_REGISTRY/s3-connector:v0.9|g' \
  deployment/k8s/deployment.yaml
```

### Apply Manifests in Order
```bash
cd deployment/k8s

# 1. RBAC and ServiceAccount
kubectl apply -f rbac.yaml

# 2. ConfigMap
kubectl apply -f configmap.yaml

# 3. Secrets
kubectl apply -f secret.yaml

# 4. Deployment
kubectl apply -f deployment.yaml

# 5. Service (if using)
kubectl apply -f service.yaml

# 6. CronJob for scheduled ingestion
kubectl apply -f cronjob.yaml

# 7. Network Policy (optional, for security)
kubectl apply -f network-policy.yaml
```

---

## ✅ Step 6: Validate Deployment

### Check Pod Status
```bash
# Watch deployment rollout
kubectl rollout status deployment/s3-connector -n openmetadata

# Check pods
kubectl get pods -n openmetadata -l app=s3-connector

# Check logs
kubectl logs -n openmetadata deployment/s3-connector --tail=50
```

### Test Connectivity
```bash
# Exec into pod
kubectl exec -it -n openmetadata deployment/s3-connector -- bash

# Inside pod - test imports
python -c "
from om_s3_connector import S3Connector
print('✅ Connector imports successfully')
"

# Test AWS credentials
python -c "
import boto3
s3 = boto3.client('s3')
print('✅ AWS credentials configured')
"
```

### Test OpenMetadata Connection
```bash
# From inside the pod
curl -f $OPENMETADATA_SERVER_URL/health-check
# Should return: {"status": "OK"}
```

---

## 🔄 Step 7: Configure Ingestion

### Manual Ingestion Test
```bash
# Create a test ingestion config
kubectl exec -n openmetadata deployment/s3-connector -- \
  metadata ingest -c /app/config/ingestion-config.yaml --dry-run
```

### Schedule Regular Ingestion
The CronJob is configured to run every 6 hours. Check its status:
```bash
# View CronJob
kubectl get cronjobs -n openmetadata

# Check CronJob logs
kubectl logs -n openmetadata jobs/s3-connector-ingestion-$(date +%s)
```

---

## 📊 Step 8: Production Monitoring

### Set Up Monitoring
```bash
# Check resource usage
kubectl top pods -n openmetadata -l app=s3-connector

# Monitor deployment
kubectl get events -n openmetadata --field-selector involvedObject.name=s3-connector
```

### Configure Alerts
```yaml
# Example Prometheus alert rule
groups:
- name: s3-connector
  rules:
  - alert: S3ConnectorDown
    expr: up{job="s3-connector"} == 0
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "S3 Connector is down"
```

---

## 🛠️ Troubleshooting Guide

### Common Issues

#### 1. Pod CrashLoopBackOff
```bash
# Check logs
kubectl logs -n openmetadata deployment/s3-connector --previous

# Common causes:
# - Missing environment variables
# - Invalid credentials
# - Network connectivity issues
```

#### 2. Import Errors
```bash
# Verify package installation
kubectl exec -n openmetadata deployment/s3-connector -- \
  pip list | grep openmetadata-s3-connector

# Check Python path
kubectl exec -n openmetadata deployment/s3-connector -- \
  python -c "import sys; print('\n'.join(sys.path))"
```

#### 3. S3 Connection Issues
```bash
# Test S3 connectivity
kubectl exec -n openmetadata deployment/s3-connector -- \
  aws s3 ls s3://your-bucket-name --endpoint-url=YOUR_ENDPOINT
```

#### 4. OpenMetadata API Issues
```bash
# Test API connectivity
kubectl exec -n openmetadata deployment/s3-connector -- \
  curl -f $OPENMETADATA_SERVER_URL/health-check
```

### Debug Commands
```bash
# Get all resources
kubectl get all -n openmetadata -l app=s3-connector

# Describe problematic pod
kubectl describe pod -n openmetadata POD_NAME

# Check events
kubectl get events -n openmetadata --sort-by=.metadata.creationTimestamp

# Enter debug mode
kubectl exec -it -n openmetadata deployment/s3-connector -- /bin/bash
```

---

## 🔄 Updates and Maintenance

### Update Container Image
```bash
# Build new version
docker build -f deployment/Dockerfile.prod -t YOUR_REGISTRY/s3-connector:v0.10 .
docker push YOUR_REGISTRY/s3-connector:v0.10

# Update deployment
kubectl set image deployment/s3-connector -n openmetadata \
  s3-connector=YOUR_REGISTRY/s3-connector:v0.10

# Watch rollout
kubectl rollout status deployment/s3-connector -n openmetadata
```

### Update Configuration
```bash
# Update ConfigMap
kubectl apply -f deployment/k8s/configmap.yaml

# Restart deployment to pick up changes
kubectl rollout restart deployment/s3-connector -n openmetadata
```

---

## 🎯 Next Steps

### 1. **Production Hardening**
- [ ] Set up resource quotas and limits
- [ ] Configure network policies
- [ ] Enable pod security policies
- [ ] Set up backup strategies

### 2. **Monitoring & Observability**
- [ ] Configure Prometheus metrics
- [ ] Set up Grafana dashboards
- [ ] Create alerting rules
- [ ] Enable distributed tracing

### 3. **CI/CD Integration**
- [ ] Automate image builds
- [ ] Set up GitOps with ArgoCD/Flux
- [ ] Configure automated testing
- [ ] Implement blue-green deployments

### 4. **Scaling Considerations**
- [ ] Configure horizontal pod autoscaling
- [ ] Set up cluster autoscaling
- [ ] Optimize resource requests/limits
- [ ] Consider multi-region deployment

---

## 📚 Additional Resources

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [OpenMetadata Ingestion](https://docs.open-metadata.org/connectors)
- [Production Best Practices](./deployment/KUBERNETES_DEPLOYMENT_COMPLETE.md)
- [Security Considerations](./docs/SECURITY.md)

---

## 🆘 Support

If you encounter issues:

1. **Check logs**: `kubectl logs -n openmetadata deployment/s3-connector`
2. **Review events**: `kubectl get events -n openmetadata`
3. **Verify configuration**: Check secrets and configmaps
4. **Test connectivity**: Verify S3 and OpenMetadata access
5. **Contact support**: Create an issue with logs and configuration

---

## ✅ Installation Complete!

Your S3 Connector is now running on Kubernetes! 🎉

**Quick verification checklist:**
- [ ] Pod is running: `kubectl get pods -n openmetadata`
- [ ] Logs show successful startup
- [ ] S3 connectivity tested
- [ ] OpenMetadata API accessible
- [ ] Ingestion job configured and running

For advanced configuration and production setup, refer to the complete deployment guide in `deployment/KUBERNETES_DEPLOYMENT_COMPLETE.md`.
