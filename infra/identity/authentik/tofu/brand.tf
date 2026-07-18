data "authentik_flow" "default_invalidation" {
  slug = "default-invalidation-flow"
}

data "authentik_flow" "default_user_settings" {
  slug = "default-user-settings-flow"
}

resource "authentik_brand" "default" {
  domain  = "authentik-default"
  default = true

  branding_title                   = "Hyperion"
  branding_logo                    = "https://home.mbastakis.com/images/hyperion.png"
  branding_favicon                 = "https://home.mbastakis.com/images/hyperion.png"
  branding_custom_css              = trimspace(file("${path.module}/catppuccin-mocha.css"))
  branding_default_flow_background = "https://home.mbastakis.com/images/background.jpg"

  flow_authentication = authentik_flow.homeserver_authentication.uuid
  flow_invalidation   = data.authentik_flow.default_invalidation.id
  flow_user_settings  = data.authentik_flow.default_user_settings.id

  attributes = jsonencode({
    settings = {
      theme = {
        base = "dark"
      }
    }
  })

  lifecycle {
    prevent_destroy = true
  }
}
