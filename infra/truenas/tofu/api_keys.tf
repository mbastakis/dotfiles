resource "null_resource" "homepage_truenas_api_key" {
  triggers = {
    bws_project_id = var.homeserver_bws_project_id
    bws_secret_key = var.homepage_truenas_api_key_secret_key
    key_name       = var.homepage_truenas_api_key_name
    key_username   = var.homepage_truenas_api_key_username
    truenas_host   = var.truenas_host
    truenas_port   = tostring(var.truenas_ssh_port)
    truenas_user   = var.truenas_ssh_user
  }

  provisioner "local-exec" {
    interpreter = ["/bin/bash", "-c"]

    environment = {
      BWS_PROJECT_ID           = var.homeserver_bws_project_id
      BWS_SECRET_KEY           = var.homepage_truenas_api_key_secret_key
      TRUENAS_API_KEY_NAME     = var.homepage_truenas_api_key_name
      TRUENAS_API_KEY_USERNAME = var.homepage_truenas_api_key_username
      TRUENAS_HOST             = var.truenas_connection_host
      TRUENAS_SSH_PORT         = tostring(var.truenas_ssh_port)
      TRUENAS_SSH_PRIVATE_KEY  = var.truenas_ssh_private_key
      TRUENAS_SSH_USER         = var.truenas_ssh_user
    }

    command = <<-EOT
      set -euo pipefail

      repo_root="$(cd "${path.module}/../../.." && pwd)"
      uv run --project "$repo_root/infra" --offline --locked \
        python -m homeserver_iac api-key apply \
        --host "$TRUENAS_SSH_USER@$TRUENAS_HOST" \
        --port "$TRUENAS_SSH_PORT" \
        --name "$TRUENAS_API_KEY_NAME" \
        --username "$TRUENAS_API_KEY_USERNAME" \
        --secret-alias truenas_api_key \
        --secret-key "$BWS_SECRET_KEY" \
        --project-id "$BWS_PROJECT_ID"
    EOT
  }

  lifecycle {
    prevent_destroy = true
  }
}
