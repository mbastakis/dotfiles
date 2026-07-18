variable "bucket_name" {
  description = "Globally unique S3 bucket name."
  type        = string
}

variable "purpose" {
  description = "Stable purpose recorded in the bucket tags."
  type        = string
}

variable "tags" {
  description = "Additional tags applied to the bucket."
  type        = map(string)
  default     = {}
}

variable "versioning_enabled" {
  description = "Whether to enable S3 object versioning."
  type        = bool
  default     = false
}

variable "encryption" {
  description = "Server-side encryption policy for bucket objects."
  type = object({
    algorithm          = optional(string, "AES256")
    kms_key_arn        = optional(string)
    bucket_key_enabled = optional(bool)
  })
  default = {}

  validation {
    condition     = contains(["AES256", "aws:kms"], var.encryption.algorithm)
    error_message = "Encryption algorithm must be AES256 or aws:kms."
  }

  validation {
    condition = (
      var.encryption.algorithm == "aws:kms" ||
      (var.encryption.kms_key_arn == null && var.encryption.bucket_key_enabled == null)
    )
    error_message = "KMS key and bucket-key settings require the aws:kms algorithm."
  }
}

variable "lifecycle_rules" {
  description = "Optional object lifecycle rules."
  type = list(object({
    id     = string
    status = optional(string, "Enabled")
    prefix = optional(string, "")
    transitions = optional(list(object({
      days          = number
      storage_class = string
    })), [])
    abort_incomplete_multipart_upload_days = optional(number)
  }))
  default = []

  validation {
    condition = alltrue([
      for rule in var.lifecycle_rules : contains(["Enabled", "Disabled"], rule.status)
    ])
    error_message = "Lifecycle rule status must be Enabled or Disabled."
  }

  validation {
    condition = alltrue(flatten([
      for rule in var.lifecycle_rules : [
        for transition in rule.transitions : transition.days >= 0
      ]
    ]))
    error_message = "Lifecycle transition days must be zero or greater."
  }

  validation {
    condition = alltrue([
      for rule in var.lifecycle_rules : (
        rule.abort_incomplete_multipart_upload_days == null ||
        rule.abort_incomplete_multipart_upload_days > 0
      )
    ])
    error_message = "Multipart upload abort days must be greater than zero."
  }
}
