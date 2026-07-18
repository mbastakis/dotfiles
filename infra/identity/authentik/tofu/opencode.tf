locals {
  opencode_redirect_uri = "${var.opencode_external_url}/oauth2/callback"
}

data "authentik_property_mapping_provider_scope" "opencode_offline_access" {
  managed_list = ["goauthentik.io/providers/oauth2/scope-offline_access"]
}

resource "tls_private_key" "opencode_signing" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

resource "tls_self_signed_cert" "opencode_signing" {
  private_key_pem       = tls_private_key.opencode_signing.private_key_pem
  validity_period_hours = 87600
  early_renewal_hours   = 720
  allowed_uses          = ["digital_signature"]

  subject {
    common_name  = "OpenCode OIDC Signing"
    organization = "mbastakis homeserver"
  }
}

resource "authentik_certificate_key_pair" "opencode_signing" {
  name             = "opencode-oidc-signing"
  certificate_data = tls_self_signed_cert.opencode_signing.cert_pem
  key_data         = tls_private_key.opencode_signing.private_key_pem
}

resource "authentik_provider_oauth2" "opencode" {
  name                = "opencode"
  client_id           = var.opencode_client_id
  client_secret       = var.opencode_oidc_client_secret
  client_type         = "confidential"
  grant_types         = ["authorization_code", "refresh_token"]
  authentication_flow = authentik_flow.homeserver_authentication.uuid
  authorization_flow  = data.authentik_flow.provider_authorization.id
  invalidation_flow   = data.authentik_flow.provider_invalidation.id

  allowed_redirect_uris = [
    {
      matching_mode     = "strict"
      redirect_uri_type = "authorization"
      url               = local.opencode_redirect_uri
    }
  ]

  include_claims_in_id_token = true
  issuer_mode                = "per_provider"
  sub_mode                   = "user_username"
  signing_key                = authentik_certificate_key_pair.opencode_signing.id
  access_token_validity      = "minutes=10"
  refresh_token_validity     = "days=7"
  property_mappings = concat(
    data.authentik_property_mapping_provider_scope.default_oauth_scopes.ids,
    data.authentik_property_mapping_provider_scope.opencode_offline_access.ids,
    [authentik_property_mapping_provider_scope.groups.id],
  )
}

resource "authentik_application" "opencode" {
  name               = "OpenCode"
  slug               = "opencode"
  protocol_provider  = authentik_provider_oauth2.opencode.id
  group              = "Developer Tools"
  meta_launch_url    = var.opencode_external_url
  meta_description   = "Tailnet-only mobile access to OpenCode sessions on Michail's Mac."
  policy_engine_mode = "all"
}

resource "authentik_policy_expression" "opencode_access" {
  name       = "opencode-michail-access"
  expression = <<-EOT
return any(
    group.name == ${jsonencode(authentik_group.opencode_users.name)}
    for group in request.user.ak_groups.all()
)
EOT
}

resource "authentik_policy_binding" "opencode_access" {
  target = authentik_application.opencode.uuid
  policy = authentik_policy_expression.opencode_access.id
  order  = 0
}
