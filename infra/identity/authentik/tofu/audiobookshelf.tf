locals {
  audiobookshelf_redirect_uris = [
    "${var.audiobookshelf_external_url}/audiobookshelf/auth/openid/callback",
    "${var.audiobookshelf_external_url}/audiobookshelf/auth/openid/mobile-redirect",
  ]

  audiobookshelf_allowed_group_keys = [
    "household",
    "admins",
  ]
}

resource "tls_private_key" "audiobookshelf_signing" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

resource "tls_self_signed_cert" "audiobookshelf_signing" {
  private_key_pem       = tls_private_key.audiobookshelf_signing.private_key_pem
  validity_period_hours = 87600
  early_renewal_hours   = 720
  allowed_uses          = ["digital_signature"]

  subject {
    common_name  = "Audiobookshelf OIDC Signing"
    organization = "mbastakis homeserver"
  }
}

resource "authentik_certificate_key_pair" "audiobookshelf_signing" {
  name             = "homeserver-audiobookshelf-oidc-signing"
  certificate_data = tls_self_signed_cert.audiobookshelf_signing.cert_pem
  key_data         = tls_private_key.audiobookshelf_signing.private_key_pem
}

resource "authentik_property_mapping_provider_scope" "audiobookshelf_role" {
  name       = "homeserver-audiobookshelf-role"
  scope_name = "audiobookshelf"
  expression = <<-EOT
return {
    "audiobookshelf": ["admin" if request.user.username == ${jsonencode(var.audiobookshelf_admin_username)} else "user"],
}
EOT
}

resource "authentik_provider_oauth2" "audiobookshelf" {
  name                = "audiobookshelf"
  client_id           = var.audiobookshelf_client_id
  client_secret       = var.audiobookshelf_oidc_client_secret
  client_type         = "confidential"
  grant_types         = ["authorization_code", "refresh_token"]
  authentication_flow = authentik_flow.homeserver_authentication.uuid
  authorization_flow  = data.authentik_flow.provider_authorization.id
  invalidation_flow   = data.authentik_flow.provider_invalidation.id

  allowed_redirect_uris = [
    for uri in local.audiobookshelf_redirect_uris : {
      matching_mode     = "strict"
      redirect_uri_type = "authorization"
      url               = uri
    }
  ]

  include_claims_in_id_token = true
  issuer_mode                = "per_provider"
  sub_mode                   = "user_username"
  signing_key                = authentik_certificate_key_pair.audiobookshelf_signing.id
  access_token_validity      = "minutes=10"
  refresh_token_validity     = "days=7"
  property_mappings = concat(
    data.authentik_property_mapping_provider_scope.default_oauth_scopes.ids,
    [authentik_property_mapping_provider_scope.audiobookshelf_role.id],
  )
}

resource "authentik_application" "audiobookshelf" {
  name              = "Audiobookshelf"
  slug              = "audiobookshelf"
  protocol_provider = authentik_provider_oauth2.audiobookshelf.id
  group             = "Homeserver"
  meta_launch_url   = "${var.audiobookshelf_external_url}/audiobookshelf/"
  meta_description  = "Private household audiobook and ebook library."
}

resource "authentik_policy_expression" "audiobookshelf_access" {
  name = "homeserver-audiobookshelf-access"
  expression = <<-EOT
allowed_groups = ${jsonencode([
  for group_key in local.audiobookshelf_allowed_group_keys : local.homeserver_file_group_names[group_key]
])}
return any(group.name in allowed_groups for group in request.user.groups.all())
EOT
}

resource "authentik_policy_binding" "audiobookshelf_access" {
  target = authentik_application.audiobookshelf.uuid
  policy = authentik_policy_expression.audiobookshelf_access.id
  order  = 0
}
