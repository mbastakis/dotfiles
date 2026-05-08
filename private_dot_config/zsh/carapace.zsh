# Carapace completions - MUST be sourced AFTER compinit (needs compdef command)
# Cached for faster startup (regenerates when carapace/config/specs change)
# Enabled by default via ZSH_ENABLE_CARAPACE=1 in exports.zsh.
# To disable persistently, change that export before this file is sourced.
#
# Do not source `carapace _carapace zsh` globally: it replaces native Zsh
# completion for common commands like ls/aws/git and makes every TAB shell out
# through carapace. Load only the explicit completers listed below instead.

[[ "${ZSH_ENABLE_CARAPACE:-0}" == "1" ]] && command -v carapace &>/dev/null || return 0

_carapace_cache="$HOME/.cache/carapace-init.zsh"
_carapace_meta="$HOME/.cache/carapace-init.meta"
_carapace_tmp="$_carapace_cache.tmp"
_carapace_bin="$(command -v carapace)"
_carapace_rebuild=0
_carapace_tools=("${(@s: :)ZSH_CARAPACE_COMPLETERS}")

_carapace_state="bin=$_carapace_bin|bridges=${CARAPACE_BRIDGES:-}|tools=${ZSH_CARAPACE_COMPLETERS:-}"

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
  : >|"$_carapace_tmp"
  for _tool in "${_carapace_tools[@]}"; do
    [[ -n "$_tool" ]] || continue
    carapace "$_tool" zsh >>"$_carapace_tmp" 2>/dev/null
  done
  mv "$_carapace_tmp" "$_carapace_cache"
  print -r -- "$_carapace_state" >"$_carapace_meta"
fi

[[ -s "$_carapace_cache" ]] && source "$_carapace_cache"
autoload -Uz _myrepos 2>/dev/null
compdef _myrepos mr 2>/dev/null
unset _carapace_cache _carapace_meta _carapace_tmp _carapace_bin _carapace_state _carapace_rebuild _carapace_tools _tool _f
