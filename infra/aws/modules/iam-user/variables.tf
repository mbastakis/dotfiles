variable "user_name" {
  description = "IAM user name."
  type        = string
}

variable "purpose" {
  description = "Stable purpose recorded in the IAM user tags."
  type        = string
}

variable "policy_name" {
  description = "Name of the inline least-privilege policy."
  type        = string
}

variable "policy_json" {
  description = "Stack-owned least-privilege policy JSON."
  type        = string
}

variable "tags" {
  description = "Additional tags applied to the IAM user."
  type        = map(string)
  default     = {}
}
