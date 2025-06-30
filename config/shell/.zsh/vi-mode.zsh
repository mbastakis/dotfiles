# ZSH Vi Mode Configuration
# Enhanced vi-like command line editing

# Enable vi mode
bindkey -v

# Reduce key timeout for better responsiveness (10ms)
export KEYTIMEOUT=1

# Change cursor shape for different vi modes
function zle-keymap-select {
  if [[ ${KEYMAP} == vicmd ]] ||
     [[ $1 = 'block' ]]; then
    echo -ne '\e[1 q'
  elif [[ ${KEYMAP} == main ]] ||
       [[ ${KEYMAP} == viins ]] ||
       [[ ${KEYMAP} = '' ]] ||
       [[ $1 = 'beam' ]]; then
    echo -ne '\e[5 q'
  fi
}
zle -N zle-keymap-select

# Use beam shape cursor on startup
echo -ne '\e[5 q'

# Use beam shape cursor for each new prompt
preexec() { echo -ne '\e[5 q' ;}

# Better searching in vi mode
bindkey -M vicmd '/' history-incremental-search-backward
bindkey -M vicmd '?' history-incremental-search-forward

# Allow backspace in vi insert mode
bindkey -M viins '^?' backward-delete-char

# Allow ctrl-h, ctrl-w, ctrl-u in vi insert mode
bindkey -M viins '^H' backward-delete-char
bindkey -M viins '^W' backward-kill-word
bindkey -M viins '^U' backward-kill-line

# Better navigation
bindkey -M viins '^A' beginning-of-line
bindkey -M viins '^E' end-of-line

# Edit line in vim with ctrl-e (in normal mode press v)
autoload -U edit-command-line
zle -N edit-command-line
bindkey -M vicmd v edit-command-line

# Quick escape with jj or jk
bindkey -M viins 'jj' vi-cmd-mode
bindkey -M viins 'jk' vi-cmd-mode

# Yank to system clipboard
function vi-yank-clipboard {
  zle vi-yank
  echo -n "$CUTBUFFER" | pbcopy
}
zle -N vi-yank-clipboard
bindkey -M vicmd 'y' vi-yank-clipboard

# Enable text objects
autoload -Uz select-bracketed select-quoted
zle -N select-bracketed
zle -N select-quoted
for km in viopp visual; do
  bindkey -M $km -- '-' vi-up-line-or-history
  for c in {a,i}${(s..)^:-\'\"\`\|,./:;=+@}; do
    bindkey -M $km $c select-quoted
  done
  for c in {a,i}${(s..)^:-'()[]{}<>bB'}; do
    bindkey -M $km $c select-bracketed
  done
done

# Add visual mode
bindkey -M vicmd 'v' visual-mode
bindkey -M vicmd 'V' visual-line-mode

# Better undo/redo
bindkey -M vicmd 'u' undo
bindkey -M vicmd '^R' redo

# Add surround functionality (simplified)
autoload -Uz surround
zle -N delete-surround surround
zle -N add-surround surround
zle -N change-surround surround
bindkey -M vicmd cs change-surround
bindkey -M vicmd ds delete-surround
bindkey -M vicmd ys add-surround
bindkey -M visual S add-surround