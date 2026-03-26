variable "aws_region" {
  description = "The AWS region to deploy the infrastructure"
  type        = string
  default     = "us-west-2"
}

variable "cluster_name" {
  description = "The name of the Kubernetes cluster"
  type        = string
  default     = "currency-conversion-cluster"
}

variable "instance_type" {
  description = "The EC2 instance type for the worker nodes"
  type        = string
  default     = "t3.medium"
}

variable "desired_capacity" {
  description = "The desired number of worker nodes in the cluster"
  type        = number
  default     = 2
}

variable "max_size" {
  description = "The maximum number of worker nodes in the cluster"
  type        = number
  default     = 5
}

variable "min_size" {
  description = "The minimum number of worker nodes in the cluster"
  type        = number
  default     = 1
}

variable "vpc_cidr" {
  description = "The CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "subnet_cidrs" {
  description = "The CIDR blocks for the subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}