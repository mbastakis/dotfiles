terraform {
  required_version = ">= 1.8.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # The S3 backend block for this self-hosting bootstrap stack is generated
  # as backend.generated.tf after the first local apply. That lets the stack
  # create the bucket with local state, then migrate its own state into S3.
}
