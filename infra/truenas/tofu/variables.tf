variable "truenas_host" {
  description = "Stable TrueNAS LAN identity used by managed resource metadata."
  type        = string
  default     = "192.168.1.74"
}

variable "truenas_connection_host" {
  description = "Runtime TrueNAS SSH endpoint. Task plan/apply selects LAN first and Tailscale otherwise."
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

variable "homeserver_bws_project_id" {
  description = "Bitwarden Secrets Manager project ID used for homeserver automation secrets."
  type        = string
  default     = "b6b2ed62-40f0-446b-b39f-b475001583b9"
}

variable "homepage_truenas_api_key_name" {
  description = "Name assigned to the TrueNAS API key used by the Homepage dashboard widget."
  type        = string
  default     = "homepage-dashboard"
}

variable "homepage_truenas_api_key_username" {
  description = "TrueNAS username that owns the API key used by the Homepage dashboard widget."
  type        = string
  default     = "mbastakis"
}

variable "homepage_truenas_api_key_secret_key" {
  description = "BWS key where the Homepage TrueNAS API key value is stored."
  type        = string
  default     = "homeserver/truenas/api-keys/homepage"
}
