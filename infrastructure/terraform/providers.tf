# =============================================================================
# FoodShare — Terraform: Providers
# =============================================================================

terraform {
  required_version = ">= 1.7.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Uncomment to use remote state (S3 backend) in production:
  # backend "s3" {
  #   bucket = "your-terraform-state-bucket"
  #   key    = "foodshare/terraform.tfstate"
  #   region = "ap-south-1"
  # }
}

provider "aws" {
  region = var.aws_region

  # Credentials configured via AWS_ACCESS_KEY_ID + AWS_SECRET_ACCESS_KEY env vars
}
