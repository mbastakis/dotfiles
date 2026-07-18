locals {
  access_condition = length(var.allowed_groups) == 1 ? (
    "group.name == ${jsonencode(var.allowed_groups[0])}"
    ) : (
    "group.name in ${jsonencode(var.allowed_groups)}"
  )
  access_expression = <<-EOT
return any(
    ${local.access_condition}
    for group in request.user.ak_groups.all()
)
EOT
}

resource "authentik_provider_proxy" "this" {
  name                = var.provider_name
  mode                = "forward_single"
  external_host       = var.external_url
  authentication_flow = var.authentication_flow_id
  authorization_flow  = var.authorization_flow_id
  invalidation_flow   = var.invalidation_flow_id
}

resource "authentik_application" "this" {
  name              = var.application_name
  slug              = var.application_slug
  protocol_provider = authentik_provider_proxy.this.id
  group             = var.application_group
  meta_launch_url   = var.launch_url
  meta_description  = var.description
}

resource "authentik_policy_expression" "access" {
  name       = "homeserver-${var.application_slug}-access"
  expression = local.access_expression
}

resource "authentik_policy_binding" "access" {
  target = authentik_application.this.uuid
  policy = authentik_policy_expression.access.id
  order  = 0
}

resource "authentik_outpost_provider_attachment" "this" {
  outpost           = var.outpost_id
  protocol_provider = authentik_provider_proxy.this.id
}
