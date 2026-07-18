# AWS Foundation

OpenTofu stack for AWS resources that support homeserver TLS automation and backups. DNS records live in the dedicated `infra/aws/stacks/dns` stack. This stack uses the shared S3 backend owned by the bootstrap stack and has its own state key.

## Owns

- Restic backup S3 bucket
- Cost-optimized, immediately readable backup storage policy
- IAM identity/policy for restic backup writes from TrueNAS
- IAM identity/policy for Traefik Route53 ACME DNS-01 on atlas

## Does Not Own

- The OpenTofu state bucket
- Route53 DNS records for homeserver service names
- TrueNAS datasets or jobs
- Restic repository contents
- Tailscale node address assignment

## State Key

```text
homeserver/aws-foundation/terraform.tfstate
```

## Commands

```bash
task aws:foundation:init
task aws:foundation:plan
task aws:foundation:apply
```

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

## Modules

| Name | Source | Version |
| ---- | ------ | ------- |
| backup\_bucket | ../../modules/hardened-s3-bucket | n/a |
| restic\_backup\_user | ../../modules/iam-user | n/a |
| traefik\_acme\_user | ../../modules/iam-user | n/a |

## Resources

| Name | Type |
| ---- | ---- |
| [aws_iam_policy_document.restic_backup](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/iam_policy_document) | data source |
| [aws_iam_policy_document.traefik_acme](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/iam_policy_document) | data source |
| [aws_route53_zone.public](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/route53_zone) | data source |

## Inputs

| Name | Description | Type | Default | Required |
| ---- | ----------- | ---- | ------- | :------: |
| aws\_region | AWS region for homeserver foundation resources. | `string` | `"eu-central-1"` | no |
| backup\_bucket\_name | S3 bucket name for encrypted restic backups from TrueNAS/Backrest. | `string` | `"mbastakis-homeserver-restic-backups"` | no |
| domain\_name | Public Route53 zone used to scope Traefik ACME DNS-01 IAM permissions. DNS records are owned by the dns stack. | `string` | `"mbastakis.com"` | no |
| restic\_iam\_user\_name | IAM user name used by TrueNAS/Backrest for restic S3 access. | `string` | `"homeserver-truenas-restic"` | no |
| tags | Tags applied to AWS foundation resources. | `map(string)` | <pre>{<br/>  "ManagedBy": "opentofu",<br/>  "Project": "homeserver",<br/>  "Stack": "aws-foundation"<br/>}</pre> | no |
| traefik\_acme\_iam\_user\_name | IAM user name used by atlas Traefik for Route53 ACME DNS-01 challenges. | `string` | `"homeserver-atlas-traefik-acme"` | no |

## Outputs

| Name | Description |
| ---- | ----------- |
| backup\_bucket\_arn | ARN of the S3 bucket used for encrypted restic backups. |
| backup\_bucket\_name | S3 bucket used for encrypted restic backups. |
| restic\_aws\_access\_key\_id | AWS access key ID for the restic IAM user. Store the paired secret access key in BWS after apply. |
| restic\_aws\_secret\_access\_key | Sensitive AWS secret access key for the restic IAM user. Store this in BWS after apply; do not print or commit it. |
| restic\_iam\_user\_name | IAM user used by TrueNAS/Backrest for restic S3 access. |
| traefik\_acme\_aws\_access\_key\_id | AWS access key ID for the Traefik Route53 ACME IAM user. |
| traefik\_acme\_aws\_secret\_access\_key | Sensitive AWS secret access key for the Traefik Route53 ACME IAM user. Store this in BWS after apply; do not print or commit it. |
| traefik\_acme\_iam\_user\_name | IAM user used by atlas Traefik for Route53 ACME DNS-01 challenges. |
<!-- END_TF_DOCS -->
