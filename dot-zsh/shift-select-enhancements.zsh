# shift-select-enhancements.zsh - Custom enhancements for zsh-shift-select plugin
# Adds Shift+Cmd+arrow support and clipboard integration

# Copy selected region to clipboard (macOS)
function shift-select::copy-region() {
	if (( REGION_ACTIVE )); then
		local start end selected_text
		if [[ $MARK -lt $CURSOR ]]; then
			start=$((MARK + 1))
			end=$CURSOR
		else
			start=$((CURSOR + 1))
			end=$MARK
		fi
		selected_text="${BUFFER[$start,$end]}"
		
		# Copy to clipboard
		printf '%s' "$selected_text" | pbcopy
		
		# Also copy to zsh kill ring for compatibility
		CUTBUFFER="$selected_text"
	fi
	zle deactivate-region -w
	zle -K main
}
zle -N shift-select::copy-region

# Cut selected region to clipboard (macOS)
function shift-select::cut-region() {
	if (( REGION_ACTIVE )); then
		local start end selected_text
		if [[ $MARK -lt $CURSOR ]]; then
			start=$((MARK + 1))
			end=$CURSOR
		else
			start=$((CURSOR + 1))
			end=$MARK
		fi
		selected_text="${BUFFER[$start,$end]}"
		
		# Copy to clipboard
		printf '%s' "$selected_text" | pbcopy
		
		# Also copy to zsh kill ring for compatibility
		CUTBUFFER="$selected_text"
		
		# Remove the selected text
		zle kill-region -w
	fi
	zle -K main
}
zle -N shift-select::cut-region

# Select entire line
function shift-select::select-whole-line() {
	zle set-mark-command -w
	zle -K shift-select
	zle beginning-of-line -w
	zle set-mark-command -w
	zle end-of-line -w
}
zle -N shift-select::select-whole-line

# Enhanced shift-select setup with additional bindings
# This script is loaded via zinit's atload hook, so the plugin is already available

emulate -L zsh

# Bind custom CSI sequences (sent by Ghostty for Cmd+C/Cmd+X) to copy/cut in shift-select mode
bindkey -M shift-select '^[[200~' shift-select::copy-region    # Custom sequence for Cmd+C
bindkey -M shift-select '^[[201~' shift-select::cut-region     # Custom sequence for Cmd+X

# Also bind in emacs mode in case the sequence comes through there
bindkey -M emacs '^[[200~' shift-select::copy-region
bindkey -M emacs '^[[201~' shift-select::cut-region

# Bind Shift+Cmd+Left/Right to select whole line
bindkey -M emacs '^[[1;10D' shift-select::select-whole-line    # Shift + Cmd + LeftArrow
bindkey -M emacs '^[[1;10C' shift-select::select-whole-line    # Shift + Cmd + RightArrow
bindkey -M shift-select '^[[1;10D' shift-select::select-whole-line
bindkey -M shift-select '^[[1;10C' shift-select::select-whole-line
