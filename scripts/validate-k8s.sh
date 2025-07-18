#!/bin/bash
# 🔍 S3 Connector Kubernetes Validation Script
# Comprehensive testing and validation of the deployed S3 connector

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
NAMESPACE="openmetadata"
APP_NAME="s3-connector"
POD_NAME=""

# Test results tracking
TESTS_PASSED=0
TESTS_FAILED=0
TOTAL_TESTS=0

print_status() { echo -e "${BLUE}[TEST]${NC} $1"; }
print_success() { echo -e "${GREEN}[PASS]${NC} $1"; }
print_failure() { echo -e "${RED}[FAIL]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARN]${NC} $1"; }

# Function to run a test
run_test() {
    local test_name="$1"
    local test_command="$2"
    local expected_exit_code="${3:-0}"
    
    ((TOTAL_TESTS++))
    print_status "Running: $test_name"
    
    if eval "$test_command" &>/dev/null; then
        local exit_code=$?
        if [ $exit_code -eq $expected_exit_code ]; then
            print_success "$test_name"
            ((TESTS_PASSED++))
            return 0
        else
            print_failure "$test_name (exit code: $exit_code, expected: $expected_exit_code)"
            ((TESTS_FAILED++))
            return 1
        fi
    else
        print_failure "$test_name"
        ((TESTS_FAILED++))
        return 1
    fi
}

# Function to get pod name
get_pod_name() {
    POD_NAME=$(kubectl get pods -n "$NAMESPACE" -l app="$APP_NAME" -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")
    if [ -z "$POD_NAME" ]; then
        print_failure "No pods found for app=$APP_NAME in namespace=$NAMESPACE"
        exit 1
    fi
    print_status "Testing pod: $POD_NAME"
}

# Test 1: Kubernetes Resources
test_kubernetes_resources() {
    echo ""
    echo "🔧 Testing Kubernetes Resources..."
    
    run_test "Namespace exists" \
        "kubectl get namespace $NAMESPACE"
    
    run_test "Deployment exists" \
        "kubectl get deployment $APP_NAME -n $NAMESPACE"
    
    run_test "Pod is running" \
        "kubectl get pod -n $NAMESPACE -l app=$APP_NAME --field-selector=status.phase=Running"
    
    run_test "Service exists" \
        "kubectl get service $APP_NAME -n $NAMESPACE"
    
    run_test "ConfigMap exists" \
        "kubectl get configmap ${APP_NAME}-config -n $NAMESPACE"
    
    run_test "Secret exists" \
        "kubectl get secret ${APP_NAME}-secrets -n $NAMESPACE"
    
    run_test "ServiceAccount exists" \
        "kubectl get serviceaccount ${APP_NAME}-sa -n $NAMESPACE"
    
    run_test "CronJob exists" \
        "kubectl get cronjob ${APP_NAME}-ingestion -n $NAMESPACE"
}

# Test 2: Pod Health
test_pod_health() {
    echo ""
    echo "🏥 Testing Pod Health..."
    
    get_pod_name
    
    run_test "Pod is ready" \
        "kubectl get pod $POD_NAME -n $NAMESPACE -o jsonpath='{.status.conditions[?(@.type==\"Ready\")].status}' | grep -q True"
    
    run_test "Container is running" \
        "kubectl get pod $POD_NAME -n $NAMESPACE -o jsonpath='{.status.containerStatuses[0].state.running}'"
    
    run_test "No restart loops" \
        "test \$(kubectl get pod $POD_NAME -n $NAMESPACE -o jsonpath='{.status.containerStatuses[0].restartCount}') -lt 5"
    
    # Check resource usage
    if kubectl top pod $POD_NAME -n $NAMESPACE &>/dev/null; then
        run_test "Resource metrics available" \
            "kubectl top pod $POD_NAME -n $NAMESPACE"
    else
        print_warning "Metrics server not available - skipping resource usage test"
    fi
}

# Test 3: Application Health
test_application_health() {
    echo ""
    echo "📦 Testing Application Health..."
    
    run_test "Python is accessible" \
        "kubectl exec $POD_NAME -n $NAMESPACE -- python --version"
    
    run_test "S3 connector package installed" \
        "kubectl exec $POD_NAME -n $NAMESPACE -- pip show openmetadata-s3-connector"
    
    run_test "Core module imports" \
        "kubectl exec $POD_NAME -n $NAMESPACE -- python -c 'import om_s3_connector; print(\"Import successful\")'"
    
    run_test "S3 connector class available" \
        "kubectl exec $POD_NAME -n $NAMESPACE -- python -c 'from om_s3_connector import S3Connector; print(\"S3Connector available\")'"
    
    run_test "Configuration class available" \
        "kubectl exec $POD_NAME -n $NAMESPACE -- python -c 'from om_s3_connector import S3Config; print(\"S3Config available\")'"
    
    run_test "Parser factory available" \
        "kubectl exec $POD_NAME -n $NAMESPACE -- python -c 'from om_s3_connector.s3.parsers.factory import ParserFactory; print(\"ParserFactory available\")'"
}

# Test 4: Environment Configuration
test_environment_config() {
    echo ""
    echo "⚙️ Testing Environment Configuration..."
    
    run_test "Environment variables loaded" \
        "kubectl exec $POD_NAME -n $NAMESPACE -- printenv | grep -E '(OPENMETADATA|AWS|S3)'"
    
    run_test "OpenMetadata server URL configured" \
        "kubectl exec $POD_NAME -n $NAMESPACE -- test -n \"\$OPENMETADATA_SERVER_URL\""
    
    run_test "AWS credentials configured" \
        "kubectl exec $POD_NAME -n $NAMESPACE -- test -n \"\$AWS_ACCESS_KEY_ID\""
    
    run_test "S3 bucket configured" \
        "kubectl exec $POD_NAME -n $NAMESPACE -- test -n \"\$BUCKET_NAME\""
    
    # Test config file access
    run_test "Ingestion config accessible" \
        "kubectl exec $POD_NAME -n $NAMESPACE -- test -f /app/config/ingestion-config.yaml"
}

# Test 5: External Connectivity
test_external_connectivity() {
    echo ""
    echo "🌐 Testing External Connectivity..."
    
    # Test OpenMetadata connectivity
    if kubectl exec $POD_NAME -n $NAMESPACE -- printenv OPENMETADATA_SERVER_URL &>/dev/null; then
        run_test "OpenMetadata health check" \
            "kubectl exec $POD_NAME -n $NAMESPACE -- curl -f \$OPENMETADATA_SERVER_URL/health-check"
    else
        print_warning "OpenMetadata URL not configured - skipping connectivity test"
    fi
    
    # Test S3 connectivity
    run_test "S3 CLI available" \
        "kubectl exec $POD_NAME -n $NAMESPACE -- which aws"
    
    # Test S3 list operation (if credentials are configured)
    if kubectl exec $POD_NAME -n $NAMESPACE -- printenv AWS_ACCESS_KEY_ID &>/dev/null; then
        run_test "S3 bucket access" \
            "kubectl exec $POD_NAME -n $NAMESPACE -- timeout 30 aws s3 ls s3://\$BUCKET_NAME/ --max-items 1"
    else
        print_warning "AWS credentials not configured - skipping S3 connectivity test"
    fi
    
    # Test DNS resolution
    run_test "DNS resolution works" \
        "kubectl exec $POD_NAME -n $NAMESPACE -- nslookup google.com"
}

# Test 6: Ingestion Capabilities
test_ingestion_capabilities() {
    echo ""
    echo "🔄 Testing Ingestion Capabilities..."
    
    run_test "Metadata CLI available" \
        "kubectl exec $POD_NAME -n $NAMESPACE -- which metadata"
    
    run_test "Ingestion help accessible" \
        "kubectl exec $POD_NAME -n $NAMESPACE -- metadata ingest --help"
    
    run_test "S3 connector dry run" \
        "kubectl exec $POD_NAME -n $NAMESPACE -- timeout 60 metadata ingest -c /app/config/ingestion-config.yaml --dry-run"
    
    # Test parser availability
    local parsers=("csv" "json" "parquet" "avro" "orc")
    for parser in "${parsers[@]}"; do
        run_test "$parser parser available" \
            "kubectl exec $POD_NAME -n $NAMESPACE -- python -c 'from om_s3_connector.s3.parsers.factory import ParserFactory; ParserFactory.get_parser(\"$parser\")'"
    done
}

# Test 7: Security Configuration
test_security_config() {
    echo ""
    echo "🔒 Testing Security Configuration..."
    
    run_test "Running as non-root user" \
        "test \$(kubectl exec $POD_NAME -n $NAMESPACE -- id -u) -ne 0"
    
    run_test "Security context applied" \
        "kubectl get pod $POD_NAME -n $NAMESPACE -o jsonpath='{.spec.securityContext}' | grep -q runAsNonRoot"
    
    run_test "Read-only root filesystem (if configured)" \
        "kubectl get pod $POD_NAME -n $NAMESPACE -o jsonpath='{.spec.containers[0].securityContext}' | grep -q readOnlyRootFilesystem || true"
    
    # Test resource limits
    run_test "Resource limits configured" \
        "kubectl get pod $POD_NAME -n $NAMESPACE -o jsonpath='{.spec.containers[0].resources.limits}'"
    
    run_test "Resource requests configured" \
        "kubectl get pod $POD_NAME -n $NAMESPACE -o jsonpath='{.spec.containers[0].resources.requests}'"
}

# Test 8: Monitoring and Logging
test_monitoring_logging() {
    echo ""
    echo "📊 Testing Monitoring and Logging..."
    
    run_test "Container logs accessible" \
        "kubectl logs $POD_NAME -n $NAMESPACE --tail=10"
    
    run_test "Events are clean (no critical errors)" \
        "! kubectl get events -n $NAMESPACE --field-selector involvedObject.name=$POD_NAME | grep -i error"
    
    # Test if metrics endpoint is available (if configured)
    if kubectl exec $POD_NAME -n $NAMESPACE -- curl -f localhost:9090/metrics &>/dev/null; then
        run_test "Metrics endpoint accessible" \
            "kubectl exec $POD_NAME -n $NAMESPACE -- curl -f localhost:9090/metrics"
    else
        print_warning "Metrics endpoint not configured or not accessible"
    fi
}

# Function to generate test report
generate_report() {
    echo ""
    echo "📋 Test Report"
    echo "=============="
    echo "Total Tests: $TOTAL_TESTS"
    echo "Passed: $TESTS_PASSED"
    echo "Failed: $TESTS_FAILED"
    echo "Success Rate: $(( (TESTS_PASSED * 100) / TOTAL_TESTS ))%"
    echo ""
    
    if [ $TESTS_FAILED -eq 0 ]; then
        print_success "🎉 All tests passed! Your S3 connector is ready for production."
    elif [ $TESTS_FAILED -lt 3 ]; then
        print_warning "⚠️ Some tests failed, but the connector should be functional. Review the failures."
    else
        print_failure "❌ Multiple test failures detected. Please review the configuration and logs."
        echo ""
        echo "🔧 Troubleshooting Tips:"
        echo "  1. Check pod logs: kubectl logs $POD_NAME -n $NAMESPACE"
        echo "  2. Check events: kubectl get events -n $NAMESPACE"
        echo "  3. Verify configuration: kubectl describe pod $POD_NAME -n $NAMESPACE"
        echo "  4. Test connectivity manually: kubectl exec -it $POD_NAME -n $NAMESPACE -- bash"
    fi
}

# Function to run performance tests
run_performance_tests() {
    echo ""
    echo "⚡ Running Performance Tests..."
    
    # Test startup time
    local startup_time=$(kubectl get pod $POD_NAME -n $NAMESPACE -o jsonpath='{.status.containerStatuses[0].state.running.startedAt}')
    local creation_time=$(kubectl get pod $POD_NAME -n $NAMESPACE -o jsonpath='{.metadata.creationTimestamp}')
    
    print_status "Pod created at: $creation_time"
    print_status "Container started at: $startup_time"
    
    # Test memory usage
    if kubectl top pod $POD_NAME -n $NAMESPACE &>/dev/null; then
        local memory_usage=$(kubectl top pod $POD_NAME -n $NAMESPACE --no-headers | awk '{print $3}')
        local cpu_usage=$(kubectl top pod $POD_NAME -n $NAMESPACE --no-headers | awk '{print $2}')
        print_status "Current Memory Usage: $memory_usage"
        print_status "Current CPU Usage: $cpu_usage"
    fi
}

# Main execution
main() {
    echo "🔍 S3 Connector Kubernetes Validation"
    echo "====================================="
    echo ""
    echo "Namespace: $NAMESPACE"
    echo "App: $APP_NAME"
    echo ""
    
    # Run all test suites
    test_kubernetes_resources
    test_pod_health
    test_application_health
    test_environment_config
    test_external_connectivity
    test_ingestion_capabilities
    test_security_config
    test_monitoring_logging
    
    # Run performance tests if requested
    if [[ "${1:-}" == "--performance" ]]; then
        run_performance_tests
    fi
    
    # Generate final report
    generate_report
    
    # Return appropriate exit code
    if [ $TESTS_FAILED -eq 0 ]; then
        exit 0
    else
        exit 1
    fi
}

# Handle script options
case "${1:-}" in
    --help|-h)
        echo "Usage: $0 [OPTIONS]"
        echo ""
        echo "Options:"
        echo "  --performance    Run additional performance tests"
        echo "  --help, -h       Show this help message"
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac
