#!/bin/bash

# Setup Script for CI/CD Pipeline with Gemini AI, GitHub Actions, Terraform, Docker, and Kubernetes
# This script automates the initial setup of the development environment

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
print_error() {
    echo -e "${RED}❌ ERROR: $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

check_command() {
    if ! command -v "$1" &> /dev/null; then
        print_error "$1 is not installed"
        return 1
    fi
    print_success "$1 is installed"
    return 0
}

# Main setup
echo "==============================================="
echo "CI/CD Pipeline Setup with Gemini AI"
echo "==============================================="
echo ""

# Check prerequisites
print_info "Checking prerequisites..."
echo ""

prerequisites_ok=true
check_command "git" || prerequisites_ok=false
check_command "aws" || prerequisites_ok=false
check_command "terraform" || prerequisites_ok=false
check_command "docker" || prerequisites_ok=false
check_command "kubectl" || prerequisites_ok=false
check_command "python3" || prerequisites_ok=false

echo ""

if [ "$prerequisites_ok" = false ]; then
    print_error "Some prerequisites are missing. Please install them and try again."
    echo ""
    echo "Installation guides:"
    echo "- AWS CLI: https://aws.amazon.com/cli/"
    echo "- Terraform: https://www.terraform.io/downloads"
    echo "- Docker: https://www.docker.com/products/docker-desktop"
    echo "- kubectl: https://kubernetes.io/docs/tasks/tools/"
    echo "- Python: https://www.python.org/downloads/"
    exit 1
fi

print_success "All prerequisites are installed"
echo ""

# Configure AWS
print_info "Step 1: Configuring AWS credentials..."
read -p "Do you want to configure AWS credentials now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    aws configure
    print_success "AWS credentials configured"
else
    print_warning "Skipped AWS credentials configuration"
fi

echo ""

# Create S3 bucket for Terraform state
print_info "Step 2: Setting up Terraform state backend..."
read -p "Do you want to create S3 bucket for Terraform state? (y/n) " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    TIMESTAMP=$(date +%s)
    BUCKET_NAME="currency-microservice-tf-state-${TIMESTAMP}"
    AWS_REGION="us-east-1"
    
    echo "Creating S3 bucket: $BUCKET_NAME"
    aws s3api create-bucket \
        --bucket "$BUCKET_NAME" \
        --region "$AWS_REGION" \
        --create-bucket-configuration LocationConstraint="$AWS_REGION" 2>/dev/null || true
    
    print_success "S3 bucket created: $BUCKET_NAME"
    
    # Enable versioning
    aws s3api put-bucket-versioning \
        --bucket "$BUCKET_NAME" \
        --versioning-configuration Status=Enabled
    
    # Enable encryption
    aws s3api put-bucket-encryption \
        --bucket "$BUCKET_NAME" \
        --server-side-encryption-configuration '{
            "Rules": [{
                "ApplyServerSideEncryptionByDefault": {
                    "SSEAlgorithm": "AES256"
                }
            }]
        }'
    
    print_success "S3 bucket configured with versioning and encryption"
    
    # Create DynamoDB table for state locking
    print_info "Creating DynamoDB table for Terraform state locking..."
    aws dynamodb create-table \
        --table-name terraform-locks-currency-service \
        --attribute-definitions AttributeName=LockID,AttributeType=S \
        --key-schema AttributeName=LockID,KeyType=HASH \
        --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
        --region "$AWS_REGION" 2>/dev/null || print_warning "DynamoDB table may already exist"
    
    print_success "DynamoDB table for state locking created"
    
    # Create backend.tf
    cat > terraform/backend.tf <<EOF
terraform {
  backend "s3" {
    bucket         = "$BUCKET_NAME"
    key            = "prod/terraform.tfstate"
    region         = "$AWS_REGION"
    encrypt        = true
    dynamodb_table = "terraform-locks-currency-service"
  }
}
EOF
    
    print_success "backend.tf created for S3 state storage"
fi

echo ""

# Get Gemini API Key
print_info "Step 3: Setting up Gemini API key..."
read -p "Enter your Gemini API key (from https://aistudio.google.com/app/apikey): " GEMINI_API_KEY

if [ -z "$GEMINI_API_KEY" ]; then
    print_error "Gemini API key is required"
    exit 1
fi

# Store in .env file (not committed to git)
cat > .env.local <<EOF
GEMINI_API_KEY=$GEMINI_API_KEY
EOF

print_success "Gemini API key stored in .env.local (add to .gitignore)"

echo ""

# Install Python dependencies
print_info "Step 4: Installing Python dependencies..."
pip install -r requirements.txt || pip3 install -r requirements.txt

print_success "Python dependencies installed"

echo ""

# Initialize Terraform
print_info "Step 5: Initializing Terraform..."
cd terraform || exit 1
terraform init
print_success "Terraform initialized"
cd - > /dev/null || exit 1

echo ""

# Plan Terraform
print_info "Step 6: Planning Terraform deployment..."
cd terraform || exit 1
terraform plan -out=tfplan
print_success "Terraform plan created: tfplan"
cd - > /dev/null || exit 1

echo ""

# Summary
echo "==============================================="
print_success "Setup completed!"
echo "==============================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Review Terraform plan:"
echo "   cd terraform && terraform plan"
echo ""
echo "2. Apply Terraform configuration:"
echo "   cd terraform && terraform apply tfplan"
echo ""
echo "3. Configure kubectl:"
echo "   $(cd terraform && terraform output -raw configure_kubectl)"
echo ""
echo "4. Set up GitHub Secrets:"
echo "   Repository → Settings → Secrets and variables → Actions"
echo ""
echo "   Secrets to add:"
echo "   - AWS_ACCESS_KEY_ID"
echo "   - AWS_SECRET_ACCESS_KEY"
echo "   - GEMINI_API_KEY"
echo ""
echo "5. Trigger GitHub Actions workflow by pushing to main branch"
echo ""
echo "For detailed guide, see: COMPREHENSIVE_GUIDE.md"
echo ""
