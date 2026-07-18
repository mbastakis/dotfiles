mock_provider "aws" {}

variables {
  user_name   = "example-user"
  purpose     = "module-test"
  policy_name = "example-policy"
  policy_json = jsonencode({ Version = "2012-10-17", Statement = [] })
  tags        = { ManagedBy = "opentofu" }
}

run "creates_a_protected_least_privilege_identity" {
  command = plan

  assert {
    condition     = aws_iam_user.this.name == "example-user"
    error_message = "The requested IAM user name must be preserved."
  }

  assert {
    condition = (
      length(aws_iam_user.this.tags) == 3 &&
      aws_iam_user.this.tags["ManagedBy"] == "opentofu" &&
      aws_iam_user.this.tags["Name"] == "example-user" &&
      aws_iam_user.this.tags["Purpose"] == "module-test"
    )
    error_message = "The module must add stable identity tags."
  }

  assert {
    condition     = aws_iam_user_policy.this.name == "example-policy"
    error_message = "The stack-owned policy name must be preserved."
  }

  assert {
    condition     = aws_iam_user_policy.this.policy == var.policy_json
    error_message = "The stack-owned policy JSON must pass through unchanged."
  }

  assert {
    condition     = aws_iam_access_key.this.user == aws_iam_user.this.name
    error_message = "The access key must belong to the managed IAM user."
  }
}
