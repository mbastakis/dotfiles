# Nocturne Rose — Vivaldi theme

Vivaldi imports themes as a zip archive, not from disk. To install or update:

```sh
cd ~/.config/vivaldi/themes/nocturne-rose
zip nocturne-rose.zip settings.json
```

Then in Vivaldi: Settings → Themes → Import Theme → pick `nocturne-rose.zip`.
Regenerate after any palette change (`chezmoi apply` re-renders settings.json).

The `engineVersion` and `id` fields are required — Vivaldi silently ignores
imports without them. The id is fixed so re-imports update the same theme.
