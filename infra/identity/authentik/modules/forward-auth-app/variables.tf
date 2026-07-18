variable "provider_name" {
  description = "Stable Authentik proxy provider name."
  type        = string
}

variable "application_name" {
  description = "User-facing Authentik application name."
  type        = string
}

variable "application_slug" {
  description = "Stable Authentik application slug."
  type        = string
}

variable "application_group" {
  description = "Authentik application group."
  type        = string
  default     = "Homeserver"
}

variable "external_url" {
  description = "External URL protected by forward-auth."
  type        = string
}

variable "launch_url" {
  description = "URL opened from the Authentik application launcher."
  type        = string
}

variable "description" {
  description = "User-facing Authentik application description."
  type        = string
}

variable "allowed_groups" {
  description = "Authentik groups allowed to launch the application."
  type        = list(string)

  validation {
    condition     = length(var.allowed_groups) > 0
    error_message = "At least one allowed group is required."
  }

  validation {
    condition     = length(var.allowed_groups) == length(distinct(var.allowed_groups))
    error_message = "Allowed groups must be unique."
  }
}

variable "authentication_flow_id" {
  description = "UUID of the Authentik authentication flow."
  type        = string
}

variable "authorization_flow_id" {
  description = "ID of the Authentik authorization flow."
  type        = string
}

variable "invalidation_flow_id" {
  description = "ID of the Authentik invalidation flow."
  type        = string
}

variable "outpost_id" {
  description = "ID of the Authentik proxy outpost."
  type        = string
}
