# =============================================================================
# FoodShare — Terraform: Outputs
# =============================================================================

# --- EC2 & Networking ---
output "vpc_id" {
  description = "VPC ID of the FoodShare network"
  value       = aws_vpc.main.id
}

output "ec2_public_ip" {
  description = "Static public IP address of the EC2 instance (Elastic IP)"
  value       = aws_eip.app.public_ip
}

output "ec2_public_dns" {
  description = "Public DNS name of the EC2 instance"
  value       = aws_instance.app.public_dns
}

output "ec2_security_group_id" {
  description = "Security group ID for the EC2 instance"
  value       = aws_security_group.ec2.id
}

# --- RDS PostgreSQL ---
output "rds_endpoint" {
  description = "Connection endpoint for RDS PostgreSQL (<host>:<port>)"
  value       = aws_db_instance.postgres.endpoint
}

output "rds_address" {
  description = "Hostname/address of the RDS PostgreSQL database"
  value       = aws_db_instance.postgres.address
}

output "rds_port" {
  description = "Port number on which RDS PostgreSQL is listening"
  value       = aws_db_instance.postgres.port
}

output "rds_db_name" {
  description = "Initial database name created in RDS"
  value       = aws_db_instance.postgres.db_name
}

output "rds_security_group_id" {
  description = "Security group ID for RDS PostgreSQL"
  value       = aws_security_group.rds.id
}
