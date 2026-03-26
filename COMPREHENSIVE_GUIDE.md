# Advanced CI/CD Pipeline with Gemini AI, GitHub Actions, Terraform, Docker, and Kubernetes on AWS

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Prerequisites](#prerequisites)
3. [Step-by-Step Setup Guide](#step-by-step-setup-guide)
4. [Component Details](#component-details)
5. [Deployment Workflow](#deployment-workflow)
6. [Monitoring and Troubleshooting](#monitoring-and-troubleshooting)
7. [Cost Optimization](#cost-optimization)

---

## Architecture Overview

```
┌──────────────────┐
│  Developer Push  │
│   to GitHub      │
└────────┬─────────┘
         │
         ▼
┌──────────────────────────────┐
│   GitHub Actions Workflow    │
│  ┌────────────────────────┐  │
│  │ 1. Checkout Code       │  │
│  │ 2. Gemini AI Review    │  │
│  │ 3. Run Tests           │  │
│  │ 4. Build Docker Image  │  │
│  │ 5. Push to ECR         │  │
│  └────────────────────────┘  │
└────────┬─────────────────────┘
         │
         ▼
┌──────────────────────────────┐
│   Terraform Provisioning     │
│  ┌────────────────────────┐  │
│  │ Create/Update EKS      │  │
│  │ - VPC & Subnets        │  │
│  │ - EKS Cluster          │  │
│  │ - Node Groups          │  │
│  │ - IAM Roles            │  │
│  │ - ECR Registry         │  │
│  │ - Security Groups      │  │
│  └────────────────────────┘  │
└────────┬─────────────────────┘
         │
         ▼
┌──────────────────────────────┐
│  Kubernetes Deployment       │
│  ┌────────────────────────┐  │
│  │ - Deployment (3 pods)  │  │
│  │ - Service (LoadBal)    │  │
│  │ - HPA (2-10 pods)      │  │
│  │ - ConfigMaps & Secrets │  │
│  └────────────────────────┘  │
└────────┬─────────────────────┘
         │
         ▼
┌──────────────────────────────┐
│   Post-Deployment Validation │
│  ┌────────────────────────┐  │
│  │ Gemini AI Validation   │  │
│  │ Health Checks          │  │
│  │ Integration Tests      │  │
│  │ Notifications          │  │
│  └────────────────────────┘  │
└────────┬─────────────────────┘
         │
         ▼
┌──────────────────────────────┐
│  Application Available       │
│  - External LoadBalancer IP  │
│  - Auto-scaling Active       │
│  - Health Monitoring         │
└──────────────────────────────┘
```

---

## Prerequisites

### AWS Account Requirements
- AWS Account with appropriate permissions
- AWS Credit or billing setup
- Region selection (e.g., us-east-1)

### Local Machine Requirements
```bash
# AWS CLI
aws --version  # v2.x or higher

# Terraform
terraform --version  # v1.5+

# Docker Desktop
docker --version  # 20.10+

# kubectl
kubectl version --client  # v1.24+

# Git
git --version  # 2.x+
```

### GitHub Requirements
- GitHub account with repository access
- Personal Access Token with `repo` and `workflow` scopes
- GitHub Actions enabled in repository

### Google Cloud / Gemini Requirements
- Google Cloud account
- Gemini API key (from Google AI Studio or Vertex AI)
- API enabled: Generative Language API

---

## Step-by-Step Setup Guide

### Phase 1: Local Environment Setup (Day 1)

#### Step 1.1: Install Required Tools

**AWS CLI**
```bash
# Windows (using Chocolatey)
choco install awscli

# Or download from: https://aws.amazon.com/cli/

# Verify installation
aws --version
```

**Terraform**
```bash
# Windows (using Chocolatey)
choco install terraform

# Or download from: https://www.terraform.io/downloads

# Verify installation
terraform --version
```

**Docker Desktop**
```bash
# Download from: https://www.docker.com/products/docker-desktop
# Install and verify
docker --version
docker run hello-world
```

**kubectl**
```bash
# Windows
choco install kubernetes-cli

# Or using AWS CLI
aws eks update-kubeconfig --region us-east-1 --name currency-cluster

# Verify installation
kubectl version --client
```

#### Step 1.2: Configure AWS Credentials

```bash
# Configure AWS CLI with your credentials
aws configure

# When prompted, enter:
# AWS Access Key ID: [your-access-key]
# AWS Secret Access Key: [your-secret-key]
# Default region: us-east-1
# Default output format: json

# Verify credentials
aws sts get-caller-identity

# Expected output:
{
    "UserId": "AIDAI...",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/your-username"
}
```

#### Step 1.3: Get Gemini API Key

```bash
# Option 1: Using Google AI Studio (Easiest)
# 1. Go to https://aistudio.google.com/app/apikey
# 2. Click "Create API key"
# 3. Create new API key in default project
# 4. Copy the API key

# Option 2: Using Vertex AI (for production)
# 1. Go to Google Cloud Console
# 2. Enable Vertex AI API
# 3. Create service account
# 4. Generate JSON key

# Store securely in GitHub Secrets
# Repository → Settings → Secrets and variables → Actions → New repository secret
# Name: GEMINI_API_KEY
# Value: your-api-key-here
```

### Phase 2: GitHub Repository Setup (Day 1)

#### Step 2.1: Clone and Configure Repository

```bash
# Create workspace directory
mkdir ~/projects/currency-microservice
cd ~/projects/currency-microservice

# Clone the Spring Boot example
git clone https://github.com/in28minutes/spring-boot-examples.git .
cd spring-boot-microservice-cicd

# Or clone your existing repo
git clone https://github.com/YOUR_USERNAME/currency-microservice.git
cd currency-microservice
```

#### Step 2.2: Add SSH Key to GitHub

```bash
# Generate SSH key (if you don't have one)
ssh-keygen -t ed25519 -C "your-email@example.com"

# Copy public key
cat ~/.ssh/id_ed25519.pub

# Add to GitHub:
# Settings → SSH and GPG keys → New SSH key
# Paste the public key

# Test connection
ssh -T git@github.com
```

#### Step 2.3: Create GitHub Secrets

Navigate to your repository → Settings → Secrets and variables → Actions

Create these secrets:

```
# AWS Credentials
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
AWS_REGION=us-east-1

# Gemini AI
GEMINI_API_KEY

# Docker Registry (if using custom registry)
DOCKER_REGISTRY_URL
DOCKER_USERNAME
DOCKER_PASSWORD

# Notifications
SLACK_WEBHOOK_URL (optional)
EMAIL_NOTIFICATION (optional)
```

### Phase 3: AWS Infrastructure Setup (Day 1-2)

#### Step 3.1: Prepare AWS Environment

```bash
# Create S3 bucket for Terraform state
aws s3api create-bucket \
  --bucket currency-microservice-tf-state-$(date +%s) \
  --region us-east-1

# Enable versioning on the bucket
aws s3api put-bucket-versioning \
  --bucket currency-microservice-tf-state-[TIMESTAMP] \
  --versioning-configuration Status=Enabled

# Create DynamoDB table for Terraform state locking
aws dynamodb create-table \
  --table-name terraform-locks-currency-service \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
  --region us-east-1
```

#### Step 3.2: Update Terraform Configuration

Update `terraform/backend.tf`:
```hcl
terraform {
  backend "s3" {
    bucket         = "currency-microservice-tf-state-[TIMESTAMP]"
    key            = "prod/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks-currency-service"
  }
}
```

Update `terraform/variables.tf` with your values:
```hcl
variable "aws_region" {
  default = "us-east-1"
}

variable "cluster_name" {
  default = "currency-cluster"
}

variable "environment" {
  default = "production"
}

variable "vpc_cidr" {
  default = "10.0.0.0/16"
}
```

#### Step 3.3: Initialize and Plan Terraform

```bash
cd terraform

# Initialize Terraform
terraform init

# Validate configuration
terraform validate

# Plan infrastructure creation
terraform plan -out=tfplan

# Review the plan output for any errors
```

**Expected output includes:**
- 1 VPC
- 2 Subnets
- 1 EKS Cluster
- 1 Node Group (with 2-3 nodes)
- 2 IAM Roles
- Various security groups
- ECR Registry

### Phase 4: GitHub Actions Workflow Setup (Day 2)

#### Step 4.1: Create Workflow Directory

```bash
mkdir -p .github/workflows
```

#### Step 4.2: Create CI/CD Workflow File

See `workflows/deploy-with-gemini.yml` for the complete workflow configuration.

Key stages:
1. **Code Review with Gemini AI**
   - Analyzes code changes
   - Checks for security issues
   - Reviews Docker configuration
   - Validates Kubernetes manifests

2. **Build and Test**
   - Run unit tests
   - Build Docker image
   - Push to ECR

3. **Infrastructure Update**
   - Apply Terraform changes
   - Update Kubernetes configuration

4. **Deployment**
   - Update deployment manifests
   - Apply Kubernetes changes
   - Wait for rollout

5. **Validation**
   - Post-deployment tests
   - Health checks
   - Gemini AI validation

### Phase 5: Kubernetes Manifests (Day 2)

#### Step 5.1: Configure Namespace

Create `k8s/namespace.yml`:
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: production
  labels:
    name: production
```

#### Step 5.2: Configure Deployment

See `k8s/deployment.yml` for complete configuration with:
- Health checks (readiness & liveness probes)
- Resource requests/limits
- Environment variables
- Volume mounts
- Security context

#### Step 5.3: Configure Service

See `k8s/service.yml` for LoadBalancer configuration

#### Step 5.4: Configure HPA

See `k8s/hpa.yml` for autoscaling rules:
- Min replicas: 2
- Max replicas: 10
- CPU target: 70%
- Memory target: 80%

### Phase 6: Docker Configuration (Day 2)

#### Step 6.1: Create Multistage Dockerfile

```dockerfile
# Build stage
FROM maven:3.8-openjdk-11 as builder
WORKDIR /build
COPY . .
RUN mvn clean package -DskipTests

# Runtime stage
FROM openjdk:11-jre-slim
WORKDIR /app
COPY --from=builder /build/target/*.jar app.jar
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8080/actuator/health || exit 1
ENTRYPOINT ["java", "-jar", "/app.jar"]
```

---

## Component Details

### GitHub Actions Workflow Details

#### Trigger Events
```yaml
on:
  push:
    branches: [main, develop]
    paths:
      - 'src/**'
      - 'pom.xml'
      - 'Dockerfile'
      - 'k8s/**'
      - '.github/workflows/**'
  pull_request:
    branches: [main]
```

#### Gemini AI Integration

**Code Review Function:**
```python
def review_code_with_gemini(changes, gemini_api_key):
    """
    Sends code changes to Gemini AI for review
    
    Returns:
    - Security issues
    - Performance concerns
    - Best practice violations
    - Kubernetes manifest issues
    """
    prompt = f"""
    Review the following code changes for:
    1. Security vulnerabilities
    2. Performance issues
    3. Best practices violations
    4. Docker/Kubernetes misconfigurations
    5. Dependency vulnerabilities
    
    Changes:
    {changes}
    
    Provide a structured analysis with severity levels.
    """
```

**Deployment Validation Function:**
```python
def validate_deployment_with_gemini(deployment_status, logs, gemini_api_key):
    """
    Validates deployment success using Gemini AI
    
    Checks:
    - All pods running
    - No errors in logs
    - Health checks passing
    - Response times acceptable
    """
```

### Terraform Configuration Details

#### EKS Cluster Configuration

```hcl
# Cluster features
resource "aws_eks_cluster" "main" {
  name     = var.cluster_name
  role_arn = aws_iam_role.eks_cluster_role.arn
  
  vpc_config {
    subnet_ids              = aws_subnet.eks_subnet[*].id
    endpoint_private_access = true
    endpoint_public_access  = true
  }
  
  # Enable relevant cluster add-ons
  enabled_cluster_log_types = [
    "api",
    "audit",
    "authenticator",
    "controllerManager",
    "scheduler"
  ]
}
```

#### Node Group Configuration

```hcl
resource "aws_eks_node_group" "main" {
  cluster_name    = aws_eks_cluster.main.name
  node_group_name = "${var.cluster_name}-ng"
  node_role_arn   = aws_iam_role.eks_node_role.arn
  subnet_ids      = aws_subnet.eks_subnet[*].id
  
  scaling_config {
    desired_size = 2
    max_size     = 10
    min_size     = 2
  }
  
  instance_types = ["t3.medium"]  # or "t3.large" for production
  
  tags = {
    Name = "${var.cluster_name}-node-group"
  }
}
```

#### ECR Registry

```hcl
resource "aws_ecr_repository" "microservice" {
  name                 = "currency-conversion-service"
  image_tag_mutability = "IMMUTABLE"
  
  image_scanning_configuration {
    scan_on_push = true
  }
  
  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_ecr_lifecycle_policy" "microservice" {
  repository = aws_ecr_repository.microservice.name
  
  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 10 images"
        selection = {
          tagStatus     = "any"
          countType     = "imageCountMoreThan"
          countNumber   = 10
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}
```

### Kubernetes Configuration Details

#### Deployment with Health Checks

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: currency-conversion-service
  namespace: production
  labels:
    app: currency-conversion
    version: v1
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: currency-conversion
  template:
    metadata:
      labels:
        app: currency-conversion
        version: v1
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8080"
        prometheus.io/path: "/actuator/prometheus"
    spec:
      serviceAccountName: currency-service-account
      containers:
      - name: currency-conversion
        image: [AWS_ACCOUNT_ID].dkr.ecr.us-east-1.amazonaws.com/currency-conversion-service:latest
        imagePullPolicy: Always
        ports:
        - containerPort: 8080
          name: http
          protocol: TCP
        
        # Resource management
        resources:
          requests:
            cpu: 100m
            memory: 256Mi
          limits:
            cpu: 500m
            memory: 512Mi
        
        # Readiness probe
        readinessProbe:
          httpGet:
            path: /actuator/health/readiness
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        
        # Liveness probe
        livenessProbe:
          httpGet:
            path: /actuator/health/liveness
            port: 8080
          initialDelaySeconds: 60
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        
        # Startup probe (for slow-starting applications)
        startupProbe:
          httpGet:
            path: /actuator/health
            port: 8080
          periodSeconds: 5
          failureThreshold: 30
        
        # Environment variables
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: LOG_LEVEL
          value: "INFO"
        - name: CURRENCY_SERVICE_URL
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: currency-service-url
        
        # Security context
        securityContext:
          allowPrivilegeEscalation: false
          runAsNonRoot: true
          runAsUser: 1000
          readOnlyRootFilesystem: true
          capabilities:
            drop:
            - ALL
        
        # Volume mounts
        volumeMounts:
        - name: temp
          mountPath: /tmp
        - name: logs
          mountPath: /var/log
      
      # Pod-level settings
      restartPolicy: Always
      terminationGracePeriodSeconds: 30
      securityContext:
        fsGroup: 1000
      
      volumes:
      - name: temp
        emptyDir: {}
      - name: logs
        emptyDir: {}
```

#### Service Configuration

```yaml
apiVersion: v1
kind: Service
metadata:
  name: currency-conversion-service
  namespace: production
  labels:
    app: currency-conversion
spec:
  type: LoadBalancer
  selector:
    app: currency-conversion
  ports:
  - name: http
    port: 80
    targetPort: 8080
    protocol: TCP
  sessionAffinity: ClientIP
  sessionAffinityConfig:
    clientIP:
      timeoutSeconds: 3600
  loadBalancerSourceRanges: []  # Restrict if needed
```

#### HPA Configuration

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: currency-conversion-hpa
  namespace: production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: currency-conversion-service
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 30
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
```

---

## Deployment Workflow

### Complete Deployment Flow Example

#### Step 1: Developer Workflow

```bash
# 1. Create feature branch
git checkout -b feature/new-currency-endpoint

# 2. Make code changes
echo "Feature implementation..." > src/main/java/com/example/NewFeature.java

# 3. Test locally
mvn test

# 4. Build Docker image locally
docker build -t currency-conversion-service:local .
docker run -p 8080:8080 currency-conversion-service:local

# 5. Commit and push
git add .
git commit -m "feat: Add new currency endpoint"
git push origin feature/new-currency-endpoint
```

#### Step 2: GitHub Actions Trigger

Workflow automatically triggers on push:

```
Event: push to feature/new-currency-endpoint
├─ Checkout code
├─ Gemini AI Code Review
│  ├─ Security analysis
│  ├─ Performance review
│  ├─ Dependency check
│  └─ Report findings
├─ Run Tests
├─ Build Docker Image
├─ Push to ECR
├─ Update Terraform
├─ Apply Infrastructure Changes
├─ Deploy to Kubernetes
├─ Validate Deployment
└─ Send Notifications
```

#### Step 3: Gemini AI Analyzes Changes

```
Gemini Review Output:
✓ No security vulnerabilities found
✓ Code follows Spring Boot best practices
⚠ Consider adding caching for performance
✓ Docker image optimized correctly
✓ Kubernetes manifests valid
Recommendation: APPROVE
```

#### Step 4: Infrastructure Update

```bash
# Terraform applies changes automatically:
terraform apply -auto-approve

# Updates or creates:
- Load balancer rules
- Security groups for new ports
- ECR repository tags
```

#### Step 5: Kubernetes Deployment

```bash
# Automatic steps:
1. Pull new image from ECR
2. Create new replica set
3. Start 1 new pod
4. Wait for readiness probe
5. Send traffic to new pod
6. Gradually terminate old pods
7. Final state: 3 pods running new version
```

#### Step 6: Post-Deployment Validation

```
Gemini Validation:
✓ All 3 pods running
✓ Health checks passing
✓ Endpoints responding
✓ No errors in logs
✓ Response times < 200ms
✓ Ready for production

Result: DEPLOYMENT SUCCESSFUL
```

### Manual Tested Deployment

```bash
# If you want to deploy manually instead of via GitHub Actions:

# 1. Authenticate with ECR
aws ecr get-login-password --region us-east-1 | docker login \
  --username AWS \
  --password-stdin [AWS_ACCOUNT_ID].dkr.ecr.us-east-1.amazonaws.com

# 2. Build and push Docker image
docker build -t currency-conversion-service:v1.0.0 .
docker tag currency-conversion-service:v1.0.0 \
  [AWS_ACCOUNT_ID].dkr.ecr.us-east-1.amazonaws.com/currency-conversion-service:v1.0.0
docker push [AWS_ACCOUNT_ID].dkr.ecr.us-east-1.amazonaws.com/currency-conversion-service:v1.0.0

# 3. Update kubeconfig
aws eks update-kubeconfig \
  --region us-east-1 \
  --name currency-cluster

# 4. Apply Kubernetes manifests
kubectl apply -f k8s/namespace.yml
kubectl apply -f k8s/deployment.yml
kubectl apply -f k8s/service.yml
kubectl apply -f k8s/hpa.yml

# 5. Check deployment status
kubectl rollout status deployment/currency-conversion-service -n production
kubectl get pods -n production
kubectl get svc -n production
```

---

## Monitoring and Troubleshooting

### View Deployment Status

```bash
# Check deployment rollout status
kubectl rollout status deployment/currency-conversion-service -n production

# View all pods
kubectl get pods -n production
kubectl get pods -n production -o wide

# View pod details
kubectl describe pod [POD_NAME] -n production

# View logs
kubectl logs [POD_NAME] -n production
kubectl logs [POD_NAME] -n production --tail=100 -f

# View events
kubectl get events -n production

# View HPA status
kubectl get hpa -n production
kubectl describe hpa currency-conversion-hpa -n production
```

### Troubleshooting Common Issues

#### Issue 1: Pods Not Starting

```bash
# Check pod status and events
kubectl describe pod currency-conversion-service-xxxxx -n production

# Common causes:
# - Image pull errors: Check ECR credentials
# - Resource limits: Increase node capacity
# - Health check failures: Check application logs

# Solution: Check logs
kubectl logs currency-conversion-service-xxxxx -n production
```

#### Issue 2: LoadBalancer Pending

```bash
# Check service status
kubectl get svc -n production
kubectl describe svc currency-conversion-service -n production

# It takes 2-3 minutes to provision
# If stuck after 5 minutes:
aws elb describe-load-balancers --region us-east-1
```

#### Issue 3: HPA Not Scaling

```bash
# Check HPA metrics
kubectl get hpa -n production
kubectl describe hpa currency-conversion-hpa -n production

# Check metrics-server is running
kubectl get deployment metrics-server -n kube-system

# If not running, install it
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# Generate load to test HPA
kubectl run -i --tty load-generator --rm --image=busybox --restart=Never -- /bin/sh -c "while sleep 0.01; do wget -q -O- http://currency-conversion-service.production.svc.cluster.local; done"
```

#### Issue 4: Gemini AI Not Reviewing

```bash
# Check if API key is set
echo $GEMINI_API_KEY

# Check GitHub workflow logs
# Repository → Actions → Latest Workflow → Error logs

# Verify API key in GitHub Secrets
# Repository → Settings → Secrets and variables → Actions

# Test API key locally:
curl -X POST "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=$GEMINI_API_KEY" \
  -H "Content-Type: application/json" \
  -d {"contents":[{"parts":[{"text":"Test"}]}]}
```

### Monitoring Metrics

#### Key Metrics to Monitor

```bash
# CPU and Memory usage
kubectl top pods -n production
kubectl top nodes

# Network traffic
kubectl exec -it [POD_NAME] -n production -- netstat -an | grep ESTABLISHED

# Check resource quotas
kubectl describe resourcequota -n production

# Monitor deployments
watch kubectl get deployment -n production
```

#### Setting Up Prometheus (Optional)

```bash
# Add Prometheus Helm repository
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Install Prometheus
helm install prometheus prometheus-community/kube-prometheus-stack \
  -n monitoring \
  --create-namespace

# Access Prometheus
kubectl port-forward svc/prometheus-kube-prometheus-prometheus -n monitoring 9090:9090

# Access Grafana
kubectl port-forward svc/prometheus-grafana -n monitoring 3000:80
# Default credentials: admin/prom-operator
```

---

## Cost Optimization

### Cost Estimation (AWS)
- EKS Cluster: $0.10/hour = ~$73/month
- t3.medium Nodes (2): $0.0416/hour each = ~$62/month
- NAT Gateway: $0.045/hour + data costs
- LoadBalancer: $0.025/hour + data costs
- ECR Storage: $0.10 per GB/month

**Total Estimate: ~$200-300/month**

### Cost Optimization Strategies

```bash
# 1. Spot Instances (70% cheaper)
# Update node group to use spot instances
variable "instance_types" {
  default = ["t3.medium", "t3a.medium"]  # Multiple types for flexibility
}

resource "aws_eks_node_group" "spot" {
  capacity_type = "SPOT"  # Use spot instances
}

# 2. Cluster Autoscaler (scale down unused nodes)
# See scripts/setup-cluster-autoscaler.sh

# 3. Resource requests/limits (right-sizing)
# Ensure containers don't waste resources
# See k8s/deployment.yml for examples

# 4. Delete test clusters when not in use
terraform destroy

# 5. Use reserved instances for long-term deployments
# Purchase 1-year RIs for 30% savings
```

### Cleanup Commands

```bash
# Stop without destroying infrastructure
# Reduce node group to 0 temporarily
aws eks describe-nodegroup --cluster-name currency-cluster --nodegroup-name currency-cluster-ng --region us-east-1

# Destroy everything (WARNING: Permanent)
cd terraform
terraform destroy -auto-approve

# Clean up ECR images
aws ecr batch-delete-image \
  --repository-name currency-conversion-service \
  --image-ids imageTag=old-version
```

---

## Additional Resources

### Recommended Reading
- [AWS EKS Documentation](https://docs.aws.amazon.com/eks/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [Kubernetes Best Practices](https://kubernetes.io/docs/concepts/configuration/overview/)
- [Gemini AI Docs](https://ai.google.dev/docs)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

### Useful Tools
- `kubectx`: Switch between clusters and namespaces
- `helm`: Kubernetes package manager
- `eksctl`: Alternative EKS cluster management
- `kube-bench`: Kubernetes security audits
- `k9s`: Terminal UI for Kubernetes

### Security Best Practices
1. Use IAM roles instead of access/secret keys
2. Enable encryption at rest and in transit
3. Use Pod Security Policies
4. Implement Network Policies
5. Regular security audits
6. Keep images up-to-date

---

## Next Steps

1. **Immediate (Day 1)**
   - Set up local environment
   - Configure AWS credentials
   - Get Gemini API key
   - Create GitHub secrets

2. **Short-term (Day 2)**
   - Deploy Terraform infrastructure
   - Set up GitHub Actions workflow
   - Deploy first version to Kubernetes
   - Test manual workflow

3. **Medium-term (Week 2)**
   - Set up monitoring (Prometheus/Grafana)
   - Implement alerting
   - Test disaster recovery
   - Document runbooks

4. **Long-term (Month 1+)**
   - Implement canary deployments
   - Set up multi-region failover
   - Implement GitOps (ArgoCD)
   - Implement service mesh (Istio)

