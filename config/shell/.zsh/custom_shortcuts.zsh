# # Yazi
# function run_y_command() {
#   BUFFER="y"
#   zle accept-line
# }
# zle -N run_y_command
# bindkey '^E' run_y_command

# # Lazygit
# function run_lazygit_command() {
#   BUFFER="lazygit"
#   zle accept-line
# }
# zle -N run_lazygit_command
# bindkey '^G' run_lazygit_command

# # k9s
# function run_k9s_command() {
#   BUFFER="k9s"
#   zle accept-line
# }
# zle -N run_k9s_command
# bindkey '^K' run_k9s_command

# Atuin search
function run_atuin_search_command() {
  BUFFER="atuin search -i"
  zle accept-line
}
zle -N run_atuin_search_command
bindkey '^S' run_atuin_search_command
