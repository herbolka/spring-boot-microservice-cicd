# API Deployment Architecture

## Quick Start Checklist

- [ ] **Prerequisites Installed**: AWS CLI, Terraform, Docker, kubectl, Python
- [ ] **AWS Configured**: `aws configure` run successfully
- [ ] **Gemini API Key**: Obtained from https://aistudio.google.com/app/apikey
- [ ] **GitHub Secrets**: Set AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, GEMINI_API_KEY
- [ ] **Terraform Initialized**: `cd terraform && terraform init`
- [ ] **Infrastructure Created**: `terraform apply`
- [ ] **kubectl Updated**: AWS EKS credentials configured
- [ ] **First Deployment**: Push to main branch to trigger GitHub Actions

---

## Architecture Components

### 1. Version Control (GitHub)
- Repository for code, Terraform, Kubernetes manifests
- GitHub Actions triggers CI/CD pipeline
- Branch protection on main requires PR reviews

### 2. CI/CD Pipeline (GitHub Actions)
```
Code Push
    ↓
Gemini AI Code Review (Security, Performance, K8s validation)
    ↓
Build & Test (Maven)
    ↓
Docker Build & Push to ECR
    ↓
Terraform Apply (Infrastructure)
    ↓
Deploy to Kubernetes
    ↓
Gemini AI Deployment Validation
    ↓
Health Checks & Monitoring
```

### 3. Infrastructure (AWS + Terraform)
- **VPC**: Isolated network with public/private subnets
- **EKS**: Managed Kubernetes cluster (1.28+)
- **EC2**: Worker nodes (t3.medium, configurable Spot/On-Demand)
- **ECR**: Private Docker registry
- **NAT Gateway**: Secure outbound internet access
- **Security Groups**: Network policies

### 4. Container Registry (ECR)
- Private repository for Docker images
- Automatic image scanning on push
- Lifecycle policy to maintain last 10 images
- Integration with Kubernetes for pulling images

### 5. Orchestration (Kubernetes/EKS)
```
Namespace: production
├── Deployment: currency-conversion-service
│   ├── 3 replicas (minimum)
│   ├── Rolling update strategy
│   ├── Health probes (readiness, liveness, startup)
│   └── Resource limits/requests
├── Service: LoadBalancer (external access)
├── Service: ClusterIP (internal access)
├── HPA: Auto-scaling (2-10 pods)
├── PDB: Pod Disruption Budget (minimum 1 pod)
└── ConfigMap & Secrets: Configuration
```

### 6. Auto-Scaling (HPA - Horizontal Pod Autoscaler)
- **Metrics**: CPU (70%) and Memory (80%)
- **Scale-up**: Within 60 seconds, double pods
- **Scale-down**: After 5 minutes, reduce by 50%
- **Min replicas**: 2 (always running)
- **Max replicas**: 10 (cost control)

### 7. Load Balancing
- **AWS NLB** (Network Load Balancer)
- **Session affinity**: Client IP-based routing
- **Health checks**: Every 10 seconds
- **External IP**: Publicly accessible

### 8. Monitoring & Observability
- **Kubernetes logs**: Captured automatically
- **Health endpoints**: /actuator/health
- **Metrics**: Prometheus-ready (optional)
- **Gemini AI**: AI-powered validation & alerts

---

## Step-by-Step Execution

### Phase 1: ONE-TIME SETUP (30 minutes)

```bash
# 1. Clone repository
git clone https://github.com/YOUR_ORG/currency-microservice.git
cd currency-microservice

# 2. Run setup script
chmod +x scripts/setup.sh
./scripts/setup.sh

# Follow prompts to:
# - Configure AWS credentials
# - Create S3 bucket for Terraform state
# - Set Gemini API key
# - Install Python dependencies

# 3. Initialize Terraform
cd terraform
terraform init
terraform validate

# 4. Plan infrastructure
terraform plan -out=tfplan
# Review the changes. Should show:
# - 1 VPC
# - 2 NAT Gateways
# - 1 EKS Cluster
# - 1 Node Group (2-10 nodes)
# - 1 ECR Repository
# - Various IAM roles and security groups

# 5. Apply infrastructure
terraform apply tfplan
# This takes 10-15 minutes...

# 6. Configure kubectl
$(terraform output -raw configure_kubectl)
# Or: aws eks update-kubeconfig --region us-east-1 --name currency-cluster

# 7. Verify cluster access
kubectl get nodes
kubectl get pods --all-namespaces
```

### Phase 2: FIRST DEPLOYMENT (15 minutes)

```bash
# 1. Push code to GitHub
cd ..
git add .
git commit -m "Initial commit: CI/CD with Gemini AI"
git push -u origin main

# 2. Monitor GitHub Actions
# Go to: https://github.com/YOUR_ORG/currency-microservice/actions
# Watch the workflow execute

# Actions steps:
# 1. Checkout code ✅
# 2. Gemini AI Code Review ✅ (analyzes your code)
# 3. Test & Build ✅ (runs Maven tests)
# 4. Build Docker Image ✅ (creates OCI image)
# 5. Push to ECR ✅ (uploads to AWS)
# 6. Terraform Apply ✅ (updates infrastructure)
# 7. Deploy to Kubernetes ✅ (creates pods)
# 8. Validate Deployment ✅ (Gemini AI checks)

# 3. Verify deployment
kubectl get pods -n production
kubectl get svc -n production
kubectl get hpa -n production

# 4. Get external IP
kubectl get svc currency-conversion-service -n production
# Wait for EXTERNAL-IP to be assigned (2-3 minutes)

# 5. Test application
curl http://EXTERNAL-IP/actuator/health
```

### Phase 3: DAILY DEVELOPMENT (5 minutes per change)

```bash
# 1. Make code changes
vim src/main/java/com/example/MyController.java

# 2. Test locally
mvn test
docker build -t currency-conversion-service:local .
docker run -p 8080:8080 currency-conversion-service:local

# 3. Commit and push (triggers CI/CD automatically)
git add .
git commit -m "feat: Add new endpoint"
git push

# 4. Monitor deployment
# GitHub Actions automatically:
# - Reviews your code with Gemini AI
# - Runs tests
# - Builds Docker image
# - Pushes to ECR
# - Updates Kubernetes
# - Validates deployment

# 5. Check if live
curl http://EXTERNAL-IP/your-new-endpoint
```

---

## Monitoring and Management

### View Deployment Status
```bash
# Pods
kubectl get pods -n production
kubectl logs -n production -l app=currency-conversion --tail=100 -f

# Service
kubectl get svc -n production
kubectl describe svc currency-conversion-service -n production

# HPA Status
kubectl get hpa -n production
kubectl describe hpa currency-conversion-hpa -n production

# Events
kubectl get events -n production
```

### Troubleshooting

**Pods not starting?**
```bash
kubectl describe pod [POD_NAME] -n production
kubectl logs [POD_NAME] -n production
```

**LoadBalancer stuck pending?**
```bash
# AWS ELB takes 2-5 minutes
aws elb describe-load-balancers --region us-east-1
```

**HPA not scaling?**
```bash
# Check if metrics server is running
kubectl get deployment metrics-server -n kube-system

# View HPA metrics
kubectl get hpa -n production
kubectl top pods -n production
```

---

## Cost Optimization

### Current Estimate
- EKS Cluster: $0.10/hour = ~$73/month
- EC2 Nodes (2x t3.medium): ~$60/month
- NAT Gateways (2x): ~$65/month
- ECR: ~$5/month
- **Total**: ~$200/month

### Reduce Costs
```hcl
# 1. Use Spot Instances (70% cheaper)
variable "capacity_type" {
  default = "SPOT"  # Change from "ON_DEMAND"
}

# 2. Smaller instance types
variable "instance_type" {
  default = "t3.small"  # Instead of t3.medium
}

# 3. Delete when not in use
terraform destroy
```

### Production Best Practices
- Use Reserved Instances (30% discount annually)
- Setup CloudWatch alarms for cost monitoring
- Regularly review and delete unused resources
- Use Savings Plans for predictable workloads

---

## Security Considerations

### Current Setup Includes
- ✅ VPC with public/private subnets
- ✅ NAT Gateway for secure outbound access
- ✅ Security Groups with minimal permissions
- ✅ IAM roles with least privilege
- ✅ ECR with privacy and scanning
- ✅ Non-root container user
- ✅ Pod security context
- ✅ RBAC for Kubernetes

### Additional Security (Optional)
- Network Policies: Restrict pod-to-pod communication
- TLS/SSL: Enable in-cluster encryption
- Secrets Manager: Store sensitive data
- VPC Flow Logs: Monitor network traffic
- IAM Policy Analyzer: Audit permissions

---

## Next Steps

1. **Day 1**: Complete Phase 1 setup
2. **Day 2**: Deploy first version (Phase 2)
3. **Day 3**: Run load tests and verify HPA
4. **Week 2**: Implement monitoring (Prometheus/Grafana)
5. **Week 3**: Add alerting and runbooks
6. **Month 1**: Implement canary deployments
7. **Month 2**: Add multi-region failover

---

## Support & Resources

### Documentation
- [COMPREHENSIVE_GUIDE.md](COMPREHENSIVE_GUIDE.md) - Full detailed guide
- [AWS EKS Documentation](https://docs.aws.amazon.com/eks/)
- [Kubernetes Best Practices](https://kubernetes.io/docs/concepts/configuration/overview/)
- [Gemini AI API](https://ai.google.dev/docs)

### Tools
- kubectl: `kubectl help`
- Terraform: `terraform -help`
- AWS CLI: `aws eks help`

### Common Issues
```bash
# Reset everything
cd terraform
terraform destroy -auto-approve  # WARNING: Permanent
cd ..

# Redeploy
./scripts/setup.sh
./scripts/deploy.sh
```

---

**Last Updated**: 2024
**Maintained By**: Your Team
**Version**: 1.0
