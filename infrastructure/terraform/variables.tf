# =============================================================================
# FoodShare — Terraform: Variables
# =============================================================================

variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "ap-south-1" # Mumbai — lowest latency for India
}

variable "project_name" {
  description = "Project name used for resource naming and tagging"
  type        = string
  default     = "foodshare"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "production"
  validation {
    condition     = contains(["staging", "production"], var.environment)
    error_message = "environment must be 'staging' or 'production'."
  }
}

# --- VPC & Subnets (Multi-AZ in ap-south-1) ---
variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_a_cidr" {
  description = "CIDR for public subnet A in ap-south-1a"
  type        = string
  default     = "10.0.1.0/24"
}

variable "public_subnet_b_cidr" {
  description = "CIDR for public subnet B in ap-south-1b"
  type        = string
  default     = "10.0.2.0/24"
}

variable "availability_zone_a" {
  description = "First availability zone in ap-south-1"
  type        = string
  default     = "ap-south-1a"
}

variable "availability_zone_b" {
  description = "Second availability zone in ap-south-1 (required for RDS multi-AZ subnet group)"
  type        = string
  default     = "ap-south-1b"
}

# --- EC2 ---
variable "ec2_instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.small"
}

variable "ec2_ami_id" {
  description = "AMI ID for the EC2 instance (Ubuntu 22.04 LTS in ap-south-1)"
  type        = string
  default     = "ami-0f5ee92e2d63afc18"
}

variable "key_pair_name" {
  description = "Name of the EC2 key pair for SSH access"
  type        = string
  default     = "foodshare-key"
}

variable "allowed_ssh_cidr" {
  description = "CIDR block allowed to SSH into the EC2 instance"
  type        = string
  default     = "117.99.94.41/32"
}

# --- RDS PostgreSQL ---
variable "db_name" {
  description = "Initial database name for FoodShare PostgreSQL"
  type        = string
  default     = "foodshare_db"
}

variable "db_username" {
  description = "Master username for RDS PostgreSQL"
  type        = string
  default     = "foodshare_user"
}

variable "db_password" {
  description = "Master password for RDS PostgreSQL (never commit plaintext passwords)"
  type        = string
  sensitive   = true
}

variable "db_instance_class" {
  description = "RDS instance class (development / student-project sized)"
  type        = string
  default     = "db.t3.micro"
}

variable "db_allocated_storage" {
  description = "Initial allocated storage in gigabytes (GB)"
  type        = number
  default     = 20
}

variable "db_max_allocated_storage" {
  description = "Maximum storage auto-scaling threshold in gigabytes (GB)"
  type        = number
  default     = 50
}

variable "db_engine_version" {
  description = "PostgreSQL engine version"
  type        = string
  default     = "15"
}
