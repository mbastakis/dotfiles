locals {
  filebrowser_quantum_redirect_uri = "${var.filebrowser_quantum_external_url}/api/auth/oidc/callback"
}

data "authentik_property_mapping_provider_scope" "default_oauth_scopes" {
  managed_list = [
    "goauthentik.io/providers/oauth2/scope-openid",
    "goauthentik.io/providers/oauth2/scope-email",
    "goauthentik.io/providers/oauth2/scope-profile",
  ]
}

resource "authentik_property_mapping_provider_scope" "groups" {
  name       = "homeserver-groups"
  scope_name = "groups"
  expression = <<-EOT
return {
    "groups": [group.name for group in request.user.ak_groups.all()],
}
EOT
}

resource "authentik_provider_oauth2" "filebrowser_quantum" {
  name                = "filebrowser-quantum"
  client_id           = var.filebrowser_quantum_client_id
  client_secret       = var.filebrowser_quantum_oidc_client_secret
  client_type         = "confidential"
  grant_types         = ["authorization_code", "refresh_token"]
  authentication_flow = authentik_flow.homeserver_authentication.uuid
  authorization_flow  = data.authentik_flow.provider_authorization.id
  invalidation_flow   = data.authentik_flow.provider_invalidation.id

  allowed_redirect_uris = [
    {
      matching_mode     = "strict"
      redirect_uri_type = "authorization"
      url               = local.filebrowser_quantum_redirect_uri
    }
  ]

  include_claims_in_id_token = true
  issuer_mode                = "per_provider"
  sub_mode                   = "user_username"
  access_token_validity      = "minutes=10"
  refresh_token_validity     = "days=7"
  property_mappings = concat(
    data.authentik_property_mapping_provider_scope.default_oauth_scopes.ids,
    [authentik_property_mapping_provider_scope.groups.id],
  )
}

resource "authentik_application" "filebrowser_quantum" {
  name              = "Homeserver Files"
  slug              = "filebrowser-quantum"
  protocol_provider = authentik_provider_oauth2.filebrowser_quantum.id
  group             = "Homeserver"
  meta_launch_url   = var.filebrowser_quantum_external_url
  meta_description  = "Private household file access through FileBrowser Quantum."
}

resource "authentik_policy_expression" "filebrowser_quantum_access" {
  name = "homeserver-filebrowser-access"
  expression = <<-EOT
allowed_groups = ${jsonencode([
  for group_key in local.filebrowser_quantum_allowed_group_keys : local.homeserver_file_group_names[group_key]
])}
return any(group.name in allowed_groups for group in request.user.ak_groups.all())
EOT
}

resource "authentik_policy_binding" "filebrowser_quantum_access" {
  target = authentik_application.filebrowser_quantum.uuid
  policy = authentik_policy_expression.filebrowser_quantum_access.id
  order  = 0
}
