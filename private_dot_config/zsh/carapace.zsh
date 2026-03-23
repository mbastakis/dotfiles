# Carapace completions - MUST be sourced AFTER compinit (needs compdef command)
# Cached for faster startup (regenerates when carapace/config/specs change)
# Temporarily disabled by default for testing. Re-enable with:
#   ZSH_ENABLE_CARAPACE=1 exec zsh

[[ "${ZSH_ENABLE_CARAPACE:-0}" == "1" ]] && command -v carapace &>/dev/null || return 0

_carapace_cache="$HOME/.cache/carapace-init.zsh"
_carapace_meta="$HOME/.cache/carapace-init.meta"
_carapace_bin="$(command -v carapace)"
_carapace_rebuild=0

# Prefer native mr completion to avoid slower carapace fallback behavior.
if [[ ",${CARAPACE_EXCLUDES:-}," != *",mr,"* ]]; then
  export CARAPACE_EXCLUDES="${CARAPACE_EXCLUDES:+${CARAPACE_EXCLUDES},}mr"
fi

# Computed after CARAPACE_EXCLUDES mutation so the state reflects the final value.
_carapace_state="bin=$_carapace_bin|bridges=${CARAPACE_BRIDGES:-}|excludes=${CARAPACE_EXCLUDES:-}"

# Rebuild if cache is missing, empty, or binary changed
if [[ ! -f "$_carapace_cache" || ! -s "$_carapace_cache" || "$_carapace_bin" -nt "$_carapace_cache" ]]; then
  _carapace_rebuild=1
fi
# Rebuild if any config or spec file is newer than cache
for _f in "$HOME/.config/carapace/config.yaml" \
          "$HOME/.config/carapace/tools.yaml" \
          "$HOME"/.config/carapace/specs/*.yaml(N); do
  if [[ -f "$_f" && "$_f" -nt "$_carapace_cache" ]]; then
    _carapace_rebuild=1
    break
  fi
done
# Rebuild if state (bridges/excludes) changed
if [[ ! -f "$_carapace_meta" ]] || [[ "$_carapace_state" != "$(<"$_carapace_meta")" ]]; then
  _carapace_rebuild=1
fi

if (( _carapace_rebuild )); then
  mkdir -p "$HOME/.cache"
  carapace _carapace zsh >"$_carapace_cache" 2>/dev/null
  print -r -- "$_carapace_state" >"$_carapace_meta"
fi

source "$_carapace_cache"
autoload -Uz _myrepos 2>/dev/null
compdef _myrepos mr 2>/dev/null
unset _carapace_cache _carapace_meta _carapace_bin _carapace_state _carapace_rebuild _f
