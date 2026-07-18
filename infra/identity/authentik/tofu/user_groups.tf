locals {
  homeserver_file_group_names = {
    admins    = "homeserver-files-admins"
    household = "homeserver-files-household"
    guests    = "homeserver-files-guests"
  }

  filebrowser_quantum_allowed_group_keys = [
    "household",
    "admins",
  ]
}

resource "authentik_group" "homeserver_files" {
  for_each = local.homeserver_file_group_names

  name = each.value
}

resource "authentik_group" "opencode_users" {
  name = "opencode-users"
}
