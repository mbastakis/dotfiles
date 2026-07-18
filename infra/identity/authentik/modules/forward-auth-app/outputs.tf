output "launch_url" {
  description = "Authentik application launch URL."
  value       = authentik_application.this.meta_launch_url
}

output "application_slug" {
  description = "Stable Authentik application slug."
  value       = authentik_application.this.slug
}
