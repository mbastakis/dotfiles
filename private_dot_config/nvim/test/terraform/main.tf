# Terraform test file with intentional format/lint issues

# Inconsistent formatting
resource "aws_instance" "web" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t2.micro"

  tags = {
    Name        = "WebServer"
    Environment = "production"
  }
}

# Very long line
resource "aws_security_group" "web_sg" {
  ingress {
    from_port   = 80
    to_port     = 80
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

# Missing required fields
resource "aws_s3_bucket" "data" {
  bucket = "my-bucket"
}

# Hardcoded values (should use variables)
resource "aws_db_instance" "database" {
  allocated_storage = 20
  engine            = "postgres"
  engine_version    = "13.7"
  instance_class    = "db.t2.micro"
  username          = "admin"
  password          = "hardcoded_password123"
}

# Inconsistent spacing
variable "region" {
  type    = string
  default = "us-east-1"
}

variable "instance_count" {
  type    = number
  default = 3
}

# Missing description
variable "vpc_cidr" {
  type    = string
  default = "10.0.0.0/16"
}

# Output without description
output "instance_id" {
  value = aws_instance.web.id
}

# Missing provider version
provider "aws" {
  region = var.region
}

# Resource without lifecycle rules
resource "aws_ebs_volume" "data" {
  availability_zone = "us-east-1a"
  size              = 100

  tags = {
    Name = "DataVolume"
  }
}
