output "route53_zone_id" {
  description = "Route53 hosted zone ID for the public domain."
  value       = aws_route53_zone.public.zone_id
}

output "route53_name_servers" {
  description = "Authoritative Route53 nameservers to configure at the registrar."
  value       = aws_route53_zone.public.name_servers
}

output "private_service_fqdns" {
  description = "Private homeserver service names managed in Route53."
  value       = { for name, record in aws_route53_record.private_service_a : name => record.fqdn }
}
