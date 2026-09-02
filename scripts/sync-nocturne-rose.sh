#!/bin/sh
set -eu

repo_root=$(CDPATH="" cd -- "$(dirname -- "$0")/.." && pwd)
theme_root=${NOCTURNE_ROSE_ROOT:-"$repo_root/../../nocturne-rose/nocturne-rose_main"}
mode=${1:-sync}

if [ ! -d "$theme_root/dist" ]; then
  if [ "$mode" = "--check" ]; then
    printf '%s\n' "Nocturne Rose sibling checkout not present; skipping cross-repository snapshot check."
    exit 0
  fi
  printf '%s\n' "Nocturne Rose repository not found at $theme_root" >&2
  exit 1
fi

copy_or_check() {
  source=$1
  destination=$2
  if [ "$mode" = "--check" ]; then
    cmp -s "$source" "$destination" || {
      printf '%s\n' "stale Nocturne Rose snapshot: $destination" >&2
      return 1
    }
  else
    cp "$source" "$destination"
  fi
}

copy_or_check "$theme_root/dist/chezmoi/nocturne-rose.yaml" "$repo_root/.chezmoidata/nocturne-rose.yaml"
copy_or_check "$theme_root/dist/vivaldi/settings.json" "$repo_root/private_dot_config/vivaldi/themes/nocturne-rose/settings.json"

if [ "$mode" = "--check" ]; then
  unzip -p "$repo_root/private_dot_config/vivaldi/themes/nocturne-rose/nocturne-rose.zip" settings.json |
    cmp -s - "$repo_root/private_dot_config/vivaldi/themes/nocturne-rose/settings.json" || {
      printf '%s\n' "stale Vivaldi theme archive" >&2
      exit 1
    }
else
  (
    cd "$repo_root/private_dot_config/vivaldi/themes/nocturne-rose"
    rm -f nocturne-rose.zip
    zip -q nocturne-rose.zip settings.json
  )
fi
