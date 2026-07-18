locals {
  backup_bucket_lifecycle_rules = [{
    id     = "restic-active-repo-glacier-instant-retrieval"
    status = "Enabled"
    prefix = ""
    transitions = [{
      days          = 0
      storage_class = "GLACIER_IR"
    }]
    abort_incomplete_multipart_upload_days = 7
  }]
}

module "backup_bucket" {
  source = "../../modules/hardened-s3-bucket"

  bucket_name        = var.backup_bucket_name
  purpose            = "restic-backups"
  versioning_enabled = false
  encryption = {
    algorithm = "AES256"
  }
  lifecycle_rules = local.backup_bucket_lifecycle_rules
  tags            = var.tags
}
