terraform {
  required_version = ">= 1.8.0"

  required_providers {
    truenas = {
      source  = "deevus/truenas"
      version = "~> 0.16.0"
    }
  }

  backend "s3" {}
}
