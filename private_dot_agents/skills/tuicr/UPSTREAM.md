# Upstream source

Vendored from https://github.com/agavra/tuicr/tree/2ff8e283538e93a7d1b7bc2b6540fb455c5a030b/skills/tuicr.

The skill and helper scripts retain their upstream contents. Chezmoi's
`executable_` source prefix makes the wrapper scripts executable when deployed.
`LICENSE` is copied from the upstream repository root.

To update, copy all files from `skills/tuicr/` at the desired upstream revision,
preserve the wrapper prefixes, update this revision, and preview and apply only
`~/.agents/skills/tuicr/` with chezmoi.
