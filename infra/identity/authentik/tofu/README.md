<!-- BEGIN_TF_DOCS -->
## Requirements

| Name | Version |
| ---- | ------- |
| terraform | >= 1.8.0 |
| authentik | ~> 2026.5 |
| tls | ~> 4.1 |

## Providers

| Name | Version |
| ---- | ------- |
| authentik | 2026.5.0 |
| tls | 4.3.0 |

## Modules

| Name | Source | Version |
| ---- | ------ | ------- |
| backrest | ../modules/forward-auth-app | n/a |
| pihole | ../modules/forward-auth-app | n/a |
| taskboard | ../modules/forward-auth-app | n/a |
| traefik\_dashboard | ../modules/forward-auth-app | n/a |

## Resources

| Name | Type |
| ---- | ---- |
| [authentik_application.audiobookshelf](https://registry.terraform.io/providers/goauthentik/authentik/latest/docs/resources/application) | resource |
| [authentik_application.filebrowser_quantum](https://registry.terraform.io/providers/goauthentik/authentik/latest/docs/resources/application) | resource |
| [authentik_application.immich](https://registry.terraform.io/providers/goauthentik/authentik/latest/docs/resources/application) | resource |
| [authentik_application.opencode](https://registry.terraform.io/providers/goauthentik/authentik/latest/docs/resources/application) | resource |
| [authentik_brand.default](https://registry.terraform.io/providers/goauthentik/authentik/latest/docs/resources/brand) | resource |
| [authentik_certificate_key_pair.audiobookshelf_signing](https://registry.terraform.io/providers/goauthentik/authentik/latest/docs/resources/certificate_key_pair) | resource |
| [authentik_certificate_key_pair.immich_signing](https://registry.terraform.io/providers/goauthentik/authentik/latest/docs/resources/certificate_key_pair) | resource |
| [authentik_certificate_key_pair.opencode_signing](https://registry.terraform.io/providers/goauthentik/authentik/latest/docs/resources/certificate_key_pair) | resource |
| [authentik_flow.homeserver_authentication](https://registry.terraform.io/providers/goauthentik/authentik/latest/docs/resources/flow) | resource |
| [authentik_flow_stage_binding.homeserver_force_reset_prompt](https://registry.terraform.io/providers/goauthentik/authentik/latest/docs/resources/flow_stage_binding) | resource |
| [authentik_flow_stage_binding.homeserver_force_reset_write](https://registry.terraform.io/providers/goauthentik/authentik/latest/docs/resources/flow_stage_binding) | resource |
| [authentik_flow_stage_binding.homeserver_identification](https://registry.terraform.io/providers/goauthentik/authentik/latest/docs/resources/flow_stage_binding) | resource |
| [authentik_flow_stage_binding.homeserver_user_login](https://registry.terraform.io/providers/goauthentik/authentik/latest/docs/resources/flow_stage_binding) | resource |
| [authentik_group.homeserver_files](https://registry.terraform.io/providers/goauthentik/authentik/latest/docs/resources/group) | resource |
| [authentik_group.opencode_users](https://registry.terraform.io/providers/goauthentik/authentik/latest/docs/resources/group) | resource |
| [authentik_policy_binding.audiobookshelf_access](https://registry.terraform.io/providers/goauthentik/authentik/latest/docs/resources/policy_binding) | resource |
| [authentik_policy_binding.filebrowser_quantum_access](https://registry.terraform.io/providers/goauthentik/authentik/latest/docs/resources/policy_binding) | resource |
| [authentik_policy_binding.homeserver_reset_password_check](https://registry.terraform.io/providers/goauthentik/authentik/latest/docs/resources/policy_binding) | resource |
| [authentik_policy_binding.homeserver_reset_password_update](https://registry.terraform.io/providers/goauthentik/authentik/latest/docs/resources/policy_binding) | resource |
| [authentik_policy_binding.immich_access](https://registry.terraform.io/providers/goauthentik/authentik/latest/docs/resources/policy_binding) | resource |
| [authentik_policy_binding.opencode_access](https://registry.terraform.io/providers/goauthentik/authentik/latest/docs/resources/policy_binding) | resource |
| [authentik_policy_expression.audiobookshelf_access](https://registry.terraform.io/providers/goauthentik/authentik/latest/docs/resources/policy_expression) | resource |
| [authentik_policy_expression.filebrowser_quantum_access](https://registry.terraform.io/providers/goauthentik/authentik/latest/docs/resources/policy_expression) | resource |
| [authentik_policy_expression.homeserver_reset_password_check](https://registry.terraform.io/providers/goauthentik/authentik/latest/docs/resources/policy_expression) | resource |
| [authentik_policy_expression.homeserver_reset_password_update](https://registry.terraform.io/providers/goauthentik/authentik/latest/docs/resources/policy_expression) | resource |
| [authentik_policy_expression.immich_access](https://registry.terraform.io/providers/goauthentik/authentik/latest/docs/resources/policy_expression) | resource |
| [authentik_policy_expression.opencode_access](https://registry.terraform.io/providers/goauthentik/authentik/latest/docs/resources/policy_expression) | resource |
| [authentik_property_mapping_provider_scope.audiobookshelf_role](https://registry.terraform.io/providers/goauthentik/authentik/latest/docs/resources/property_mapping_provider_scope) | resource |
| [authentik_property_mapping_provider_scope.groups](https://registry.terraform.io/providers/goauthentik/authentik/latest/docs/resources/property_mapping_provider_scope) | resource |
| [authentik_property_mapping_provider_scope.immich_role](https://registry.terraform.io/providers/goauthentik/authentik/latest/docs/resources/property_mapping_provider_scope) | resource |
| [authentik_provider_oauth2.audiobookshelf](https://registry.terraform.io/providers/goauthentik/authentik/latest/docs/resources/provider_oauth2) | resource |
| [authentik_provider_oauth2.filebrowser_quantum](https://registry.terraform.io/providers/goauthentik/authentik/latest/docs/resources/provider_oauth2) | resource |
| [authentik_provider_oauth2.immich](https://registry.terraform.io/providers/goauthentik/authentik/latest/docs/resources/provider_oauth2) | resource |
| [authentik_provider_oauth2.opencode](https://registry.terraform.io/providers/goauthentik/authentik/latest/docs/resources/provider_oauth2) | resource |
| [authentik_stage_identification.homeserver_identification](https://registry.terraform.io/providers/goauthentik/authentik/latest/docs/resources/stage_identification) | resource |
| [authentik_stage_password.homeserver_password](https://registry.terraform.io/providers/goauthentik/authentik/latest/docs/resources/stage_password) | resource |
| [authentik_stage_prompt.homeserver_force_reset_password](https://registry.terraform.io/providers/goauthentik/authentik/latest/docs/resources/stage_prompt) | resource |
| [authentik_stage_prompt_field.homeserver_force_reset_password](https://registry.terraform.io/providers/goauthentik/authentik/latest/docs/resources/stage_prompt_field) | resource |
| [authentik_stage_prompt_field.homeserver_force_reset_password_repeat](https://registry.terraform.io/providers/goauthentik/authentik/latest/docs/resources/stage_prompt_field) | resource |
| [authentik_stage_user_login.homeserver_user_login](https://registry.terraform.io/providers/goauthentik/authentik/latest/docs/resources/stage_user_login) | resource |
| [authentik_stage_user_write.homeserver_force_reset_password](https://registry.terraform.io/providers/goauthentik/authentik/latest/docs/resources/stage_user_write) | resource |
| [authentik_user.homeserver](https://registry.terraform.io/providers/goauthentik/authentik/latest/docs/resources/user) | resource |
| [tls_private_key.audiobookshelf_signing](https://registry.terraform.io/providers/hashicorp/tls/latest/docs/resources/private_key) | resource |
| [tls_private_key.immich_signing](https://registry.terraform.io/providers/hashicorp/tls/latest/docs/resources/private_key) | resource |
| [tls_private_key.opencode_signing](https://registry.terraform.io/providers/hashicorp/tls/latest/docs/resources/private_key) | resource |
| [tls_self_signed_cert.audiobookshelf_signing](https://registry.terraform.io/providers/hashicorp/tls/latest/docs/resources/self_signed_cert) | resource |
| [tls_self_signed_cert.immich_signing](https://registry.terraform.io/providers/hashicorp/tls/latest/docs/resources/self_signed_cert) | resource |
| [tls_self_signed_cert.opencode_signing](https://registry.terraform.io/providers/hashicorp/tls/latest/docs/resources/self_signed_cert) | resource |
| [authentik_flow.default_invalidation](https://registry.terraform.io/providers/goauthentik/authentik/latest/docs/data-sources/flow) | data source |
| [authentik_flow.default_user_settings](https://registry.terraform.io/providers/goauthentik/authentik/latest/docs/data-sources/flow) | data source |
| [authentik_flow.provider_authorization](https://registry.terraform.io/providers/goauthentik/authentik/latest/docs/data-sources/flow) | data source |
| [authentik_flow.provider_invalidation](https://registry.terraform.io/providers/goauthentik/authentik/latest/docs/data-sources/flow) | data source |
| [authentik_outpost.embedded_proxy](https://registry.terraform.io/providers/goauthentik/authentik/latest/docs/data-sources/outpost) | data source |
| [authentik_property_mapping_provider_scope.default_oauth_scopes](https://registry.terraform.io/providers/goauthentik/authentik/latest/docs/data-sources/property_mapping_provider_scope) | data source |
| [authentik_property_mapping_provider_scope.opencode_offline_access](https://registry.terraform.io/providers/goauthentik/authentik/latest/docs/data-sources/property_mapping_provider_scope) | data source |

## Inputs

| Name | Description | Type | Default | Required |
| ---- | ----------- | ---- | ------- | :------: |
| audiobookshelf\_admin\_username | Only Authentik username that receives the Audiobookshelf admin role claim. | `string` | `"michail"` | no |
| audiobookshelf\_client\_id | OIDC client ID used by Audiobookshelf. | `string` | `"homeserver-audiobookshelf"` | no |
| audiobookshelf\_external\_url | External private URL for Audiobookshelf through Traefik. | `string` | `"https://audiobooks.mbastakis.com"` | no |
| audiobookshelf\_oidc\_client\_secret | OIDC client secret shared by Authentik and Audiobookshelf. | `string` | n/a | yes |
| authentik\_embedded\_outpost\_name | Name of the built-in Authentik proxy outpost used for forward-auth providers. | `string` | `"authentik Embedded Outpost"` | no |
| authentik\_token | Authentik API token. Supplied from BWS via AUTHENTIK\_TOKEN/TF\_VAR\_authentik\_token. | `string` | n/a | yes |
| authentik\_url | Authentik API endpoint. | `string` | `"https://auth.mbastakis.com"` | no |
| backrest\_external\_url | External private URL for Backrest through Traefik and Authentik forward-auth. | `string` | `"https://backrest.mbastakis.com"` | no |
| chara\_initial\_password | Unique onboarding password for the Authentik chara user. | `string` | n/a | yes |
| filebrowser\_quantum\_client\_id | OIDC client ID used by FileBrowser Quantum. | `string` | `"homeserver-filebrowser-quantum"` | no |
| filebrowser\_quantum\_external\_url | External private URL for FileBrowser Quantum through Traefik. | `string` | `"https://files.mbastakis.com"` | no |
| filebrowser\_quantum\_oidc\_client\_secret | OIDC client secret shared by Authentik and FileBrowser Quantum. | `string` | n/a | yes |
| immich\_admin\_username | Only Authentik username that may receive the Immich admin role claim. | `string` | `"michail"` | no |
| immich\_client\_id | OIDC client ID used by Immich. | `string` | `"homeserver-immich"` | no |
| immich\_external\_url | External private URL for Immich through Traefik. | `string` | `"https://photos.mbastakis.com"` | no |
| immich\_oidc\_client\_secret | OIDC client secret shared by Authentik and Immich. | `string` | n/a | yes |
| michail\_initial\_password | Unique onboarding password for the Authentik michail user. | `string` | n/a | yes |
| opencode\_client\_id | OIDC client ID used by the Mac OpenCode oauth2-proxy. | `string` | `"opencode-mobile"` | no |
| opencode\_external\_url | Tailnet-only OpenCode URL routed through Atlas to Michail's Mac. | `string` | `"https://code.mbastakis.com"` | no |
| opencode\_oidc\_client\_secret | OIDC client secret shared by Authentik and the Mac OpenCode oauth2-proxy. | `string` | n/a | yes |
| pihole\_external\_url | External private URL for Pi-hole through Traefik and Authentik forward-auth. | `string` | `"https://pihole.mbastakis.com"` | no |
| sso\_session\_duration | Authentik user-login session duration for homeserver application auth flows. | `string` | `"days=7"` | no |
| taskboard\_external\_url | External private URL for Sisyphus through Traefik and Authentik forward-auth. | `string` | `"https://taskboard.mbastakis.com"` | no |
| traefik\_dashboard\_external\_url | External private URL for the Traefik dashboard through Traefik and Authentik forward-auth. | `string` | `"https://traefik.mbastakis.com"` | no |

## Outputs

| Name | Description |
| ---- | ----------- |
| audiobookshelf\_client\_id | OIDC client ID for Audiobookshelf. |
| audiobookshelf\_issuer\_url | OIDC issuer URL for Audiobookshelf. |
| audiobookshelf\_redirect\_uris | OIDC redirect URIs registered for Audiobookshelf web and mobile clients. |
| backrest\_launch\_url | Authentik-protected Backrest URL. |
| filebrowser\_quantum\_client\_id | OIDC client ID for FileBrowser Quantum. |
| filebrowser\_quantum\_issuer\_url | OIDC issuer URL for FileBrowser Quantum. |
| filebrowser\_quantum\_redirect\_uri | OIDC redirect URI registered for FileBrowser Quantum. |
| homeserver\_file\_groups | Authentik groups used by FileBrowser Quantum. |
| immich\_client\_id | OIDC client ID for Immich. |
| immich\_issuer\_url | OIDC issuer URL for Immich. |
| immich\_redirect\_uris | OIDC redirect URIs registered for Immich web and mobile clients. |
| opencode\_client\_id | OIDC client ID for the Mac OpenCode oauth2-proxy. |
| opencode\_group | Authentik group allowed to access the OpenCode mobile application. |
| opencode\_issuer\_url | OIDC issuer URL for the Mac OpenCode oauth2-proxy. |
| opencode\_redirect\_uri | OIDC redirect URI registered for the Mac OpenCode oauth2-proxy. |
| pihole\_launch\_url | Authentik-protected Pi-hole administration URL. |
| taskboard\_launch\_url | Authentik-protected Sisyphus URL. |
| traefik\_dashboard\_launch\_url | Authentik-protected Traefik dashboard URL. |
<!-- END_TF_DOCS -->
