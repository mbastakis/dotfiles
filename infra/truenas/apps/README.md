# TrueNAS App Declarations

Catalog app declarations for storage-adjacent TrueNAS apps. These files are applied by a small API wrapper because the current provider can manage custom Compose apps but does not yet expose full catalog app install values.

## Target Apps

| App | Model | Notes |
|---|---|---|
| Syncthing | TrueNAS stable catalog app | Future Obsidian sync uses a dedicated dataset |
| File Browser | TrueNAS catalog app if suitable | Exposes selected host-path datasets |
| Restic backup runner | Catalog app if a real restic client/scheduler exists, otherwise scheduled CLI job | Uploads selected local datasets to S3 |

## Declaration Contract

Each declaration should include:

```yaml
app_name: syncthing
catalog_app: syncthing
train: stable
version: "1.3.10"
values: {}
```

Rules:

- `version` is pinned, even when it starts from the catalog's current latest version.
- `values` must not contain secrets.
- Durable user-owned data must use explicit host-path datasets from `pool_4tb`.
- App runtime data is never deleted automatically by the wrapper.
