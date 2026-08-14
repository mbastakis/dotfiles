# Dotfiles Context

This repository owns durable user- and machine-wide configuration for the local
workstation through chezmoi.

## Ownership Boundary

**Persistent workstation configuration**:
Configuration that is installed, rendered, or executed on this machine. This
includes local shells, editors, applications, LaunchAgents, SSH clients,
credentials, route selectors, and clients for remote services.

**External infrastructure**:
Configuration that declares, deploys, reconciles, tests, or documents machines
and services outside this workstation. It belongs in the sibling Kavouki
repository, including Atlas, TrueNAS, OpenWrt, AWS, Authentik, Tailscale policy,
remote Syncthing, backups, DNS, and homeserver workloads.

Remote hostnames and service URLs may appear here when they configure a local
client. That does not transfer ownership of the remote service into dotfiles.
