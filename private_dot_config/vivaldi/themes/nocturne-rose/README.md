# Nocturne Rose — Vivaldi theme

Vivaldi imports themes as a zip archive, not from disk. To install or update:

```sh
cd ~/.config/vivaldi/themes/nocturne-rose
zip nocturne-rose.zip settings.json
```

Then in Vivaldi: Settings → Themes → Import Theme → pick `nocturne-rose.zip`.
Refresh after a palette release with `mise exec task -- task theme:sync`, then apply the updated files with chezmoi.

The `engineVersion` and `id` fields are required — Vivaldi silently ignores
imports without them. The id is fixed so re-imports update the same theme.
