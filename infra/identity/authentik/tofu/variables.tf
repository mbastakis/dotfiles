variable "authentik_url" {
  description = "Authentik API endpoint."
  type        = string
  default     = "https://auth.mbastakis.com"
}

variable "authentik_token" {
  description = "Authentik API token. Supplied from BWS via AUTHENTIK_TOKEN/TF_VAR_authentik_token."
  type        = string
  sensitive   = true
}

variable "michail_initial_password" {
  description = "Unique onboarding password for the Authentik michail user."
  type        = string
  sensitive   = true
}

variable "chara_initial_password" {
  description = "Unique onboarding password for the Authentik chara user."
  type        = string
  sensitive   = true
}

variable "filebrowser_quantum_oidc_client_secret" {
  description = "OIDC client secret shared by Authentik and FileBrowser Quantum."
  type        = string
  sensitive   = true
}

variable "filebrowser_quantum_client_id" {
  description = "OIDC client ID used by FileBrowser Quantum."
  type        = string
  default     = "homeserver-filebrowser-quantum"
}

variable "filebrowser_quantum_external_url" {
  description = "External private URL for FileBrowser Quantum through Traefik."
  type        = string
  default     = "https://files.mbastakis.com"
}

variable "immich_oidc_client_secret" {
  description = "OIDC client secret shared by Authentik and Immich."
  type        = string
  sensitive   = true
}

variable "immich_client_id" {
  description = "OIDC client ID used by Immich."
  type        = string
  default     = "homeserver-immich"
}

variable "immich_external_url" {
  description = "External private URL for Immich through Traefik."
  type        = string
  default     = "https://photos.mbastakis.com"
}

variable "immich_admin_username" {
  description = "Only Authentik username that may receive the Immich admin role claim."
  type        = string
  default     = "michail"
}

variable "audiobookshelf_oidc_client_secret" {
  description = "OIDC client secret shared by Authentik and Audiobookshelf."
  type        = string
  sensitive   = true
}

variable "audiobookshelf_client_id" {
  description = "OIDC client ID used by Audiobookshelf."
  type        = string
  default     = "homeserver-audiobookshelf"
}

variable "audiobookshelf_external_url" {
  description = "External private URL for Audiobookshelf through Traefik."
  type        = string
  default     = "https://audiobooks.mbastakis.com"
}

variable "audiobookshelf_admin_username" {
  description = "Only Authentik username that receives the Audiobookshelf admin role claim."
  type        = string
  default     = "michail"
}

variable "opencode_oidc_client_secret" {
  description = "OIDC client secret shared by Authentik and the Mac OpenCode oauth2-proxy."
  type        = string
  sensitive   = true
}

variable "opencode_client_id" {
  description = "OIDC client ID used by the Mac OpenCode oauth2-proxy."
  type        = string
  default     = "opencode-mobile"
}

variable "opencode_external_url" {
  description = "Tailnet-only OpenCode URL routed through Atlas to Michail's Mac."
  type        = string
  default     = "https://code.mbastakis.com"
}

variable "traefik_dashboard_external_url" {
  description = "External private URL for the Traefik dashboard through Traefik and Authentik forward-auth."
  type        = string
  default     = "https://traefik.mbastakis.com"
}

variable "taskboard_external_url" {
  description = "External private URL for Sisyphus through Traefik and Authentik forward-auth."
  type        = string
  default     = "https://taskboard.mbastakis.com"
}

variable "backrest_external_url" {
  description = "External private URL for Backrest through Traefik and Authentik forward-auth."
  type        = string
  default     = "https://backrest.mbastakis.com"
}

variable "pihole_external_url" {
  description = "External private URL for Pi-hole through Traefik and Authentik forward-auth."
  type        = string
  default     = "https://pihole.mbastakis.com"
}

variable "authentik_embedded_outpost_name" {
  description = "Name of the built-in Authentik proxy outpost used for forward-auth providers."
  type        = string
  default     = "authentik Embedded Outpost"
}

variable "sso_session_duration" {
  description = "Authentik user-login session duration for homeserver application auth flows."
  type        = string
  default     = "days=7"
}
