# Troubleshooting Guide

Common issues and solutions for the CI/CD pipeline with Gemini AI, GitHub Actions, Terraform, and Kubernetes.

## Table of Contents
1. [GitHub Actions Issues](#github-actions-issues)
2. [AWS/Terraform Issues](#awsterraform-issues)
3. [Kubernetes Issues](#kubernetes-issues)
4. [Gemini AI Issues](#gemini-ai-issues)
5. [Docker Issues](#docker-issues)
6. [General Issues](#general-issues)

---

## GitHub Actions Issues

### Workflow Not Triggering

**Problem**: Pushed code but GitHub Actions workflow didn't start

**Solutions**:
```bash
# 1. Check workflow file is in correct location
ls -la .github/workflows/deploy-with-gemini.yml

# 2. Verify workflow isn't disabled
# Go to: Repository → Actions → Check workflow status

# 3. Verify branch matches trigger
# Workflow triggers on: push to main/develop
git branch  # Confirm you're on main or develop

# 4. Check file paths in workflow
# Workflow triggers on changes to:
# - src/**
# - pom.xml
# - Dockerfile
# - k8s/**
# - .github/workflows/**

# 5. Try manual trigger
# Go to: Repository → Actions → Deploy workflow → Run workflow

# 6. Check GitHub secrets are configured
# Repository → Settings → Secrets and variables → Actions
```

### Workflow Timeout

**Problem**: Workflow exceeded 6-hour timeout

**Solutions**:
```yaml
# 1. Add timeout-minutes to job
jobs:
  build:
    timeout-minutes: 30  # Limit job duration
    runs-on: ubuntu-latest

# 2. Increase container timeout
docker:
  timeout: 600  # 10 minutes

# 3. Reduce scope of analysis
--include-security: false  # Skip optional reviews
```

### Insufficient Permissions

**Problem**: GitHub Actions can't access AWS

**Solutions**:
```bash
# 1. Check GitHub Secrets are set
# Repository → Settings → Secrets and variables → Actions
# Must have:
# - AWS_ACCESS_KEY_ID
# - AWS_SECRET_ACCESS_KEY

# 2. Verify IAM user has permissions
aws iam list-user-policies --user-name your-github-user

# 3. Use IAM role instead of keys (more secure)
# Update workflow to use role-to-assume
- name: Configure AWS credentials
  uses: aws-actions/configure-aws-credentials@v2
  with:
    role-to-assume: arn:aws:iam::ACCOUNT_ID:role/GitHubRole
    aws-region: us-east-1

# 4. Required IAM permissions:
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecr:*",
        "eks:*",
        "iam:*",
        "ec2:*",
        "vpc:*",
        "terraform:*"
      ],
      "Resource": "*"
    }
  ]
}
```

### PR Comments Not Appearing

**Problem**: Automation doesn't comment on pull requests

**Solutions**:
```bash
# 1. Check GITHUB_TOKEN permission
# Repository → Settings → Actions → General
# Workflow permissions: "Read and write permissions"

# 2. Verify job has correct permissions
jobs:
  code-review:
    permissions:
      pull-requests: write
      contents: read

# 3. Check if error in comment creation
# Look at GitHub Actions logs for error message

# 4. Verify PR is from same repository
# Comments only work on same-repo PRs
```

---

## AWS/Terraform Issues

### AWS Credentials Not Found

**Problem**: Terraform can't authenticate with AWS

**Solutions**:
```bash
# 1. Configure credentials
aws configure
# Enter: Access Key ID, Secret Access Key, Region, Output format

# 2. Verify credentials work
aws sts get-caller-identity
# Should show: UserId, Account, Arn

# 3. Check environment variables
echo $AWS_ACCESS_KEY_ID
echo $AWS_SECRET_ACCESS_KEY

# 4. On GitHub Actions, ensure secrets are set
export AWS_ACCESS_KEY_ID=${{ secrets.AWS_ACCESS_KEY_ID }}
export AWS_SECRET_ACCESS_KEY=${{ secrets.AWS_SECRET_ACCESS_KEY }}

# 5. Use AWS profile
aws configure --profile custom-profile
terraform {
  backend "s3" {
    profile = "custom-profile"
  }
}
```

### Terraform State Lock

**Problem**: "Error: Error acquiring the lock"

**Solutions**:
```bash
# 1. Wait 10 minutes for lock to timeout automatically

# 2. Force unlock (CAUTION: Can cause issues)
terraform force-unlock LOCK_ID

# 3. Check DynamoDB table
aws dynamodb scan --table-name terraform-locks-currency-service

# 4. Delete stuck lock
aws dynamodb delete-item \
  --table-name terraform-locks-currency-service \
  --key '{"LockID":{"S":"currency-cluster"}}'
```

### S3 Backend Not Found

**Problem**: "Error: bucket does not exist"

**Solutions**:
```bash
# 1. Check S3 bucket exists
aws s3 ls | grep terraform

# 2. Create bucket if missing
aws s3api create-bucket \
  --bucket currency-microservice-tf-state-$(date +%s) \
  --region us-east-1

# 3. Update backend.tf with correct bucket name
terraform {
  backend "s3" {
    bucket = "your-correct-bucket-name"
    ...
  }
}

# 4. Re-initialize Terraform
terraform init
```

### EKS Creation Timeout

**Problem**: "Timeout waiting for cluster to be in ACTIVE state"

**Solutions**:
```bash
# 1. Check cluster status in AWS Console
aws eks describe-cluster --name currency-cluster --region us-east-1

# 2. Wait and retry (EKS takes 10-15 minutes)
terraform apply -auto-approve

# 3. Check for errors in cluster events
aws eks describe-cluster-logging --cluster-name currency-cluster

# 4. Check IAM role has correct permissions
aws iam get-role-policy --role-name currency-cluster-eks-cluster-role \
  --policy-name AmazonEKSClusterPolicy

# 5. Delete and retry if stuck
terraform destroy -auto-approve
terraform apply -auto-approve
```

### Not Enough Capacity

**Problem**: "InsufficientInstanceCapacity"

**Solutions**:
```bash
# 1. Change region or availability zone
variable "aws_region" {
  default = "us-east-2"  # Try different region
}

# 2. Try different instance type
variable "instance_type" {
  default = "t3.small"  # Smaller or different family
}

# 3. Add retry logic
resource "aws_eks_node_group" "main" {
  ...
  tags = {
    retry = "1"
  }
}

# 4. Wait and retry
sleep 300
terraform apply -auto-approve
```

### Exceeded AWS Limits

**Problem**: "LimitExceededException"

**Solutions**:
```bash
# 1. Request limit increase
# AWS Console → Service Quotas → Search for service limit

# 2. Reduce resource limits in terraform/variables.tf
variable "max_size" {
  default = 5  # Reduced from 10
}

variable "desired_capacity" {
  default = 1  # Reduced from 2
}

# 3. Use smaller instance types
variable "instance_type" {
  default = "t3.micro"  # Much smaller
}

# 4. Clean up other AWS resources
aws ec2 describe-instances
aws rds describe-db-instances
```

---

## Kubernetes Issues

### Pods Not Starting

**Problem**: `kubectl get pods` shows pods stuck in `Pending` or `CrashLoopBackOff`

**Solutions**:
```bash
# 1. Describe the pod for more info
kubectl describe pod [POD_NAME] -n production

# 2. Check for image pull errors
# Look for: "ImagePullBackOff"
kubectl get events -n production

# 3. Check ECR credentials
kubectl get secret ecr-secret -n production -o yaml

# 4. Manually re-create secret
aws ecr get-login-password --region us-east-1 | docker login \
  --username AWS \
  --password-stdin ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

kubectl delete secret ecr-secret -n production
kubectl create secret docker-registry ecr-secret \
  --docker-server=ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com \
  --docker-username=AWS \
  --docker-password="$(aws ecr get-login-password --region us-east-1)" \
  -n production

# 5. Check resource availability
kubectl describe nodes

# 6. Check logs
kubectl logs [POD_NAME] -n production -c currency-conversion
```

### LoadBalancer Pending

**Problem**: `kubectl get svc` shows LoadBalancer with no EXTERNAL-IP

**Solutions**:
```bash
# 1. Wait longer (AWS ELB takes 2-5 minutes)
watch kubectl get svc -n production

# 2. Check AWS Load Balancer
aws elb describe-load-balancers --region us-east-1

# 3. Check security group for port 80
aws ec2 describe-security-groups --region us-east-1

# 4. Re-create service
kubectl delete svc currency-conversion-service -n production
kubectl apply -f k8s/service.yml

# 5. Verify service selector matches pod labels
kubectl get pods -n production -o wide
kubectl get svc -n production -o wide

# 6. Check node security group
# Must allow inbound on port 80 and 8080
```

### HPA Not Scaling

**Problem**: HPA shows 0 pods or doesn't scale

**Solutions**:
```bash
# 1. Check if metrics-server is running
kubectl get deployment metrics-server -n kube-system

# 2. Install metrics-server if missing
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# 3. Wait for metrics to appear (takes 1-2 minutes)
kubectl top pods -n production

# 4. Check HPA status
kubectl describe hpa currency-conversion-hpa -n production

# 5. Check if pods have resource requests defined
kubectl describe pod [POD_NAME] -n production | grep -A 2 "Requests"

# 6. Generate load to test HPA
kubectl run load-generator --image=busybox:1.28 \
  --restart=Never -- /bin/sh -c \
  "while true; do wget -q -O- http://currency-conversion-service.production.svc.cluster.local; done"

# 7. Watch HPA scaling
watch kubectl get hpa -n production
```

### Persistent Volume Issues

**Problem**: Pod stuck in `Pending` due to PVC

**Solutions**:
```bash
# 1. Check PVC status
kubectl get pvc -n production

# 2. Describe PVC for errors
kubectl describe pvc [PVC_NAME] -n production

# 3. Check if storage class exists
kubectl get storageclass

# 4. Use emptyDir instead (temporary storage)
volumes:
- name: temp
  emptyDir: {}

# 5. Delete and re-create PVC
kubectl delete pvc [PVC_NAME] -n production
kubectl apply -f k8s/storage.yml
```

### Node Not Ready

**Problem**: `kubectl get nodes` shows node `NotReady`

**Solutions**:
```bash
# 1. Describe node
kubectl describe node [NODE_NAME]

# 2. Check node logs
# AWS EC2 → Instances → Select node → Monitor tab
# Or use: aws ec2 get-console-output --instance-id i-xxxxx

# 3. Restart node
aws ec2 reboot-instances --instance-ids i-xxxxx --region us-east-1

# 4. Replace node
terraform taint aws_eks_node_group.main
terraform apply -auto-approve

# 5. Check cluster autoscaler
kubectl get deployment -n kube-system | grep autoscaler
```

---

## Gemini AI Issues

### API Key Not Working

**Problem**: "Invalid API key" error

**Solutions**:
```bash
# 1. Verify API key format
echo $GEMINI_API_KEY
# Should be ~40 character alphanumeric string

# 2. Test API directly
curl -X POST \
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=$GEMINI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"contents":[{"parts":[{"text":"Test"}]}]}'

# 3. Check if API is enabled in Google Cloud
# Go to: Google Cloud Console → APIs & Services → Enabled APIs
# Search for: "Generative Language API"

# 4. Regenerate key in Google AI Studio
# Go to: https://aistudio.google.com/app/apikey
# Create new key, update GitHub Secrets

# 5. Check for spaces or hidden characters
GEMINI_API_KEY="$(echo -n $GEMINI_API_KEY)"
```

### Rate Limiting

**Problem**: "429 Too Many Requests"

**Solutions**:
```bash
# 1. Free tier limit: 60 RPM
# Wait 1 minute before retrying

# 2. Upgrade to paid tier
# Go to: https://ai.google.dev/pricing

# 3. Add retry logic with exponential backoff
# Implemented in: scripts/gemini_code_review.py

# 4. Reduce simultaneous requests
# Run reviews sequentially, not in parallel
```

### Timeout

**Problem**: Gemini AI request times out after 30 seconds

**Solutions**:
```bash
# 1. Reduce file size being analyzed
# Limit to first 2000 characters per file

# 2. Skip non-critical reviews
--include-security: false

# 3. Increase timeout in workflow
timeout-minutes: 15

# 4. Simplify prompt for faster analysis
# Edit prompts in scripts/gemini_code_review.py

# 5. Check network connectivity
ping generativelanguage.googleapis.com
```

### No Results in Review

**Problem**: Review completes but no output in report

**Solutions**:
```bash
# 1. Check if file reading failed
# Look for warnings in GitHub Actions logs
# "Could not read [filename]"

# 2. Ensure files have content
git log --oneline -n 5 -- src/main/java/Example.java

# 3. Check file encoding
file src/main/java/Example.java

# 4. Run manually for debugging
python scripts/gemini_code_review.py \
  --api-key "key" \
  --changed-files "src/main/java/" \
  --include-security \
  --include-kubernetes

# 5. Check GitHub Actions logs for errors
# Repository → Actions → Failed workflow → Logs
```

---

## Docker Issues

### Image Build Fails

**Problem**: `docker build` command fails

**Solutions**:
```bash
# 1. Check Docker is running
docker ps

# 2. Check Dockerfile syntax
docker build --no-cache -t test:latest .

# 3. Check build context
ls -la Dockerfile
ls -la target/*.jar  # JAR file must exist

# 4. Build with detailed output
docker build --progress=plain -t test:latest .

# 5. Check base image
docker pull openjdk:11-jre-slim

# 6. Build locally first
mvn clean package
docker build -t currency-conversion-service:local .
```

### Image Push to ECR Fails

**Problem**: `docker push` fails to ECR

**Solutions**:
```bash
# 1. Login to ECR
aws ecr get-login-password --region us-east-1 | docker login \
  --username AWS \
  --password-stdin ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# 2. Check image tag format
docker images | grep currency
# Should show: ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/...

# 3. Verify ECR repository exists
aws ecr describe-repositories --region us-east-1

# 4. Create repo if missing
aws ecr create-repository \
  --repository-name currency-conversion-service \
  --region us-east-1

# 5. Check Docker daemon space
docker system df
docker system prune  # Clean up old images
```

### Container Image Too Large

**Problem**: Docker image builds to 500MB+, slow to push

**Solutions**:
```dockerfile
# 1. Use multi-stage build (in Dockerfile)
FROM maven:3.8-openjdk-11 as builder
WORKDIR /build
COPY . .
RUN mvn clean package -DskipTests

FROM openjdk:11-jre-slim
COPY --from=builder /build/target/*.jar app.jar
ENTRYPOINT ["java", "-jar", "/app/app.jar"]

# 2. Use smaller base image
FROM alpine:latest  # 5MB vs 150MB for full OS

# 3. Remove build cache
docker build --no-cache -t image:tag .

# 4. Clean up in Dockerfile
RUN apt-get clean && rm -rf /var/lib/apt/lists/*
```

---

## General Issues

### Permission Denied Errors

**Problem**: "Permission denied" when running scripts

**Solutions**:
```bash
# 1. Make scripts executable
chmod +x scripts/setup.sh
chmod +x scripts/deploy.sh
chmod +x scripts/gemini_code_review.py

# 2. Run with explicit python
python3 scripts/gemini_code_review.py [args]

# 3. Run with bash
bash scripts/deploy.sh
```

### Command Not Found

**Problem**: `terraform: command not found`

**Solutions**:
```bash
# 1. Install missing tool
brew install terraform  # macOS
choco install terraform  # Windows
apt-get install terraform  # Linux

# 2. Check PATH
echo $PATH

# 3. Add to PATH
export PATH=$PATH:/usr/local/bin

# 4. Verify installation
which terraform
terraform version
```

### File Not Found

**Problem**: "File [filename] not found"

**Solutions**:
```bash
# 1. Check current directory
pwd

# 2. List files
ls -la

# 3. Use absolute path
python /home/user/project/scripts/deploy.sh  # instead of ./scripts/deploy.sh

# 4. Check file exists
test -f filename && echo "Exists" || echo "Not found"

# 5. Check case sensitivity
# Linux: case-sensitive
# macOS/Windows: case-insensitive
```

### Port Already in Use

**Problem**: "Address already in use" when binding to port

**Solutions**:
```bash
# 1. Find process using port
lsof -i :8080  # macOS/Linux
netstat -ano | findstr :8080  # Windows

# 2. Kill process
kill -9 PID  # Linux/macOS
taskkill /PID [PID] /F  # Windows

# 3. Use different port
kubectl port-forward svc/service 9090:80

# 4. Wait for port to be released
sleep 30
```

---

## Getting Help

### Collecting Debug Information

```bash
# 1. Cluster info
kubectl cluster-info
kubectl version

# 2. Node info
kubectl get nodes -o wide
kubectl top nodes

# 3. Pod info
kubectl get pods -A -o wide

# 4. Recent events
kubectl get events -A --sort-by='.lastTimestamp'

# 5. Deployment info
kubectl describe deployment currency-conversion-service -n production

# 6. Save all diagnostics
kubectl cluster-info dump --output-directory=[dir]
```

### Useful Commands for Debugging

```bash
# Test connectivity
nc -zv host port

# Check DNS
nslookup service.namespace.svc.cluster.local

# Test curl
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -- sh

# Shell into pod
kubectl exec -it [POD_NAME] -n production -- /bin/sh

# Stream logs
kubectl logs -f [POD_NAME] -n production

# Watch changes
watch kubectl get pods -n production
```

### References

- [Kubernetes Troubleshooting Guide](https://kubernetes.io/docs/tasks/debug/debug-cluster/)
- [AWS EKS Troubleshooting](https://docs.aws.amazon.com/eks/latest/userguide/troubleshooting.html)
- [Terraform Debugging](https://www.terraform.io/docs/internals/debugging.html)
- [Docker Troubleshooting](https://docs.docker.com/config/containers/troubleshoot/)

---

**Last Updated**: 2024
**Maintained By**: Your Team
