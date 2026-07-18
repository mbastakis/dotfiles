resource "tailscale_acl" "homeserver" {
  acl = file("${path.module}/../policy.hujson")

  overwrite_existing_content = false
  reset_acl_on_destroy       = false
}
