resource "aws_iam_user" "this" {
  name = var.user_name
  tags = merge(var.tags, {
    Name    = var.user_name
    Purpose = var.purpose
  })

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_iam_user_policy" "this" {
  name   = var.policy_name
  user   = aws_iam_user.this.name
  policy = var.policy_json

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_iam_access_key" "this" {
  user = aws_iam_user.this.name

  lifecycle {
    prevent_destroy = true
  }
}
