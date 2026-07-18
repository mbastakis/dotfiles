data "authentik_outpost" "embedded_proxy" {
  name = var.authentik_embedded_outpost_name
}

module "traefik_dashboard" {
  source = "../modules/forward-auth-app"

  provider_name          = "traefik-dashboard"
  application_name       = "Traefik Dashboard"
  application_slug       = "traefik-dashboard"
  external_url           = var.traefik_dashboard_external_url
  launch_url             = "${var.traefik_dashboard_external_url}/dashboard/"
  description            = "Private reverse-proxy dashboard protected by Authentik forward-auth."
  allowed_groups         = [local.homeserver_file_group_names["admins"]]
  authentication_flow_id = authentik_flow.homeserver_authentication.uuid
  authorization_flow_id  = data.authentik_flow.provider_authorization.id
  invalidation_flow_id   = data.authentik_flow.provider_invalidation.id
  outpost_id             = data.authentik_outpost.embedded_proxy.id
}
