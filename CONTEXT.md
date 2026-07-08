# Dotfiles Infrastructure Context

This context defines the language used for personal infrastructure managed from this dotfiles repository.

## Language

**atlas**:
A persistent personal server running on a home laptop that currently hosts stateful applications. Its data is valuable; its current application setup is not.
_Avoid_: disposable host, workstation, laptop profile

**Stateful application server**:
A server where application data must be preserved before configuration is changed, services are removed, or the host is rebuilt.
_Avoid_: disposable server, cattle host

**Application data**:
The persistent user-owned data produced or stored by applications on **atlas**. For the current atlas cleanup, this means only the **Actual Budget export** and **File Browser data**.
_Avoid_: app setup, current stack, Portainer configuration

**Actual Budget export**:
The restorable zip file exported from Actual Budget that contains `db.sqlite` and `metadata.json`. This is the preferred backup artifact for preserving the budget numbers from **atlas**.
_Avoid_: Actual setup, Actual container, Actual Docker volume

**Actual safety copy**:
A server-side copy of the Actual Budget data directory or Docker volume from **atlas**. It is insurance in addition to the **Actual Budget export**, not the canonical restore artifact.
_Avoid_: Actual setup, canonical Actual backup

**Atlas local backup**:
The local-machine backup directory for atlas cleanup artifacts, conventionally `~/Backups/atlas/YYYY-MM-DD/`. For the atlas cleanup it holds the Actual artifacts and manifest; large File Browser data may be recorded there but stored on TrueNAS.
_Avoid_: offsite backup, disaster-recovery backup

**TrueNAS atlas backup**:
The TrueNAS dataset used for large atlas backup artifacts that do not fit on the local machine. For the current atlas cleanup, it stores the File Browser data copied from atlas.
_Avoid_: local backup, app setup

**Backup checkpoint**:
The pause before any destructive atlas action where the Actual Budget export, Actual safety copy, File Browser data, and a manifest are present in their agreed backup locations and have been checked as non-empty. Formatting or reinstall work starts only after this checkpoint passes.
_Avoid_: best-effort copy, unverified backup

**File Browser data**:
The user file tree exposed through the File Browser service currently running on **atlas**. File Browser's internal database, users, settings, and application configuration are not backup targets.
_Avoid_: File Browser setup, File Browser container

**Discardable app setup**:
The current Portainer-managed applications, container definitions, images, and service configuration on **atlas**. These can be deleted after the scoped **application data** is backed up.
_Avoid_: data, backup target

**Automated setup**:
The future reproducible configuration for **atlas** after its **application data** has been preserved. It replaces the current hand-managed setup.
_Avoid_: manual cleanup, snowflake setup

**Fresh atlas installation**:
A clean-disk Ubuntu Server 26.04 LTS installation for **atlas** where previous packages, containers, services, data, and hand-managed configuration do not survive. An in-place Ubuntu release upgrade is not a fresh atlas installation.
_Avoid_: do-release-upgrade, in-place cleanup

**Physical USB installation**:
The accepted OS installation path for rebuilding **atlas**. Ubuntu Server is installed from physical USB media, then Ansible configures the already-installed server over SSH.
_Avoid_: SSH-first reinstall, remote autoinstall, bootstrap-managed OS install

**Ansible-owned configuration**:
The desired future state where atlas configuration after OS installation is applied from Ansible, not preserved from the existing server. Manual changes on atlas are temporary unless captured in Ansible.
_Avoid_: hand-managed server, snowflake configuration

**Source-only Ansible automation**:
The Ansible inventory, playbooks, roles, and helper scripts for personal servers live under `infra/ansible/` in this repository but are ignored by chezmoi so they are not deployed to `~/`. atlas is one managed host in that structure, not the whole automation namespace.
_Avoid_: deployed dotfiles, target home directory state

**Initial atlas configuration**:
The first Ansible-owned configuration applied after the fresh atlas installation. It provides base access, wired DHCP, laptop always-on power behavior, Docker CLI support, and terminal comfort; it does not declare or run applications yet.
_Avoid_: full homelab stack, Portainer replacement

**Atlas wired DHCP**:
The network policy where atlas gets its wired address through DHCP on the current wired interface, `enp3s0`. Static addressing and router reservations are separate decisions.
_Avoid_: static IP, unmanaged installer network state

**Atlas always-on power policy**:
The laptop-server policy where closing the lid or idling does not suspend, hibernate, sleep, or power off atlas.
_Avoid_: workstation laptop power saving

**Docker CLI support**:
The Docker client and related command-line access needed to inspect or operate containers later. It does not imply any containers, Compose projects, Portainer instance, or long-running application services are configured.
_Avoid_: Docker app stack, Portainer

**Atlas terminal comfort**:
The Ansible-managed interactive shell/editor layer for administering **atlas**. It installs Neovim, Zsh, Starship, and supporting CLI tools, deploys selected config from this repository, and avoids workstation-only Homebrew, secrets, and app integrations.
_Avoid_: full workstation dotfiles, chezmoi bootstrap, app stack

**No initial chezmoi on atlas**:
The first atlas setup does not run chezmoi on the server. Ansible may deploy selected Neovim, Zsh, and Starship configuration for server administration, but atlas does not receive the full personal dotfiles profile.
_Avoid_: full dotfiles install, workstation profile

**Atlas admin user**:
The normal sudo-capable user managed by Ansible for administering **atlas** over SSH. It uses authorized public keys from the local workstation; workstation private keys are not copied to atlas. After the first privileged Ansible run, this user has passwordless sudo so the account password is not stored in the repository.
_Avoid_: root SSH user, copied private key

**truenas**:
The TrueNAS SCALE homeserver used primarily as the durable storage appliance for files, backups, and storage-adjacent services. It may run a small set of minimal apps, but it is not the general-purpose application host.
_Avoid_: general Docker host, atlas replacement

**TrueNAS minimal apps**:
The intentionally small app set that belongs on **truenas** because it directly serves storage workflows. The current target set is Tailscale, Syncthing, FileBrowser Quantum, and Backrest.
_Avoid_: full homelab stack, arbitrary app hosting

**TrueNAS configuration as code**:
The desired state where repeatable TrueNAS settings are managed from this repository through API-backed infrastructure code and version-controlled workload files, with TrueNAS config backups kept as a recovery layer rather than the primary source of truth.
_Avoid_: UI-only management, ad hoc shell-only automation

**Code-first homeserver configuration**:
The operating rule that repeatable homeserver configuration should be owned by repository code, templates, or declarations whenever a stable automation path exists. A UI change is acceptable only as a discovery, bootstrap, or explicit exception path and should be captured back into code or documentation once understood.
_Avoid_: permanent click-only configuration, undocumented UI drift, code fighting unmanaged runtime state

**TrueNAS automation baseline**:
The minimum accepted TrueNAS SCALE version for new repository-managed automation is 25.04.2 or newer. The older 24.10 train is not the target for new Terraform/API/app configuration work.
_Avoid_: 24.10-first automation, archived API baseline

**TrueNAS Terraform state**:
The Terraform state for **TrueNAS configuration as code**. It lives in an external AWS S3 backend with locking and encryption, not in GitHub, not on **truenas**, and not as a committed file in this repository.
_Avoid_: committed tfstate, GitHub-backed state, NAS-hosted state

**Terraform state bootstrap**:
The documented one-time bootstrap script that creates the external Terraform state backend before repository-managed Terraform is initialized. The backend is foundational infrastructure, uses fixed repository-owned names, and is not managed by the same Terraform state it stores.
_Avoid_: undocumented manual setup, self-hosted bootstrap loop, state bucket managed by itself, caller-selected bucket name

**TrueNAS Terraform user**:
The dedicated automation identity used by Terraform to manage **truenas** through the supported middleware/API path. It authenticates with SSH key material that is not committed to this repository and is preferred over root/admin credentials.
_Avoid_: root automation, committed private key, shared personal login

**Terraform-owned TrueNAS configuration**:
The lower-blast-radius TrueNAS configuration that Terraform is allowed to manage: datasets, shares, snapshot tasks, backup/sync jobs, service users/groups, host-path app plumbing, and supported custom app declarations. Pool creation, disk layout, boot pool, network interfaces, update train selection, app runtime data, and one-time bootstrap actions are outside Terraform ownership unless a later decision explicitly moves them in.
_Avoid_: whole-appliance takeover, pool destruction automation, runtime data management

**TrueNAS catalog app**:
A maintained application from the TrueNAS Apps catalog, preferably from the stable train, configured through catalog app values rather than rewritten as a custom Compose stack. Syncthing should use this model when the catalog app meets the need.
_Avoid_: reinvented Compose stack, UI-only app setup

**TrueNAS app automation wrapper**:
A small source-controlled automation path that applies **TrueNAS catalog app** declarations through the TrueNAS API or `midclt` when Terraform provider support is not sufficient. It is a bridge to keep app configuration in code, not a replacement for Terraform-owned datasets, shares, users, permissions, snapshots, or backup jobs.
_Avoid_: manual catalog clicks, untracked UI values, provider-blocked app management

**TrueNAS app declaration**:
A repository-owned YAML file under `infra/truenas/apps/` that declares one catalog app installation: app name, catalog app identifier, train, version policy, and non-secret values. The **TrueNAS app automation wrapper** applies these declarations idempotently and never treats app runtime data as disposable.
_Avoid_: screenshots as config, undocumented UI forms, secret-bearing app YAML

**Pinned TrueNAS app version**:
The explicit catalog app version committed in a **TrueNAS app declaration**. New app declarations may start from the catalog's current latest version, but the committed declaration pins that version so later upgrades are deliberate repository changes.
_Avoid_: floating latest, silent app upgrade, unreviewed catalog drift

**TrueNAS app secret**:
A secret value needed to install or configure a **TrueNAS catalog app**. It is supplied at apply time from Bitwarden or environment variables and is never committed to app declarations, Terraform code, generated plans, or documentation.
_Avoid_: committed password, secret-bearing YAML, secret in README

**Homeserver secret source**:
Bitwarden Secrets Manager is the canonical source for homeserver deployment secrets. Repository files name which secrets are needed, while Ansible, Taskfile, or OpenTofu workflows fetch or inject values at apply time without committing them.
_Avoid_: committed `.env` files, hand-maintained server-only secrets, duplicating the same secret in multiple stores

**Homeserver secret alias**:
A stable repository-visible logical name for a Bitwarden Secrets Manager secret. The repository may commit aliases, human-readable path-style BWS names, BWS IDs, and intended environment-variable wiring, but never secret values. Automation resolves aliases by BWS ID so code stays readable without relying on mutable names at runtime.
_Avoid_: inline raw UUIDs throughout templates, resolving production secrets only by mutable display name, committing secret values, duplicating one secret under many aliases

**Homeserver secret helper**:
The source-controlled automation that resolves **Homeserver secret alias** entries and either injects secret values into a child command or renders restricted dotenv/config files for a target host. It should default to redacted/non-secret output and avoid printing raw secret values to stdout except as part of an explicit file-rendering or child-process execution mode.
_Avoid_: raw secret dumps in terminal logs, shell-history-friendly export snippets, committed `.env` or `.tfvars` files, one-off manual secret copying

**TrueNAS managed pool**:
The existing TrueNAS storage pool that repository-managed automation is allowed to configure through child datasets and related settings. The first managed pool is `pool_4tb`; Terraform does not create, destroy, or repartition it.
_Avoid_: Terraform-created pool, disk automation, boot pool

**TrueNAS dataset layout**:
The storage organization for **truenas**, split by lifecycle and backup policy. Human files, backup targets, and app config/data live in separate datasets so permissions, snapshots, and restore behavior can differ intentionally.
_Avoid_: single apps dump, mixed backup and file-share tree, app-owned user files

**TrueNAS app host-path storage**:
The preferred way for **TrueNAS minimal apps** to access durable data: catalog apps mount explicitly managed datasets from `pool_4tb` as host paths. File Browser and Syncthing should use dataset mounts rather than SMB/NFS loops or app-private storage for user-owned files.
_Avoid_: app-private user data, SMB-to-local-app path, hidden ixVolume-only storage

**No initial TrueNAS network shares**:
The first repository-managed TrueNAS setup does not create SMB or NFS shares by default. Network shares are added only when a real client or server workflow needs them.
_Avoid_: default SMB share, speculative NFS export, unused protocol surface

**Private homeserver access**:
The remote-access policy where homeserver services are reached from outside the home only after the client joins an authenticated private network. Public DNS names may exist for convenience, but storage and admin services are not treated as public internet services.
_Avoid_: public storage app exposure, internet-facing NAS admin, unauthenticated direct access

**No surprise public ingress**:
The router hardening posture where public inbound paths are explicit reviewed decisions. UPnP should be disabled after private Tailscale access works so LAN devices cannot silently create public port mappings.
_Avoid_: accidental UPnP port exposure, speculative port forwards, DMZ-style homeserver exposure

**Tailscale private access**:
The first private homeserver access implementation, where trusted personal devices join a Tailscale network before reaching homeserver services. It avoids requiring public router port forwards or dynamic DNS for the initial remote-access setup.
_Avoid_: public ingress, router-dependent VPN, DDNS-first remote access

**Tailscale access classes**:
The VPN authorization model that separates admin devices from app-user devices. Admin devices may reach infrastructure management surfaces such as TrueNAS administration, Syncthing administration, SSH, and selected LAN routes; app-user devices should reach only approved application entrypoints such as Traefik on **atlas** unless a specific sync workflow requires a narrow exception.
_Avoid_: flat tailnet access, shared VPN credentials, giving family or friends NAS/router/SSH reachability by default

**TrueNAS tailnet storage node**:
The network role where **truenas** joins the private Tailscale network directly for narrow storage-adjacent access such as Syncthing sync and administrator maintenance. It is not the general web entrypoint, exit node, or LAN subnet router for app users.
_Avoid_: truenas as general VPN gateway, app-user access to NAS administration, broad LAN routing through truenas

**TrueNAS Tailscale app**:
The TrueNAS catalog app used to give **truenas** its own tailnet identity while preserving the appliance model. It is preferred over manually installing Tailscale into the TrueNAS host OS.
_Avoid_: modifying the TrueNAS base OS, using truenas as an exit node, advertising broad LAN routes from truenas

**Homeserver tailnet server roles**:
The Tailscale authorization model where homeserver machines are identified by their function, such as private web entrypoint or storage node, so access rules grant capabilities to roles rather than to a flat list of devices.
_Avoid_: per-device ACL sprawl, flat LAN-style VPN access, giving household users storage-node reachability by default

**Per-person homeserver identity**:
The identity policy where each human has their own Tailscale identity and their own Authentik identity. VPN access, web app access, auditability, and revocation are managed per person rather than through shared household or guest credentials.
_Avoid_: shared VPN account, shared File Browser account, shared admin password, credential reuse for guests

**Filesystem-safe homeserver username**:
The stable short username used when an identity also maps to files or folders. It should be lowercase, durable, and safe as a directory name so per-person file areas can be tied to identity without later renaming.
_Avoid_: email address as folder name, display name as username, names with spaces or punctuation, renaming users casually

**Central homeserver identity**:
The shared login layer for private web applications, provided first by Authentik running on **atlas** behind **Tailscale private access**. It reduces per-application account sprawl for web apps, while non-web/device-based systems such as Syncthing still use their own device and folder trust model. Phase-1 web SSO sessions should favor household usability with a 7-day target where cleanly code-managed.
_Avoid_: per-app account sprawl for web apps, Authentik on truenas, treating Syncthing as SSO-capable, very short household web sessions without a concrete risk

**Authentik desired configuration**:
The intended Authentik objects that can be recreated from code, such as users, groups, applications, providers, bindings, and OIDC client settings. It is distinct from ongoing live credential state and should be managed declaratively after the identity service has been bootstrapped.
_Avoid_: hand-only app/provider setup, untracked group policy, confusing rebuildable configuration with user credential state

**Code-managed Authentik user**:
An Authentik user account created by the Authentik OpenTofu stack with a unique per-user BWS-generated and BWS-stored initial password plus code-owned group membership. The initial password is only an onboarding secret; after first login, the user's changed password and MFA enrollment are live identity state, not code-owned desired state. It is accepted that temporary initial passwords may appear in encrypted OpenTofu state for this tiny household setup.
_Avoid_: manually creating household users, shared default passwords, committing default passwords, reapplying the initial password after onboarding, managing MFA secrets in code, storing reusable long-lived human passwords in state

**Homeserver admin MFA**:
The phase-1 Authentik policy that the `michail` admin account must enroll and use TOTP MFA for admin access after changing the temporary onboarding password. Chara's file-only account must change its temporary password on first login, but MFA is optional unless a future app or risk model requires it. Passkeys/WebAuthn are future hardening, not a bootstrap dependency.
_Avoid_: password-only admin access, making Chara setup harder before there is a real need, storing MFA secrets or recovery codes in code, requiring WebAuthn before the basic stack is stable

**Authentik bootstrap boundary**:
The minimal setup needed to start Authentik and give automation a controlled way to manage it. It should create only the service runtime and seed credentials needed for declarative configuration, not become the place where app access policy is edited.
_Avoid_: managing ongoing app policy in bootstrap scripts, committing bootstrap secrets, confusing startup credentials with desired identity configuration

**Authentik automation token**:
The privileged API credential seeded during Authentik bootstrap and reused by the configuration stack for the first homeserver implementation. It is a secret automation credential, not a human login or desired policy object.
_Avoid_: committed API token, per-person use of the automation token, multiple overlapping automation tokens without a reason

**Authentik configuration stack**:
The ongoing infrastructure-as-code owner for **Authentik desired configuration** after bootstrap. It manages Authentik users, unique per-user initial passwords sourced from BWS, group membership, applications, providers, groups, and bindings while leaving changed passwords, MFA, sessions, and audit history inside Authentik live state.
_Avoid_: mixing bootstrap and ongoing app policy, shared onboarding passwords, multiple tools managing the same Authentik objects, treating OpenTofu state as an Authentik database backup, depending on initial passwords after onboarding

**Authentik live identity state**:
The runtime Authentik data that is not desirable or complete to manage as code, such as password hashes, MFA enrollments, recovery details, sessions, audit events, and user-driven account state. It may be acceptable to recreate manually for a tiny household, but it is the reason a database backup can still matter.
_Avoid_: committing passwords or MFA secrets, assuming configuration-as-code preserves enrolled authenticators, depending on audit/session history for disaster recovery

**Initial household files model**:
The first homeserver file access model where approved household users get a shared household area and separate per-person areas. Guest access is not part of the initial model and should be introduced only with explicit folder boundaries.
_Avoid_: friend access without a folder boundary, pretending all users need identical permissions, mixing private and shared household files

**File-only household user**:
A household identity whose homeserver access is limited to FileBrowser Quantum through the private web ingress, with access to the shared household file area and that user's own personal file area. Chara has this role in phase 1; Syncthing, Obsidian, Backrest, TrueNAS administration, and other infra surfaces remain Michail-only.
_Avoid_: accidental sync exceptions, household access to infra surfaces, mixing file sharing with Obsidian vault access, omitting a per-person privacy boundary for household users

**File-only guest access**:
The default future model for any friend/guest who is granted homeserver access at all: Tailscale plus Authentik plus FileBrowser Quantum to an explicit guest folder only. Guest access should be rare and does not include Syncthing, Obsidian, Backrest, TrueNAS administration, or other infra surfaces unless a separate explicit decision is made.
_Avoid_: casual broad friend access, guest access without a folder boundary, guest Syncthing device trust by default, exposing private household or Obsidian data to guests

**FileBrowser Quantum access**:
The selected private web file access application for the first shared drive, running on **truenas** against local datasets and using native OIDC with **Central homeserver identity**. It is preferred over original File Browser proxy-header authentication because Authentik becomes the delegated login provider rather than only an outer header-setting proxy. Phase-1 sessions should favor normal household usability with long-ish web sessions rather than frequent re-authentication.
_Avoid_: original File Browser as the first SSO target, blind proxy-header trust as the primary identity model, per-app File Browser passwords, making household file access brittle with overly short sessions

**FileBrowser Quantum desired configuration**:
The code-owned FileBrowser Quantum settings that define identity, source boundaries, default permissions, and externally visible URLs. Runtime database/index state may remain app-owned, but OIDC and source policy should be reproducible from repository templates plus secrets. Steady-state FileBrowser Quantum access is OIDC-only through Authentik; password auth is disabled unless temporarily enabled by a documented Michail-only break-glass procedure during an Authentik/OIDC outage. Any required local admin seed is a random BWS secret, unused during normal operation and rotated after break-glass use.
_Avoid_: UI-only SSO setup, hidden source mappings, password-auth fallback for normal users, relying on app runtime DB as the only copy of access policy, sharing break-glass credentials with household users, leaving password auth enabled in steady state

**FileBrowser scope privacy boundary**:
The phase-1 privacy model where FileBrowser Quantum source scopes keep household users inside their own personal folder while FileBrowser admin access is trusted to see all mounted file areas. Filesystem permissions protect the datasets from unrelated services and host users, not from FileBrowser Quantum itself.
_Avoid_: promising per-OIDC-user filesystem isolation before it exists, treating FileBrowser admin as unable to see user files, introducing complex ZFS/Unix ACL mapping before there is a concrete need

**Homeserver service placement**:
The boundary where storage-adjacent services run on **truenas** against local datasets, while access and identity services run on **atlas** as the private entry layer. It avoids making **truenas** the general access-control host and avoids serving NAS data through fragile network mounts on **atlas**.
_Avoid_: atlas-mounted NAS data as the app source of truth, truenas as the identity/control-plane host, splitting one storage workflow across unnecessary hosts

**Atlas homeserver app stack**:
The access and identity application layer on **atlas**, managed separately from base operating-system configuration. It is where private web ingress and central identity live, while user-owned NAS files remain on **truenas**.
_Avoid_: bundling all app decisions into base provisioning, putting identity on truenas, storing NAS user files on atlas

**Private Route53 service names**:
OpenTofu-managed public Route53 DNS records under `mbastakis.com` that resolve selected private homeserver service names to **atlas** on the Tailscale network. They provide stable friendly names for VPN-connected clients without creating public ingress; only intentional browser entrypoints get records, and direct TrueNAS/admin app names are not published.
_Avoid_: public app endpoints, router DDNS as the first access path, exposing truenas directly in public DNS, wildcard service records, manually edited DNS drift

**Private TLS automation**:
The certificate model where Traefik on **atlas** obtains and renews public Let's Encrypt certificates for private Tailscale-only service names using Route53 DNS-01 challenges. It provides normal browser trust without opening public HTTP/HTTPS ingress.
_Avoid_: self-signed household certs, public HTTP challenge exposure, wildcard certificates before they are needed, manual certificate renewal

**Private web app ingress**:
The Traefik reverse-proxy boundary on **atlas** for browser-based homeserver applications reached over **Tailscale private access** and protected by **Central homeserver identity** where the application supports it. It is the normal user path for web apps such as FileBrowser Quantum and future dashboards; direct TrueNAS app ports are reserved for administrator break-glass/debug use, not household access.
_Avoid_: proxying every protocol, family-facing Syncthing UI, bypassing the VPN boundary, teaching users internal NAS app ports

**Homeserver infra surface**:
An administrator/debug interface for operating the homeserver rather than a household application. TrueNAS UI, SSH, Syncthing UI, Backrest UI, direct FileBrowser Quantum port, and any future Traefik dashboard are infra surfaces restricted to homeserver admins across the tailnet; the home LAN is trusted in phase 1 and relies on credentials rather than network segmentation.
_Avoid_: Route53 records for admin UIs, household access to infrastructure ports, treating backup/sync/admin UIs as family apps, claiming VLAN-level isolation before it exists

**Trusted home LAN**:
The phase-1 network assumption that devices on the local home network are not isolated by VLAN/firewall policy. Tailscale ACLs provide remote/private-network isolation, while local LAN access relies on application credentials and no public internet exposure.
_Avoid_: assuming Tailscale ACLs restrict local Wi-Fi traffic, delaying phase 1 on VLAN design, giving guests permanent trusted LAN access without revisiting this assumption

**TrueNAS Obsidian dataset**:
The planned dedicated dataset for the Obsidian vault synced through Syncthing, separate from generic personal files so snapshot, sync, and restore behavior can be tuned independently. It may be declared before the vault contents are migrated, but the actual Obsidian data migration happens later.
_Avoid_: generic personal folder, immediate vault migration, SMB-based vault sync

**iOS Obsidian sync**:
The iPhone/iPad vault workflow where Obsidian reads a local vault folder and an iOS Syncthing-compatible client moves files in and out of that folder. Obsidian does not talk to Syncthing directly, and mobile sync is constrained by iOS background scheduling.
_Avoid_: Obsidian remote sync, direct Obsidian-Syncthing integration, assuming desktop-like always-on background sync

**Möbius Sync Pro**:
The accepted iOS Syncthing-compatible client for the first iOS Obsidian sync implementation. It can sync the Obsidian-accessible local vault folder, but because iOS controls background execution, it is a mostly-seamless sync layer rather than a guaranteed instant sync layer.
_Avoid_: official Syncthing for iOS, guaranteed real-time iOS sync, assuming opening Obsidian triggers Syncthing

**TrueNAS Obsidian sync peer**:
The Syncthing topology where **truenas** is the always-on durable peer for the Obsidian vault. Client devices sync with **truenas** over LAN or Tailscale rather than relying on another phone or workstation being online.
_Avoid_: atlas as Obsidian sync storage, phone-to-phone dependency, calling truenas the Syncthing master

**Obsidian send-receive sync folder**:
The Syncthing folder mode for the Obsidian vault where every trusted Obsidian device can both send and receive changes. It supports editing on desktop and mobile while relying on versioning, snapshots, and backups for recovery from conflicts or accidental edits.
_Avoid_: TrueNAS as Syncthing master, receive-only mobile sync, treating conflict-free multi-device editing as guaranteed

**Obsidian recovery layers**:
The combined protection for the synced Obsidian vault: Syncthing versioning for per-file recovery, ZFS snapshots for dataset rollback, and restic for off-NAS disaster recovery after the backup phase exists.
_Avoid_: treating Syncthing as backup, migrating the real vault before restore tests, relying on one recovery mechanism for all failure modes

**TrueNAS disaster-recovery backup**:
The off-NAS backup layer for important user-owned TrueNAS data, implemented first with restic to S3. It protects selected datasets from NAS loss and is separate from local ZFS snapshots; it is allowed to have a longer recovery point than local snapshots because it is for disaster recovery, not ordinary rollback.
_Avoid_: NAS-only backup, plain sync as backup, unencrypted cloud copy, treating off-NAS backup as the first rollback tool

**Weekly off-NAS recovery point**:
The accepted disaster-recovery target where S3/restic backups may be up to one week behind current TrueNAS data. Local ZFS snapshots and Syncthing versioning cover ordinary recent mistakes, while manual restic runs are used after major migrations or important uploads.
_Avoid_: pretending weekly offsite backup protects same-day changes, relying on S3 backup instead of local snapshots for quick rollback

**Atlas migration staging data**:
The temporary `pool_4tb/backups/atlas/...` data that carried files from the old atlas state into the new homeserver file area. Its FileBrowser payload was migrated into the household FileBrowser Quantum dataset and the old `pool_4tb/backups` staging datasets were deleted. Future migrations should remain explicitly temporary and include a cleanup plan.
_Avoid_: treating migration staging as disaster-recovery backup, keeping stale backup folders forever, building new architecture around temporary paths

**Initial TrueNAS backup scope**:
The first datasets that need off-NAS backup: Obsidian and personal/household files, sized for a practical low-cost S3 target under roughly $5/month with review around $10/month. App config datasets are not part of the initial off-NAS backup scope because the goal is to recreate app configuration from code; app runtime data can be added later only when it becomes user-owned or expensive to recreate. Large photo/media archives are future scope and should not be silently included in phase 1.
_Avoid_: backup everything blindly, backup code-recreatable state first, app cache backup, adding bulk photos without a new cost/scope decision

**TrueNAS backup runner**:
The automation that runs on **truenas** to back up selected local datasets directly to S3 with restic. It reads local dataset host paths and avoids requiring atlas or a workstation to mount TrueNAS data just to perform NAS backups.
_Avoid_: workstation-pulled NAS backup, atlas-mediated NAS backup, network-share-only backup path

**Backrest backup app**:
The preferred phase-1 **TrueNAS backup runner**: a TrueNAS catalog app that provides a managed UI and scheduler for restic backups. It keeps the restic backup format while avoiding a custom scheduler/container unless Backrest cannot cleanly support the required S3, secret, mount, or schedule model. Its desired repository and plan configuration should be code-owned where practical, while its UI remains an administrator surface.
_Avoid_: Duplicati as the first backup engine, Restic REST Server as an uploader, hand-written scheduler when the managed app fits, household access to backup administration, untracked backup policy changes

**TrueNAS restic client job**:
The fallback implementation for **TrueNAS backup runner** if **Backrest backup app** cannot satisfy the required S3, secret, read-only mount, or schedule behavior. It is a repository-managed scheduled restic CLI invocation on **truenas** with explicit retention and no committed secrets.
_Avoid_: Restic REST Server as S3 uploader, manual backup clicks, unversioned cron command

**TrueNAS backup S3 bucket**:
The dedicated AWS S3 bucket for restic disaster-recovery backups from **truenas**, separate from the Terraform state bucket and optimized for low storage cost. AWS access for provisioning and maintenance uses the `mbastakis` account through `aws-login`.
_Avoid_: shared Terraform state bucket, GitHub backup storage, same credentials as state by default

**Homeserver AWS account**:
The fixed AWS account used for homeserver S3 state and backup infrastructure. Repository workflows call `aws-login exec mbastakis --` directly instead of accepting an environment-selected AWS profile.
_Avoid_: profile override, accidental alternate AWS account, unreviewed account switch

**Readable restic cold storage**:
The cost-optimized S3 storage policy for the active restic repository. Objects must remain immediately readable for restic backup, check, prune, and restore operations; the first implementation uses S3 Glacier Instant Retrieval because off-NAS restores are rare but should not require asynchronous restore workflows. Phase-1 backup scope should target a practical low monthly cost rather than roomy bulk-archive storage.
_Avoid_: lifecycle-to-Deep-Archive, async restore requirement, frequent full repository reads, S3 lifecycle deletion of restic objects, treating the phase-1 repo as an unlimited photo archive

**Homeserver Terraform stack**:
A separately initialized Terraform root module under `infra/terraform/` with its own S3 state key. `bootstrap` manages the shared OpenTofu S3 backend bucket, `dns` manages the Route53 hosted zone and homeserver service records, `aws-foundation` manages AWS backup bucket/IAM, `truenas` manages supported TrueNAS configuration, and `authentik` manages Authentik desired configuration after the service is reachable. Separate states keep backend, DNS, AWS foundation, TrueNAS, and identity changes independently applicable.
_Avoid_: monolithic homeserver state, mixed DNS/AWS/NAS/identity blast radius, shared state key

**OpenTofu homeserver workflow**:
The canonical infrastructure-as-code command path for homeserver stacks in this repository. Repository tasks and docs use `tofu` commands; Terraform remains the ecosystem term for providers, state, and compatible module structure.
_Avoid_: Terraform CLI fallback, mixed tofu/terraform commands, hand-applied provider changes

**OpenTofu backend guard**:
The Taskfile preflight that verifies the fixed S3 state bucket exists through `aws-login exec mbastakis --` before remote homeserver stack initialization, planning, or applying. Plan/apply tasks re-run fixed-backend initialization with S3 native lockfiles first so local validation state or accidental alternate backend config is not reused silently. The bootstrap stack is created/adopted once with local state, then migrates its own state into the fixed backend.
_Avoid_: unverified backend, local state plan after migration, environment-selected backend, DynamoDB locking dependency

**Repo-local homeserver toolchain**:
The OpenTofu, TFLint, terraform-docs, pre-commit, and go-task tooling pinned by `mise.toml` for this repository. Homeserver infrastructure tasks use these repo-local tool versions instead of relying on globally installed Homebrew packages.
_Avoid_: global tool drift, unpinned IaC tools, Brewfile-owned homeserver tooling

**Single-page reading**:
The OpenCode workflow for reading, summarizing, or extracting markdown from one ordinary web page without creating persisted crawl artifacts. It should use defuddle-style extraction first and reach Crawl4AI only when browser-rendered JavaScript content defeats ordinary extraction.
_Avoid_: crawl pipeline, archival crawl, ai-docs artifact

**Crawl pipeline**:
A repeatable Crawl4AI workflow for multi-page crawling, browser-rendered JavaScript fallback, authenticated/session-based crawling with user authorization, structured repeated extraction, or persisted web data collection. It is not the default path for **single-page reading**.
_Avoid_: ordinary page summary, one-off article extraction, casual read

**Persisted crawl artifact**:
The saved output of an archival crawl, conventionally under `ai-docs/` when invoked through `/crawl` or `@crawl`. Explicit `/crawl <url>` requests a persisted crawl artifact even when the input is a single URL.
_Avoid_: chat-only summary, temporary extraction, unsaved page read

**Crawl boundary**:
The explicit scope that defines completeness for a **crawl pipeline**, such as URLs under a start path, a requested whole same-domain crawl, a supplied URL list, or an adaptive query boundary. Exhaustiveness means every reachable page inside this boundary is crawled, skipped with reason, or failed with reason; it does not mean unbounded whole-web crawling.
_Avoid_: absolute all pages, implicit whole domain, open-ended web crawl

## Example Dialogue

Dev: Should we remove the existing Portainer stack before applying the new setup?

Domain expert: No. atlas is a stateful application server, so application data must be preserved first. The current setup can be discarded after that.

Dev: Are we trying to keep Portainer exactly as-is?

Domain expert: No. We care about application data, not the current app setup.

Dev: Should we preserve every Docker volume before formatting atlas?

Domain expert: No. Only the Actual Budget export and File Browser data are backup targets; the rest of the app setup is discardable.

Dev: Is the Actual UI export enough before formatting atlas?

Domain expert: The UI export is the canonical backup, but take a server-side Actual safety copy as insurance.

Dev: Do we need cloud or external-disk redundancy before formatting atlas?

Domain expert: No. An atlas local backup is acceptable for this cleanup.

Dev: What if the File Browser data does not fit on the local machine?

Domain expert: Store the File Browser data in the TrueNAS atlas backup and record it in the local manifest.

Dev: Can we start reinstalling atlas as soon as one backup command finishes?

Domain expert: No. Stop at the backup checkpoint and confirm the scoped artifacts are present before any destructive action.

Dev: Can we use `do-release-upgrade` as the clean rebuild path?

Domain expert: No. A release upgrade preserves existing system state; atlas needs a fresh atlas installation followed by Ansible-owned configuration.

Dev: Can we keep the existing disk contents and just remove old services?

Domain expert: No. atlas should be rebuilt from a clean disk after the scoped backup is complete.

Dev: Should Ansible or bootstrap scripts install the operating system on atlas?

Domain expert: No. The OS is installed through physical USB media; Ansible only manages configuration after Ubuntu Server is installed and reachable.

Dev: Should the first Ansible pass start all the services atlas used to run?

Domain expert: No. The initial atlas configuration should provide base access, wired DHCP, always-on power behavior, Docker CLI support, and terminal comfort only; applications will be added step by step later.

Dev: Should atlas receive the personal dotfiles during the first setup?

Domain expert: No. Start with no initial chezmoi on atlas so Ansible remains the only configuration channel. Ansible can deploy a server-safe Neovim/Zsh/Starship subset without applying the full workstation profile.

Dev: Should atlas Ansible files be deployed to the home directory by chezmoi?

Domain expert: No. They are source-only Ansible automation in this repository, run through helper scripts when needed.

Dev: Should atlas receive the workstation's private SSH keys?

Domain expert: No. Ansible manages an atlas admin user with public-key SSH and sudo; private keys stay off atlas.

Dev: Should the repository store the atlas account password so Ansible can use sudo?

Domain expert: No. The first run can prompt for the password once, then Ansible configures passwordless sudo for the atlas admin user.
