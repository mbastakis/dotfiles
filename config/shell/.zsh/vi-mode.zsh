# # ZSH Vi Mode Configuration
# # Minimal vi-mode with only normal mode (vicmd) bindings

# # Enable vi mode
# bindkey -v

# # Reduce key timeout for better responsiveness (10ms)
# export KEYTIMEOUT=1

# # Change cursor shape for different vi modes
# function zle-keymap-select {
#   if [[ ${KEYMAP} == vicmd ]] ||
#      [[ $1 = 'block' ]]; then
#     echo -ne '\e[1 q'
#   elif [[ ${KEYMAP} == main ]] ||
#        [[ ${KEYMAP} == viins ]] ||
#        [[ ${KEYMAP} = '' ]] ||
#        [[ $1 = 'beam' ]]; then
#     echo -ne '\e[5 q'
#   fi
# }
# zle -N zle-keymap-select

# # Use beam shape cursor on startup
# echo -ne '\e[5 q'

# # Use beam shape cursor for each new prompt
# preexec() { echo -ne '\e[5 q' ;}

# # === VICMD (Normal Mode) Bindings Only ===

# # Better searching in vi command mode
# bindkey -M vicmd '/' history-incremental-search-backward
# bindkey -M vicmd '?' history-incremental-search-forward

# # Navigation in command mode
# bindkey -M vicmd '^A' beginning-of-line
# bindkey -M vicmd '^E' end-of-line

# # Word navigation with Ctrl+arrows in command mode
# bindkey -M vicmd '^[[1;5C' forward-word      # Ctrl+Right
# bindkey -M vicmd '^[[1;5D' backward-word     # Ctrl+Left
# # Alternative sequences for different terminals
# bindkey -M vicmd '\e[1;5C' forward-word      # Ctrl+Right
# bindkey -M vicmd '\e[1;5D' backward-word     # Ctrl+Left
# bindkey -M vicmd '^[OC' forward-word         # Ctrl+Right (some terminals)
# bindkey -M vicmd '^[OD' backward-word        # Ctrl+Left (some terminals)

# # Edit line in vim with v
# autoload -U edit-command-line
# zle -N edit-command-line
# bindkey -M vicmd v edit-command-line

# # Yank to system clipboard
# function vi-yank-clipboard {
#   zle vi-yank
#   echo -n "$CUTBUFFER" | pbcopy
# }
# zle -N vi-yank-clipboard
# bindkey -M vicmd 'y' vi-yank-clipboard

# # Enable text objects
# autoload -Uz select-bracketed select-quoted
# zle -N select-bracketed
# zle -N select-quoted
# for km in viopp visual; do
#   bindkey -M $km -- '-' vi-up-line-or-history
#   for c in {a,i}${(s..)^:-\'\"\`\|,./:;=+@}; do
#     bindkey -M $km $c select-quoted
#   done
#   for c in {a,i}${(s..)^:-'()[]{}<>bB'}; do
#     bindkey -M $km $c select-bracketed
#   done
# done

# # Add visual mode
# bindkey -M vicmd 'v' visual-mode
# bindkey -M vicmd 'V' visual-line-mode

# # Better undo/redo
# bindkey -M vicmd 'u' undo
# bindkey -M vicmd '^R' redo

# # Add surround functionality (simplified)
# autoload -Uz surround
# zle -N delete-surround surround
# zle -N add-surround surround
# zle -N change-surround surround
# bindkey -M vicmd cs change-surround
# bindkey -M vicmd ds delete-surround
# bindkey -M vicmd ys add-surround
# bindkey -M visual S add-surround
