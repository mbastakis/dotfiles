data "authentik_flow" "provider_authorization" {
  slug = "default-provider-authorization-implicit-consent"
}

data "authentik_flow" "provider_invalidation" {
  slug = "default-provider-invalidation-flow"
}

resource "authentik_flow" "homeserver_authentication" {
  name        = "homeserver-authentication"
  title       = "Homeserver Authentication"
  slug        = "homeserver-authentication"
  designation = "authentication"
}

resource "authentik_stage_password" "homeserver_password" {
  name     = "homeserver-password"
  backends = ["authentik.core.auth.InbuiltBackend"]
}

resource "authentik_stage_identification" "homeserver_identification" {
  name           = "homeserver-identification"
  user_fields    = ["username", "email"]
  password_stage = authentik_stage_password.homeserver_password.id
}

resource "authentik_stage_user_login" "homeserver_user_login" {
  name             = "homeserver-user-login"
  session_duration = var.sso_session_duration
}

resource "authentik_flow_stage_binding" "homeserver_identification" {
  target = authentik_flow.homeserver_authentication.uuid
  stage  = authentik_stage_identification.homeserver_identification.id
  order  = 10
}

resource "authentik_flow_stage_binding" "homeserver_user_login" {
  target = authentik_flow.homeserver_authentication.uuid
  stage  = authentik_stage_user_login.homeserver_user_login.id
  order  = 20
}

# ---------------------------------------------------------------------------
# Force password reset on first login
#
# Users are created with attributes.reset_password = true. Two expression
# policies gate a prompt stage (new password entry) and a user-write stage
# (persist new password + clear the marker) that are bound inline in the
# authentication flow between identification (order 10) and user-login
# (order 20). After first login the user-write stage flips reset_password to
# false; the authentik_user lifecycle ignores attributes drift so OpenTofu
# does not fight the runtime mutation.
# ---------------------------------------------------------------------------

resource "authentik_stage_prompt_field" "homeserver_force_reset_password" {
  name      = "homeserver-force-reset-password"
  field_key = "password"
  label     = "New Password"
  type      = "password"
  required  = true
  order     = 100
}

resource "authentik_stage_prompt_field" "homeserver_force_reset_password_repeat" {
  name      = "homeserver-force-reset-password-repeat"
  field_key = "password_repeat"
  label     = "New Password (repeat)"
  type      = "password"
  required  = true
  order     = 101
}

resource "authentik_stage_prompt" "homeserver_force_reset_password" {
  name = "homeserver-force-reset-password"
  fields = [
    authentik_stage_prompt_field.homeserver_force_reset_password.id,
    authentik_stage_prompt_field.homeserver_force_reset_password_repeat.id,
  ]
}

resource "authentik_stage_user_write" "homeserver_force_reset_password" {
  name               = "homeserver-force-reset-write"
  user_creation_mode = "never_create"
}

resource "authentik_policy_expression" "homeserver_reset_password_check" {
  name       = "homeserver-reset-password-check"
  expression = <<-EOT
    if request.context["pending_user"].attributes.get("reset_password") == True:
        return True
    return False
  EOT
}

resource "authentik_policy_expression" "homeserver_reset_password_update" {
  name       = "homeserver-reset-password-update"
  expression = <<-EOT
    if request.context["pending_user"].attributes.get("reset_password") == True:
        request.context["pending_user"].attributes["reset_password"] = False
        return True
    return False
  EOT
}

resource "authentik_flow_stage_binding" "homeserver_force_reset_prompt" {
  target = authentik_flow.homeserver_authentication.uuid
  stage  = authentik_stage_prompt.homeserver_force_reset_password.id
  order  = 15
}

resource "authentik_flow_stage_binding" "homeserver_force_reset_write" {
  target = authentik_flow.homeserver_authentication.uuid
  stage  = authentik_stage_user_write.homeserver_force_reset_password.id
  order  = 16
}

resource "authentik_policy_binding" "homeserver_reset_password_check" {
  target = authentik_flow_stage_binding.homeserver_force_reset_prompt.id
  policy = authentik_policy_expression.homeserver_reset_password_check.id
  order  = 10
}

resource "authentik_policy_binding" "homeserver_reset_password_update" {
  target = authentik_flow_stage_binding.homeserver_force_reset_write.id
  policy = authentik_policy_expression.homeserver_reset_password_update.id
  order  = 10
}
