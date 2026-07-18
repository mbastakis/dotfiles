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
| [aws_route53_record.private_service_a](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/route53_record) | resource |
| [aws_route53_zone.public](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/route53_zone) | resource |

## Inputs

| Name | Description | Type | Default | Required |
| ---- | ----------- | ---- | ------- | :------: |
| atlas\_tailscale\_ipv4 | Tailscale IPv4 address of atlas. Used for private homeserver service A records. | `string` | `"100.101.208.110"` | no |
| aws\_region | AWS region used by the provider. Route53 is global, but the provider still requires a region. | `string` | `"eu-central-1"` | no |
| domain\_name | Public DNS zone managed in Route53. | `string` | `"mbastakis.com"` | no |
| private\_service\_subdomains | Homeserver service subdomains pointed at atlas over Tailscale. | `set(string)` | <pre>[<br/>  "auth",<br/>  "code",<br/>  "files",<br/>  "tasks",<br/>  "taskboard",<br/>  "home",<br/>  "traefik",<br/>  "backrest",<br/>  "photos",<br/>  "audiobooks",<br/>  "push",<br/>  "pihole"<br/>]</pre> | no |
| tags | Tags applied to DNS resources. | `map(string)` | <pre>{<br/>  "ManagedBy": "opentofu",<br/>  "Project": "homeserver",<br/>  "Stack": "dns"<br/>}</pre> | no |

## Outputs

| Name | Description |
| ---- | ----------- |
| private\_service\_fqdns | Private homeserver service names managed in Route53. |
| route53\_name\_servers | Authoritative Route53 nameservers to configure at the registrar. |
| route53\_zone\_id | Route53 hosted zone ID for the public domain. |
<!-- END_TF_DOCS -->
