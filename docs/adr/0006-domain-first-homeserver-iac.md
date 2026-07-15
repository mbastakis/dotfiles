# Domain-First Homeserver IaC Operated Through Task

## Status

Accepted.

## Decision

Homeserver infrastructure remains source-only under `infra/`; chezmoi never deploys it into `$HOME`. Operations start from the workstation at the repository root and use Task as the public interface. Direct OpenTofu, Ansible, Python, and shell entrypoints are implementation details used by domain Taskfiles.

The final layout is domain-first: `aws`, `atlas`, `truenas`, `identity`, `network`, `sync`, and the cross-domain `secrets` and typed `homeserver_iac` package. Each managed domain exposes explicit read-only status/plan behavior and separately named apply behavior. `infra:validate` remains deterministic, secret-free, and live-service-free; `infra:status` aggregates live read-only domain checks and never applies changes.

OpenTofu state remains split by lifecycle and blast radius across six fixed S3 keys. Provider resources are preferred where they preserve required ownership and secret boundaries. Typed reconcilers cover concrete provider gaps, Ansible owns Atlas host convergence, and shell is limited to bootstrap and small command glue.

## Consequences

- Old `tf:<stack>:*`, `tailscale:*`, `syncthing:*`, and `*:legacy:*` compatibility commands are removed.
- Cross-stack OpenTofu quality commands such as `tf:validate`, `tf:tflint`, and `tf:state:baseline` remain because they are aggregate tooling, not deployment aliases.
- Desired-state and runtime-state boundaries are recorded in the ownership matrix.
- Secret values remain in BWS or provider memory; committed metadata records identity, ownership, consumers, generation, and rotation instructions.
- Applies remain deliberate and are never dependencies of validation or status tasks.
