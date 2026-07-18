module "pihole" {
  source = "../modules/forward-auth-app"

  provider_name          = "pihole"
  application_name       = "Pi-hole"
  application_slug       = "pihole"
  external_url           = var.pihole_external_url
  launch_url             = "${var.pihole_external_url}/admin/"
  description            = "Private DNS filtering administration protected by Authentik forward-auth."
  allowed_groups         = [local.homeserver_file_group_names["admins"]]
  authentication_flow_id = authentik_flow.homeserver_authentication.uuid
  authorization_flow_id  = data.authentik_flow.provider_authorization.id
  invalidation_flow_id   = data.authentik_flow.provider_invalidation.id
  outpost_id             = data.authentik_outpost.embedded_proxy.id
}
