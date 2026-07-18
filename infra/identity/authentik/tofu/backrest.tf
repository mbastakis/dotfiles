module "backrest" {
  source = "../modules/forward-auth-app"

  provider_name          = "backrest"
  application_name       = "Backrest"
  application_slug       = "backrest"
  external_url           = var.backrest_external_url
  launch_url             = var.backrest_external_url
  description            = "Private restic backup administration protected by Authentik forward-auth."
  allowed_groups         = [local.homeserver_file_group_names["admins"]]
  authentication_flow_id = authentik_flow.homeserver_authentication.uuid
  authorization_flow_id  = data.authentik_flow.provider_authorization.id
  invalidation_flow_id   = data.authentik_flow.provider_invalidation.id
  outpost_id             = data.authentik_outpost.embedded_proxy.id
}
