# Spring Boot Microservice CI/CD

This project demonstrates a Continuous Integration and Continuous Deployment (CI/CD) pipeline for a Spring Boot microservice using GitHub Actions, Terraform, Docker, and Kubernetes on AWS.

## Project Structure

```
spring-boot-microservice-cicd
├── .github
│   └── workflows
│       └── deploy.yml          # GitHub Actions workflow for CI/CD
├── terraform
│   ├── main.tf                 # Terraform configuration for AWS infrastructure
│   ├── variables.tf            # Input variables for Terraform
│   └── outputs.tf              # Outputs from Terraform
├── k8s
│   ├── deployment.yml           # Kubernetes deployment configuration
│   ├── service.yml              # Kubernetes service configuration
│   └── hpa.yml                  # Horizontal Pod Autoscaler configuration
├── Dockerfile                   # Dockerfile for building the microservice image
├── docker-compose.yml           # Docker Compose configuration for local development
├── scripts
│   └── validate.sh              # Script for validating the deployment
└── README.md                    # Project documentation
```

## Getting Started

### Prerequisites

- AWS account
- Terraform installed
- Docker installed
- Kubernetes cluster (EKS or similar)
- GitHub account

### Setup Instructions

1. **Clone the repository:**
   ```
   git clone https://github.com/in28minutes/spring-boot-examples.git
   cd spring-boot-microservice-cicd
   ```

2. **Configure Terraform:**
   - Update `terraform/variables.tf` with your desired AWS region, instance types, and cluster size.
   - Initialize Terraform:
     ```
     cd terraform
     terraform init
     ```

3. **Provision Infrastructure:**
   ```
   terraform apply
   ```

4. **Build and Push Docker Image:**
   - Build the Docker image:
     ```
     docker build -t currency-conversion-service .
     ```
   - Push the image to your cloud registry (e.g., Docker Hub, AWS ECR).

5. **Deploy to Kubernetes:**
   - Apply the Kubernetes configurations:
     ```
     kubectl apply -f k8s/
     ```

6. **Validate Deployment:**
   - Run the validation script:
     ```
     ./scripts/validate.sh
     ```

### Accessing the Application

Once the deployment is complete, you can access the application via the external IP provided by the LoadBalancer service defined in `k8s/service.yml`.

### CI/CD Workflow

The CI/CD pipeline is defined in `.github/workflows/deploy.yml`. It triggers on code pushes, runs tests, builds the Docker image, and deploys the application to the Kubernetes cluster.

### Contributing

Feel free to submit issues or pull requests for improvements or bug fixes.

### License

This project is licensed under the MIT License. See the LICENSE file for details.