locals {
  private_service_records = {
    for subdomain in var.private_service_subdomains : subdomain => {
      fqdn = "${subdomain}.${var.domain_name}"
      ipv4 = var.atlas_tailscale_ipv4
    }
  }
}

resource "aws_route53_record" "private_service_a" {
  for_each = local.private_service_records

  zone_id         = aws_route53_zone.public.zone_id
  name            = each.value.fqdn
  type            = "A"
  ttl             = 300
  records         = [each.value.ipv4]
  allow_overwrite = true
}
