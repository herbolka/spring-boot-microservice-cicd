#!/bin/bash

# Deploy script to manually deploy the application to Kubernetes
# This is useful for testing outside of GitHub Actions

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Configuration
NAMESPACE="production"
DEPLOYMENT="currency-conversion-service"
IMAGE_TAG=${1:-"latest"}
AWS_REGION=${2:-"us-east-1"}
CLUSTER_NAME=${3:-"currency-cluster"}

echo "==============================================="
echo "Kubernetes Deployment Script"
echo "==============================================="
echo ""
print_info "Deployment Configuration:"
echo "  Namespace: $NAMESPACE"
echo "  Deployment: $DEPLOYMENT"
echo "  Image Tag: $IMAGE_TAG"
echo "  AWS Region: $AWS_REGION"
echo "  Cluster Name: $CLUSTER_NAME"
echo ""

# Step 1: Get AWS credentials and login to ECR
print_info "Step 1: Logging in to ECR..."
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$ECR_REGISTRY"
print_success "Logged in to ECR"

# Step 2: Build Docker image
print_info "Step 2: Building Docker image..."
docker build -t "$DEPLOYMENT:$IMAGE_TAG" .
docker tag "$DEPLOYMENT:$IMAGE_TAG" "$ECR_REGISTRY/$DEPLOYMENT:$IMAGE_TAG"
print_success "Docker image built"

# Step 3: Push to ECR
print_info "Step 3: Pushing image to ECR..."
docker push "$ECR_REGISTRY/$DEPLOYMENT:$IMAGE_TAG"
print_success "Image pushed to ECR: $ECR_REGISTRY/$DEPLOYMENT:$IMAGE_TAG"

# Step 4: Update kubeconfig
print_info "Step 4: Configuring kubectl..."
aws eks update-kubeconfig \
    --region "$AWS_REGION" \
    --name "$CLUSTER_NAME"
print_success "kubectl configured"

# Step 5: Create namespace if not exists
print_info "Step 5: Creating namespace (if needed)..."
kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
print_success "Namespace ready"

# Step 6: Create ECR secret
print_info "Step 6: Creating ECR authentication secret..."
kubectl delete secret ecr-secret -n "$NAMESPACE" 2>/dev/null || true
kubectl create secret docker-registry ecr-secret \
    --docker-server="$ECR_REGISTRY" \
    --docker-username=AWS \
    --docker-password="$(aws ecr get-login-password --region "$AWS_REGION")" \
    -n "$NAMESPACE"
print_success "ECR secret created"

# Step 7: Update deployment image
print_info "Step 7: Updating deployment manifests..."
cp k8s/deployment.yml k8s/deployment.yml.bak
sed -i.bak "s|<your-docker-registry>/currency-conversion-service:latest|$ECR_REGISTRY/$DEPLOYMENT:$IMAGE_TAG|g" k8s/deployment.yml
print_success "Deployment manifest updated"

# Step 8: Apply Kubernetes manifests
print_info "Step 8: Applying Kubernetes manifests..."
kubectl apply -f k8s/namespace.yml
kubectl apply -f k8s/configmap.yml
kubectl apply -f k8s/deployment.yml
kubectl apply -f k8s/service.yml
kubectl apply -f k8s/hpa.yml
print_success "Kubernetes manifests applied"

# Step 9: Wait for rollout
print_info "Step 9: Waiting for deployment rollout..."
kubectl rollout status deployment/"$DEPLOYMENT" -n "$NAMESPACE" --timeout=5m
print_success "Deployment rollout complete"

# Step 10: Get deployment info
echo ""
print_info "Deployment Information:"
echo ""
kubectl get pods -n "$NAMESPACE" -l app=currency-conversion
echo ""

# Get LoadBalancer info
LB_STATUS=$(kubectl get svc "$DEPLOYMENT" -n "$NAMESPACE" -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "Pending")

if [ "$LB_STATUS" = "Pending" ] || [ -z "$LB_STATUS" ]; then
    print_info "LoadBalancer hostname is pending. It may take 2-5 minutes to be assigned."
    echo "  Run: kubectl get svc $DEPLOYMENT -n $NAMESPACE"
else
    print_success "LoadBalancer Address: $LB_STATUS"
fi

echo ""
print_info "Useful commands:"
echo "  View pods:        kubectl get pods -n $NAMESPACE"
echo "  View logs:        kubectl logs -n $NAMESPACE -l app=currency-conversion --tail=100 -f"
echo "  Describe pod:     kubectl describe pod [POD_NAME] -n $NAMESPACE"
echo "  Check HPA:        kubectl get hpa -n $NAMESPACE"
echo "  Port forward:     kubectl port-forward svc/$DEPLOYMENT 8080:80 -n $NAMESPACE"
echo ""

print_success "Deployment complete!"
