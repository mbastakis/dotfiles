provider "truenas" {
  host        = var.truenas_connection_host
  auth_method = "ssh"

  ssh {
    user                 = var.truenas_ssh_user
    port                 = var.truenas_ssh_port
    private_key          = var.truenas_ssh_private_key
    host_key_fingerprint = var.truenas_ssh_host_key_fingerprint
  }
}
