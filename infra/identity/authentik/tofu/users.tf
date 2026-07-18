locals {
  homeserver_users = {
    michail = {
      username = "michail"
      name     = "Michail"
      email    = "mbastakis@gmail.com"
      groups = [
        "admins",
        "household",
      ]
    }
    chara = {
      username = "chara"
      name     = "Chara"
      email    = ""
      groups = [
        "household",
      ]
    }
  }

  homeserver_user_initial_passwords = {
    michail = var.michail_initial_password
    chara   = var.chara_initial_password
  }
}

resource "authentik_user" "homeserver" {
  for_each = local.homeserver_users

  username   = each.value.username
  name       = each.value.name
  email      = each.value.email
  password   = local.homeserver_user_initial_passwords[each.key]
  attributes = jsonencode({ reset_password = true })
  groups = concat(
    [
      for group_key in each.value.groups : authentik_group.homeserver_files[group_key].id
    ],
    each.key == "michail" ? [authentik_group.opencode_users.id] : [],
  )

  lifecycle {
    # OpenTofu owns the onboarding password and the reset marker only.
    # Once users change their password through the force-reset flow,
    # Authentik flips reset_password to false and stores the new password.
    # Future applies must not reset either value back to bootstrap state.
    ignore_changes = [password, attributes]
  }
}
