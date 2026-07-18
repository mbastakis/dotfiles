mock_provider "aws" {}

variables {
  bucket_name = "example-hardened-bucket"
  purpose     = "module-test"
}

run "defaults_are_private_and_aes_encrypted" {
  command = plan

  assert {
    condition     = aws_s3_bucket.this.force_destroy == false
    error_message = "Buckets must not allow force deletion."
  }

  assert {
    condition = (
      aws_s3_bucket_public_access_block.this.block_public_acls &&
      aws_s3_bucket_public_access_block.this.block_public_policy &&
      aws_s3_bucket_public_access_block.this.ignore_public_acls &&
      aws_s3_bucket_public_access_block.this.restrict_public_buckets
    )
    error_message = "All public-access controls must be enabled."
  }

  assert {
    condition = one(
      aws_s3_bucket_ownership_controls.this.rule
    ).object_ownership == "BucketOwnerEnforced"
    error_message = "Bucket ownership must be enforced."
  }

  assert {
    condition = one(one(
      aws_s3_bucket_server_side_encryption_configuration.this.rule
    ).apply_server_side_encryption_by_default).sse_algorithm == "AES256"
    error_message = "AES256 must be the default encryption algorithm."
  }

  assert {
    condition     = length(aws_s3_bucket_versioning.this) == 0
    error_message = "Versioning must be opt-in."
  }

  assert {
    condition     = length(aws_s3_bucket_lifecycle_configuration.this) == 0
    error_message = "Lifecycle rules must be opt-in."
  }
}

run "versioning_can_be_enabled" {
  command = plan

  variables {
    versioning_enabled = true
  }

  assert {
    condition = one(one(
      aws_s3_bucket_versioning.this
    ).versioning_configuration).status == "Enabled"
    error_message = "Versioning must be enabled when requested."
  }
}

run "lifecycle_rules_are_rendered" {
  command = plan

  variables {
    lifecycle_rules = [{
      id     = "archive"
      prefix = ""
      status = "Enabled"
      transitions = [{
        days          = 0
        storage_class = "GLACIER_IR"
      }]
      abort_incomplete_multipart_upload_days = 7
    }]
  }

  assert {
    condition     = length(aws_s3_bucket_lifecycle_configuration.this) == 1
    error_message = "Lifecycle configuration must be created when rules are supplied."
  }
}

run "kms_encryption_can_be_selected" {
  command = plan

  variables {
    encryption = {
      algorithm          = "aws:kms"
      kms_key_arn        = "arn:aws:kms:eu-central-1:123456789012:key/example"
      bucket_key_enabled = true
    }
  }

  assert {
    condition = one(one(
      aws_s3_bucket_server_side_encryption_configuration.this.rule
    ).apply_server_side_encryption_by_default).sse_algorithm == "aws:kms"
    error_message = "KMS encryption must be selected when requested."
  }

  assert {
    condition = one(
      aws_s3_bucket_server_side_encryption_configuration.this.rule
    ).bucket_key_enabled
    error_message = "KMS bucket keys must be configurable."
  }
}
