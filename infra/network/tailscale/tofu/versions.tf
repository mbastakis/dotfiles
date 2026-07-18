terraform {
  required_version = ">= 1.8.0"

  required_providers {
    tailscale = {
      source  = "tailscale/tailscale"
      version = "= 0.29.2"
    }
  }

  backend "s3" {}
}
