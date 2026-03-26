#!/bin/bash

# Test deployment script
# Simulates traffic to test HPA scaling behavior

set -e

NAMESPACE="production"
SERVICE_NAME="currency-conversion-service"

print_info() {
    echo "ℹ️  $1"
}

print_success() {
    echo "✅ $1"
}

# Get LoadBalancer IP
print_info "Getting LoadBalancer IP/hostname..."
LB_ADDRESS=$(kubectl get svc "$SERVICE_NAME" -n "$NAMESPACE" \
    -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' || \
    kubectl get svc "$SERVICE_NAME" -n "$NAMESPACE" \
    -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

if [ -z "$LB_ADDRESS" ]; then
    # Use port-forward instead
    print_info "LoadBalancer not ready. Using port-forward instead..."
    kubectl port-forward svc/"$SERVICE_NAME" 8080:80 -n "$NAMESPACE" &
    sleep 3
    LB_ADDRESS="localhost:8080"
fi

print_success "Service address: $LB_ADDRESS"

# Generate load
print_info "Generating load to test auto-scaling..."
print_info "Press Ctrl+C to stop"

# Create load generator pod
kubectl run load-generator \
    --image=busybox:1.28 \
    --restart=Never \
    --rm -it \
    -n "$NAMESPACE" \
    -- /bin/sh -c "while true; do wget -q -O- http://$SERVICE_NAME/; done"

print_success "Load test completed"
