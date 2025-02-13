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
  ami                         = "ami-0ddf631ad198e005e"
  instance_type               = "t2.micro"
  key_name                    = "QuantumMoney-KEY"
  subnet_id                   = aws_default_subnet.first.id
  vpc_security_group_ids      = [aws_security_group.backend.id]
  associate_public_ip_address = true

  user_data = <<-EOF
    #!/bin/bash
    apt-get update -y
    apt-get upgrade -y
    apt-get install -y python3.10 python3.10-venv python3.10-pip git tmux curl

    cd /home/admin
    git clone https://github.com/lianstemp/GCC2025-Quantum-Money.git
    cd GCC2025-Quantum-Money/backend

    python3.10 -m pip install -r requirements.txt

    tmux new-session -d -s fastapi_session 'uvicorn main:app --host 0.0.0.0 --port 8000'
  EOF
}

# resource "random_id" "bucket_id" {
#   byte_length = 4
# }

resource "aws_s3_bucket" "frontend" {
  bucket = "quantumoney.datzen.cloud"
}

resource "aws_s3_bucket_ownership_controls" "frontend" {
  bucket = aws_s3_bucket.frontend.id
  rule {
    object_ownership = "BucketOwnerPreferred"
  }
}

resource "aws_s3_bucket_acl" "frontend" {
  depends_on = [aws_s3_bucket_ownership_controls.frontend]
  bucket = aws_s3_bucket.frontend.id
  acl    = "public-read"
}

resource "aws_s3_bucket_website_configuration" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  index_document {
    suffix = "index.html"
  }

  error_document {
    key = "index.html"
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
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "PublicReadGetObject"
        Effect    = "Allow"
        Principal = "*"
        Action    = [
          "s3:GetObject"
        ]
        Resource = [
          "${aws_s3_bucket.frontend.arn}/*"
        ]
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
