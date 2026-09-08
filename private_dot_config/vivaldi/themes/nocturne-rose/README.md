# Nocturne Rose — Vivaldi theme

Copy the ready-made `dist/vivaldi/settings.json` and `dist/vivaldi/nocturne-rose.zip`
from the Nocturne Rose theme repository into this source directory, then apply
those two managed targets with chezmoi.

In Vivaldi: Settings → Themes → Import Theme → pick
`~/.config/vivaldi/themes/nocturne-rose/nocturne-rose.zip`.

The `engineVersion` and `id` fields are required — Vivaldi silently ignores
imports without them. The id is fixed so re-imports update the same theme.
