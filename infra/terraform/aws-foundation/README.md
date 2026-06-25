# AWS Foundation

OpenTofu stack for AWS resources that support homeserver backups. This stack uses the shared S3 backend owned by the bootstrap stack and has its own state key.

## Owns

- Restic backup S3 bucket
- Cost-optimized, immediately readable backup storage policy
- IAM identity/policy for restic backup writes from TrueNAS

## Does Not Own

- The OpenTofu state bucket
- TrueNAS datasets or jobs
- Restic repository contents

## State Key

```text
homeserver/aws-foundation/terraform.tfstate
```

## Commands

```bash
task tf:aws-foundation:init
task tf:aws-foundation:plan
task tf:aws-foundation:apply
```

<!-- BEGIN_TF_DOCS -->
## Requirements

| Name | Version |
| ---- | ------- |
| terraform | >= 1.8.0 |
| aws | ~> 5.0 |
<!-- END_TF_DOCS -->
