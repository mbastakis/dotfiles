mock_provider "authentik" {
  mock_resource "authentik_provider_proxy" {
    defaults = {
      id = 1
    }
  }

  mock_resource "authentik_policy_expression" {
    defaults = {
      id = 2
    }
  }
}

variables {
  provider_name          = "example"
  application_name       = "Example"
  application_slug       = "example"
  external_url           = "https://example.invalid"
  launch_url             = "https://example.invalid/dashboard/"
  description            = "Example protected application."
  allowed_groups         = ["example-admins"]
  authentication_flow_id = "authentication-flow"
  authorization_flow_id  = "authorization-flow"
  invalidation_flow_id   = "invalidation-flow"
  outpost_id             = "embedded-outpost"
}

run "creates_a_complete_forward_auth_graph" {
  command = plan

  assert {
    condition = (
      authentik_provider_proxy.this.name == "example" &&
      authentik_provider_proxy.this.mode == "forward_single" &&
      authentik_provider_proxy.this.external_host == "https://example.invalid"
    )
    error_message = "The proxy provider must preserve its stable identity and URL."
  }

  assert {
    condition = (
      authentik_application.this.name == "Example" &&
      authentik_application.this.slug == "example" &&
      authentik_application.this.group == "Homeserver" &&
      authentik_application.this.meta_launch_url == "https://example.invalid/dashboard/"
    )
    error_message = "The application identity and launcher metadata must be preserved."
  }

  assert {
    condition = strcontains(
      authentik_policy_expression.access.expression,
      "group.name == \"example-admins\"",
    )
    error_message = "The access policy must contain the allowed group."
  }

  assert {
    condition     = authentik_policy_binding.access.order == 0
    error_message = "The application access policy must have deterministic order."
  }

  assert {
    condition     = authentik_outpost_provider_attachment.this.outpost == "embedded-outpost"
    error_message = "The proxy provider must attach to the requested outpost."
  }
}
