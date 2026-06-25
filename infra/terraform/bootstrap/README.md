# OpenTofu State Bootstrap

OpenTofu stack that owns the S3 backend bucket used by homeserver infrastructure state. The first run uses local state, creates or adopts the bucket, and then migrates this stack's own state into that same bucket.

## Owns

- S3 bucket for OpenTofu state
- S3 versioning
- S3 server-side encryption with SSE-S3
- S3 public access block
- S3 object ownership controls
- TLS-only bucket policy
- S3 native state lockfile support

## Does Not Own

- Restic backup buckets or IAM
- TrueNAS datasets or jobs
- Application infrastructure outside OpenTofu state storage

## Backend

After bootstrap, this stack stores its own state at:

```text
s3://mbastakis-homeserver-opentofu-state/homeserver/bootstrap/terraform.tfstate
```

Other homeserver stacks use separate state keys in the same bucket.

## One-Time Bootstrap or Adoption

Run from the repository root:

```bash
task tf:bootstrap-state
```

The helper script is orchestration only: AWS resources are declared in HCL. It runs through the fixed `aws-login exec mbastakis --` profile and supports both first creation and adoption of the legacy script-created bucket before migrating local state to S3.

Pass OpenTofu apply flags through the task when needed:

```bash
task tf:bootstrap-state -- -auto-approve
```

## Steady-State Commands

After the one-time migration, manage backend bucket changes through normal remote-state tasks:

```bash
task tf:bootstrap:init
task tf:bootstrap:plan
task tf:bootstrap:apply
```

Do not run `task tf:bootstrap-state` again after `homeserver/bootstrap/terraform.tfstate` exists.

<!-- BEGIN_TF_DOCS -->
## Requirements

| Name | Version |
| ---- | ------- |
| terraform | >= 1.8.0 |
| aws | ~> 5.0 |

## Providers

| Name | Version |
| ---- | ------- |
| aws | 5.100.0 |

## Resources

| Name | Type |
| ---- | ---- |
| [aws_s3_bucket.opentofu_state](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket) | resource |
| [aws_s3_bucket_ownership_controls.opentofu_state](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_ownership_controls) | resource |
| [aws_s3_bucket_policy.opentofu_state](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_policy) | resource |
| [aws_s3_bucket_public_access_block.opentofu_state](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_public_access_block) | resource |
| [aws_s3_bucket_server_side_encryption_configuration.opentofu_state](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_server_side_encryption_configuration) | resource |
| [aws_s3_bucket_versioning.opentofu_state](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_versioning) | resource |
| [aws_iam_policy_document.state_bucket](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/iam_policy_document) | data source |

## Inputs

| Name | Description | Type | Default | Required |
| ---- | ----------- | ---- | ------- | :------: |
| aws\_region | AWS region for the OpenTofu state bucket. | `string` | `"eu-central-1"` | no |
| state\_bucket\_name | S3 bucket name for homeserver OpenTofu state. | `string` | `"mbastakis-homeserver-opentofu-state"` | no |
| tags | Tags applied to bootstrap-managed AWS resources. | `map(string)` | <pre>{<br/>  "ManagedBy": "opentofu",<br/>  "Project": "homeserver",<br/>  "Stack": "bootstrap"<br/>}</pre> | no |

## Outputs

| Name | Description |
| ---- | ----------- |
| bootstrap\_state\_key | S3 backend key used by the bootstrap stack after migration. |
| s3\_native\_locking | Whether stacks use S3 native lockfiles instead of DynamoDB locking. |
| state\_bucket\_arn | ARN of the S3 bucket used for homeserver OpenTofu state. |
| state\_bucket\_name | Name of the S3 bucket used for homeserver OpenTofu state. |
| state\_bucket\_region | AWS region for the homeserver OpenTofu state bucket. |
<!-- END_TF_DOCS -->
