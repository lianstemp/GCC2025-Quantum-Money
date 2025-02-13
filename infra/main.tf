terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
  required_version = ">= 1.0"
}

provider "aws" {
  region     = "ap-northeast-1"
  access_key = var.aws_access_key
  secret_key = var.aws_secret_key
}

resource "aws_default_vpc" "default" {}

resource "aws_default_subnet" "first" {
  availability_zone = "ap-northeast-1a"
}

data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]
  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-ebs"]
  }
}

resource "aws_security_group" "backend" {
  name   = "backend-sg"
  vpc_id = aws_default_vpc.default.id
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  ingress {
    from_port   = 80
    to_port     = 80
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
}

resource "aws_instance" "backend" {
  ami                         = data.aws_ami.amazon_linux.id
  instance_type               = "t2.micro"
  subnet_id                   = aws_default_subnet.first.id
  vpc_security_group_ids      = [aws_security_group.backend.id]
  associate_public_ip_address = true

  user_data = <<-EOF
    #!/bin/bash
    # Update system and install dependencies (using Amazon Linux commands)
    yum update -y
    yum install -y python3 git

    cd /home/ec2-user
    git clone https://github.com/lianstemp/GCC2025-Quantum-Money.git
    cd GCC2025-Quantum-Money/backend

    # Install Python dependencies from requirements.txt
    python3 -m pip install -r requirements.txt

    # Start the FastAPI app (running in the background)
    nohup uvicorn main:app --host 0.0.0.0 --port 8000 &
  EOF

}

resource "random_id" "bucket_id" {
  byte_length = 4
}

resource "aws_s3_bucket" "frontend" {
  bucket = "quantum-slot-machine-frontend-${random_id.bucket_id.hex}"
}

resource "aws_s3_bucket_website_configuration" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  index_document {
    suffix = "index.html"
  }

  error_document {
    key = "error.html"
  }
}

# Add public access block resource to allow public bucket policy
resource "aws_s3_bucket_public_access_block" "frontend" {
  bucket                  = aws_s3_bucket.frontend.id
  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

resource "aws_s3_bucket_policy" "frontend_policy" {
  bucket = aws_s3_bucket.frontend.id
  policy = jsonencode({
    Version   = "2012-10-17",
    Statement = [
      {
        Effect    = "Allow",
        Principal = "*",
        Action    = "s3:GetObject",
        Resource  = "${aws_s3_bucket.frontend.arn}/*"
      }
    ]
  })
}

# Disable account-level block public access (if permitted)
resource "aws_s3_account_public_access_block" "account" {
  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

# Create CloudWatch Log Group for API Gateway monitoring
resource "aws_cloudwatch_log_group" "api_gw_logs" {
  name              = "/aws/apigateway/quantum_slot_api"
  retention_in_days = 14
}
