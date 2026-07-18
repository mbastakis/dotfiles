output "backup_bucket_name" {
  description = "S3 bucket used for encrypted restic backups."
  value       = module.backup_bucket.name
}

output "backup_bucket_arn" {
  description = "ARN of the S3 bucket used for encrypted restic backups."
  value       = module.backup_bucket.arn
}

output "restic_iam_user_name" {
  description = "IAM user used by TrueNAS/Backrest for restic S3 access."
  value       = module.restic_backup_user.name
}

output "restic_aws_access_key_id" {
  description = "AWS access key ID for the restic IAM user. Store the paired secret access key in BWS after apply."
  value       = module.restic_backup_user.access_key_id
}

output "restic_aws_secret_access_key" {
  description = "Sensitive AWS secret access key for the restic IAM user. Store this in BWS after apply; do not print or commit it."
  value       = module.restic_backup_user.secret_access_key
  sensitive   = true
}

output "traefik_acme_iam_user_name" {
  description = "IAM user used by atlas Traefik for Route53 ACME DNS-01 challenges."
  value       = module.traefik_acme_user.name
}

output "traefik_acme_aws_access_key_id" {
  description = "AWS access key ID for the Traefik Route53 ACME IAM user."
  value       = module.traefik_acme_user.access_key_id
}

output "traefik_acme_aws_secret_access_key" {
  description = "Sensitive AWS secret access key for the Traefik Route53 ACME IAM user. Store this in BWS after apply; do not print or commit it."
  value       = module.traefik_acme_user.secret_access_key
  sensitive   = true
}
