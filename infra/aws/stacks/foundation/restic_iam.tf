data "aws_iam_policy_document" "restic_backup" {
  statement {
    sid = "ListBackupBucket"
    actions = [
      "s3:GetBucketLocation",
      "s3:ListBucket",
      "s3:ListBucketMultipartUploads",
    ]
    resources = [module.backup_bucket.arn]
  }

  statement {
    sid = "ReadWriteResticObjects"
    actions = [
      "s3:AbortMultipartUpload",
      "s3:DeleteObject",
      "s3:GetObject",
      "s3:ListMultipartUploadParts",
      "s3:PutObject",
      "s3:RestoreObject",
    ]
    resources = ["${module.backup_bucket.arn}/*"]
  }
}

module "restic_backup_user" {
  source = "../../modules/iam-user"

  user_name   = var.restic_iam_user_name
  purpose     = "restic-backup-writer"
  policy_name = "homeserver-restic-s3-access"
  policy_json = data.aws_iam_policy_document.restic_backup.json
  tags        = var.tags
}
