variable "aws_region" {
  description = "AWS region used by the provider. Route53 is global, but the provider still requires a region."
  type        = string
  default     = "eu-central-1"
}

variable "domain_name" {
  description = "Public DNS zone managed in Route53."
  type        = string
  default     = "mbastakis.com"
}

variable "atlas_tailscale_ipv4" {
  description = "Tailscale IPv4 address of atlas. Used for private homeserver service A records."
  type        = string
  default     = "100.101.208.110"

  validation {
    condition     = can(regex("^100\\.[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}$", var.atlas_tailscale_ipv4))
    error_message = "atlas_tailscale_ipv4 must be the atlas Tailscale IPv4 address, usually in 100.64.0.0/10."
  }
}

variable "private_service_subdomains" {
  description = "Homeserver service subdomains pointed at atlas over Tailscale."
  type        = set(string)
  default     = ["auth", "code", "files", "tasks", "taskboard", "home", "traefik", "backrest", "photos", "audiobooks", "push", "pihole"]
}

variable "tags" {
  description = "Tags applied to DNS resources."
  type        = map(string)
  default = {
    ManagedBy = "opentofu"
    Project   = "homeserver"
    Stack     = "dns"
  }
}
