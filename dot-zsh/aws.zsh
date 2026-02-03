# AWS profile switcher
# Wraps Go binary to enable env var export

# aws-login function - wraps the Go binary
# Usage: aws-login <profile> [mfa-code] [options]
aws-login() {
  local output
  output=$("$HOME/.bin/_aws-login" "$@")
  local exit_code=$?

  if [[ $exit_code -eq 0 && -n "$output" ]]; then
    eval "$output"
  fi

  return $exit_code
}
