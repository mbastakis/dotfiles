output "name" {
  description = "S3 bucket name."
  value       = aws_s3_bucket.this.id
}

output "arn" {
  description = "S3 bucket ARN."
  value       = aws_s3_bucket.this.arn
}

output "tls_only_policy_json" {
  description = "Rendered TLS-only bucket policy JSON."
  value       = data.aws_iam_policy_document.tls_only.json
}
