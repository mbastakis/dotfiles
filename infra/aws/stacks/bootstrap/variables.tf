variable "aws_region" {
  description = "AWS region for the OpenTofu state bucket."
  type        = string
  default     = "eu-central-1"
}

variable "state_bucket_name" {
  description = "S3 bucket name for homeserver OpenTofu state."
  type        = string
  default     = "mbastakis-homeserver-opentofu-state"
}

variable "tags" {
  description = "Tags applied to bootstrap-managed AWS resources."
  type        = map(string)
  default = {
    ManagedBy = "opentofu"
    Project   = "homeserver"
    Stack     = "bootstrap"
  }
}
