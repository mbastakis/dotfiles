locals {
  immich_redirect_uris = [
    "${var.immich_external_url}/auth/login",
    "${var.immich_external_url}/user-settings",
    "app.immich:///oauth-callback",
  ]

  immich_allowed_group_keys = [
    "household",
    "admins",
  ]
}

resource "tls_private_key" "immich_signing" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

resource "tls_self_signed_cert" "immich_signing" {
  private_key_pem       = tls_private_key.immich_signing.private_key_pem
  validity_period_hours = 87600
  early_renewal_hours   = 720
  allowed_uses          = ["digital_signature"]

  subject {
    common_name  = "Immich OIDC Signing"
    organization = "mbastakis homeserver"
  }
}

resource "authentik_certificate_key_pair" "immich_signing" {
  name             = "homeserver-immich-oidc-signing"
  certificate_data = tls_self_signed_cert.immich_signing.cert_pem
  key_data         = tls_private_key.immich_signing.private_key_pem
}

resource "authentik_property_mapping_provider_scope" "immich_role" {
  name       = "homeserver-immich-role"
  scope_name = "immich"
  expression = <<-EOT
return {
    "immich_role": "admin" if request.user.username == ${jsonencode(var.immich_admin_username)} else "user",
}
EOT
}

resource "authentik_provider_oauth2" "immich" {
  name                = "immich"
  client_id           = var.immich_client_id
  client_secret       = var.immich_oidc_client_secret
  client_type         = "confidential"
  grant_types         = ["authorization_code", "refresh_token"]
  authentication_flow = authentik_flow.homeserver_authentication.uuid
  authorization_flow  = data.authentik_flow.provider_authorization.id
  invalidation_flow   = data.authentik_flow.provider_invalidation.id

  allowed_redirect_uris = [
    for uri in local.immich_redirect_uris : {
      matching_mode     = "strict"
      redirect_uri_type = "authorization"
      url               = uri
    }
  ]

  include_claims_in_id_token = true
  issuer_mode                = "per_provider"
  sub_mode                   = "user_username"
  signing_key                = authentik_certificate_key_pair.immich_signing.id
  logout_method              = "backchannel"
  logout_uri                 = "${var.immich_external_url}/api/oauth/backchannel-logout"
  access_token_validity      = "minutes=10"
  refresh_token_validity     = "days=7"
  property_mappings = concat(
    data.authentik_property_mapping_provider_scope.default_oauth_scopes.ids,
    [authentik_property_mapping_provider_scope.immich_role.id],
  )
}

resource "authentik_application" "immich" {
  name              = "Immich"
  slug              = "immich"
  protocol_provider = authentik_provider_oauth2.immich.id
  group             = "Homeserver"
  meta_launch_url   = var.immich_external_url
  meta_description  = "Private household photo library on atlas."
}

resource "authentik_policy_expression" "immich_access" {
  name = "homeserver-immich-access"
  expression = <<-EOT
allowed_groups = ${jsonencode([
  for group_key in local.immich_allowed_group_keys : local.homeserver_file_group_names[group_key]
])}
return request.user.username == ${jsonencode(var.immich_admin_username)} or any(
    group.name in allowed_groups for group in request.user.groups.all()
)
EOT
}

resource "authentik_policy_binding" "immich_access" {
  target = authentik_application.immich.uuid
  policy = authentik_policy_expression.immich_access.id
  order  = 0
}
