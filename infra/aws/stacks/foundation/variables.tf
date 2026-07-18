variable "aws_region" {
  description = "AWS region for homeserver foundation resources."
  type        = string
  default     = "eu-central-1"
}

variable "domain_name" {
  description = "Public Route53 zone used to scope Traefik ACME DNS-01 IAM permissions. DNS records are owned by the dns stack."
  type        = string
  default     = "mbastakis.com"
}

variable "backup_bucket_name" {
  description = "S3 bucket name for encrypted restic backups from TrueNAS/Backrest."
  type        = string
  default     = "mbastakis-homeserver-restic-backups"
}

variable "restic_iam_user_name" {
  description = "IAM user name used by TrueNAS/Backrest for restic S3 access."
  type        = string
  default     = "homeserver-truenas-restic"
}

variable "traefik_acme_iam_user_name" {
  description = "IAM user name used by atlas Traefik for Route53 ACME DNS-01 challenges."
  type        = string
  default     = "homeserver-atlas-traefik-acme"
}

variable "tags" {
  description = "Tags applied to AWS foundation resources."
  type        = map(string)
  default = {
    ManagedBy = "opentofu"
    Project   = "homeserver"
    Stack     = "aws-foundation"
  }
}
