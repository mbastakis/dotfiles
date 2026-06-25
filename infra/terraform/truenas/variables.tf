variable "truenas_host" {
  description = "TrueNAS host or IP address."
  type        = string
  default     = "192.168.1.74"
}

variable "truenas_ssh_user" {
  description = "TrueNAS SSH user used by OpenTofu. Must authenticate with a private key."
  type        = string
  default     = "mbastakis"
}

variable "truenas_ssh_port" {
  description = "TrueNAS SSH port."
  type        = number
  default     = 22
}

variable "truenas_ssh_private_key" {
  description = "Private key content for the TrueNAS SSH user. Supply via environment/secret manager; never commit it."
  type        = string
  sensitive   = true
}

variable "truenas_ssh_host_key_fingerprint" {
  description = "TrueNAS SSH host key fingerprint. The provider currently negotiates the ECDSA host key."
  type        = string
  default     = "SHA256:PaERL229czZ7ImwLw6mCaZzlIKKmwdTuqTopEyEVjEU"
}
