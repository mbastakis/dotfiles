module "state_bucket" {
  source = "../../modules/hardened-s3-bucket"

  bucket_name        = var.state_bucket_name
  purpose            = "opentofu-state"
  versioning_enabled = true
  encryption = {
    algorithm = "AES256"
  }
  lifecycle_rules = []
  tags            = var.tags
}
