output "state_bucket_name" {
  description = "Name of the S3 bucket used for homeserver OpenTofu state."
  value       = module.state_bucket.name
}

output "state_bucket_arn" {
  description = "ARN of the S3 bucket used for homeserver OpenTofu state."
  value       = module.state_bucket.arn
}

output "state_bucket_region" {
  description = "AWS region for the homeserver OpenTofu state bucket."
  value       = var.aws_region
}

output "bootstrap_state_key" {
  description = "S3 backend key used by the bootstrap stack after migration."
  value       = "homeserver/bootstrap/terraform.tfstate"
}

output "s3_native_locking" {
  description = "Whether stacks use S3 native lockfiles instead of DynamoDB locking."
  value       = true
}
