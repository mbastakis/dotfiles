terraform {
  required_version = ">= 1.8.0"

  required_providers {
    null = {
      source  = "hashicorp/null"
      version = "~> 3.2"
    }

    truenas = {
      source  = "deevus/truenas"
      version = "~> 0.16.0"
    }
  }

  backend "s3" {}
}
