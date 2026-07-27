output "ec2_public_ip" {
  description = "MoreAI EC2 public IP"
  value       = aws_eip.moreai.public_ip
}

output "s3_bucket_name" {
  description = "Artifacts S3 bucket"
  value       = aws_s3_bucket.artifacts.bucket
}

output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.moreai_vpc.id
}