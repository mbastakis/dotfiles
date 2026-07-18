output "filebrowser_quantum_issuer_url" {
  description = "OIDC issuer URL for FileBrowser Quantum."
  value       = "${var.authentik_url}/application/o/${authentik_application.filebrowser_quantum.slug}/"
}

output "filebrowser_quantum_client_id" {
  description = "OIDC client ID for FileBrowser Quantum."
  value       = authentik_provider_oauth2.filebrowser_quantum.client_id
}

output "filebrowser_quantum_redirect_uri" {
  description = "OIDC redirect URI registered for FileBrowser Quantum."
  value       = local.filebrowser_quantum_redirect_uri
}

output "immich_issuer_url" {
  description = "OIDC issuer URL for Immich."
  value       = "${var.authentik_url}/application/o/${authentik_application.immich.slug}/"
}

output "immich_client_id" {
  description = "OIDC client ID for Immich."
  value       = authentik_provider_oauth2.immich.client_id
}

output "immich_redirect_uris" {
  description = "OIDC redirect URIs registered for Immich web and mobile clients."
  value       = local.immich_redirect_uris
}

output "audiobookshelf_issuer_url" {
  description = "OIDC issuer URL for Audiobookshelf."
  value       = "${var.authentik_url}/application/o/${authentik_application.audiobookshelf.slug}/"
}

output "audiobookshelf_client_id" {
  description = "OIDC client ID for Audiobookshelf."
  value       = authentik_provider_oauth2.audiobookshelf.client_id
}

output "audiobookshelf_redirect_uris" {
  description = "OIDC redirect URIs registered for Audiobookshelf web and mobile clients."
  value       = local.audiobookshelf_redirect_uris
}

output "opencode_issuer_url" {
  description = "OIDC issuer URL for the Mac OpenCode oauth2-proxy."
  value       = "${var.authentik_url}/application/o/${authentik_application.opencode.slug}/"
}

output "opencode_client_id" {
  description = "OIDC client ID for the Mac OpenCode oauth2-proxy."
  value       = authentik_provider_oauth2.opencode.client_id
}

output "opencode_redirect_uri" {
  description = "OIDC redirect URI registered for the Mac OpenCode oauth2-proxy."
  value       = local.opencode_redirect_uri
}

output "homeserver_file_groups" {
  description = "Authentik groups used by FileBrowser Quantum."
  value = {
    for key, group in authentik_group.homeserver_files : key => group.name
  }
}

output "opencode_group" {
  description = "Authentik group allowed to access the OpenCode mobile application."
  value       = authentik_group.opencode_users.name
}

output "traefik_dashboard_launch_url" {
  description = "Authentik-protected Traefik dashboard URL."
  value       = module.traefik_dashboard.launch_url
}

output "taskboard_launch_url" {
  description = "Authentik-protected Sisyphus URL."
  value       = module.taskboard.launch_url
}

output "backrest_launch_url" {
  description = "Authentik-protected Backrest URL."
  value       = module.backrest.launch_url
}

output "pihole_launch_url" {
  description = "Authentik-protected Pi-hole administration URL."
  value       = module.pihole.launch_url
}
