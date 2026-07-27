# Security Group
resource "aws_security_group" "moreai" {
  name        = "${var.app_name}-sg"
  description = "MoreAI security group"
  vpc_id      = aws_vpc.moreai_vpc.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.app_name}-sg"
  }
}

# EC2 Instance
resource "aws_instance" "moreai" {
  ami                    = "ami-0f58b397bc5c1f2e8"  # Ubuntu 24.04 ap-south-1
  instance_type          = var.ec2_instance_type
  subnet_id              = aws_subnet.public[0].id
  vpc_security_group_ids = [aws_security_group.moreai.id]
  iam_instance_profile   = aws_iam_instance_profile.moreai.name

  root_block_device {
    volume_size = 30
    volume_type = "gp3"
    encrypted   = true
  }

  user_data = <<-EOF
    #!/bin/bash
    apt-get update -y
    apt-get install -y docker.io docker-compose-plugin
    systemctl start docker
    systemctl enable docker
    usermod -aG docker ubuntu
  EOF

  tags = {
    Name        = "${var.app_name}-server"
    Environment = var.environment
  }
}

# Elastic IP — stable IP that survives instance stops
resource "aws_eip" "moreai" {
  instance = aws_instance.moreai.id
  domain   = "vpc"

  tags = {
    Name = "${var.app_name}-eip"
  }
}