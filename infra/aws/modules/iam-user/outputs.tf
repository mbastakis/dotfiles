output "name" {
  description = "IAM user name."
  value       = aws_iam_user.this.name
}

output "access_key_id" {
  description = "IAM access key ID."
  value       = aws_iam_access_key.this.id
}

output "secret_access_key" {
  description = "IAM secret access key."
  value       = aws_iam_access_key.this.secret
  sensitive   = true
}
