## Terraform — MoreAI Infrastructure

### Setup
```bash
# install terraform
choco install terraform   # Windows
brew install terraform    # Mac

# init
cd terraform
terraform init

# plan — see what will be created
terraform plan

# apply — create infrastructure
terraform apply

# destroy — tear everything down
terraform destroy
```

### What gets created
- VPC with public + private subnets across 2 AZs
- EC2 t3.medium with Docker pre-installed
- Elastic IP for stable addressing
- S3 bucket for artifacts (encrypted, versioned, private)
- S3 bucket for Terraform state
- IAM role with least-privilege S3 access
- Security group (80, 443, 8000)