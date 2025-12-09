#!/usr/bin/env zsh
# obsidian-cli.zsh - Obsidian CLI configuration

if command -v obsidian-cli &> /dev/null; then
  obsidian-cli set-default "my-notes" &> /dev/null
else
  echo "obsidian-cli is not installed. Please install it to use the obsidian command."
fi
