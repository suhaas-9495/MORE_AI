variable "aws_region" {
  description = "AWS region"
  default     = "ap-south-1"
}

variable "environment" {
  description = "Environment name"
  default     = "production"
}

variable "app_name" {
  description = "Application name"
  default     = "moreai"
}

variable "ec2_instance_type" {
  description = "EC2 instance type"
  default     = "t3.medium"
}

variable "db_instance_class" {
  description = "RDS instance class"
  default     = "db.t3.micro"
}