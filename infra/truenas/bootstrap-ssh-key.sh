#!/bin/bash
set -euo pipefail

readonly DEFAULT_HOST="192.168.1.74"
readonly DEFAULT_USER="mbastakis"
readonly DEFAULT_PORT="22"
readonly DEFAULT_LOGIN_SHELL="/usr/bin/bash"
readonly DEFAULT_HOME_PARENT="/mnt/pool_4tb"

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd -- "$script_dir/../.." && pwd)"

if [[ -f "$repo_root/private_dot_ssh/id_ed25519.pub" ]]; then
    default_public_key_path="$repo_root/private_dot_ssh/id_ed25519.pub"
else
    default_public_key_path="$HOME/.ssh/id_ed25519.pub"
fi

host="$DEFAULT_HOST"
user="$DEFAULT_USER"
port="$DEFAULT_PORT"
public_key_path="$default_public_key_path"
private_key_path="$HOME/.ssh/id_ed25519"
login_shell="$DEFAULT_LOGIN_SHELL"
home_parent="$DEFAULT_HOME_PARENT"
skip_test=false

usage() {
    cat >&2 <<EOF
Usage: $0 [options]

Bootstraps key-based SSH access for a TrueNAS user through the TrueNAS CLI
login shell. The first connection may prompt for the current password-based
SSH login.

Options:
  --host HOST             TrueNAS host or IP (default: $DEFAULT_HOST)
  --user USER             TrueNAS user to update (default: $DEFAULT_USER)
  --port PORT             SSH port (default: $DEFAULT_PORT)
  --public-key PATH       Public key to install (default: $public_key_path)
  --private-key PATH      Private key for the post-bootstrap test (default: $private_key_path)
  --login-shell PATH      TrueNAS login shell to set for this user (default: $DEFAULT_LOGIN_SHELL)
  --home-parent PATH      Existing dataset path for TrueNAS to create the home under (default: $DEFAULT_HOME_PARENT)
  --skip-test             Do not run the key-based SSH test after updating
  -h, --help              Show this help
EOF
}

log_info() {
    printf '\033[0;34m[INFO]\033[0m %s\n' "$*" >&2
}

log_warning() {
    printf '\033[0;33m[WARN]\033[0m %s\n' "$*" >&2
}

log_error() {
    printf '\033[0;31m[ERROR]\033[0m %s\n' "$*" >&2
}

shell_quote() {
    local value="${1//\'/\'\\\'\'}"
    printf "'%s'" "$value"
}

cli_quote() {
    local value="${1//\\/\\\\}"
    value="${value//\"/\\\"}"
    printf '"%s"' "$value"
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --host)
            host="${2:-}"
            shift 2
            ;;
        --user)
            user="${2:-}"
            shift 2
            ;;
        --port)
            port="${2:-}"
            shift 2
            ;;
        --public-key)
            public_key_path="${2:-}"
            shift 2
            ;;
        --private-key)
            private_key_path="${2:-}"
            shift 2
            ;;
        --login-shell)
            login_shell="${2:-}"
            shift 2
            ;;
        --home-parent)
            home_parent="${2:-}"
            shift 2
            ;;
        --skip-test)
            skip_test=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            log_error "Unknown argument: $1"
            usage
            exit 2
            ;;
    esac
done

if ! command -v ssh &>/dev/null; then
    log_error "Missing required command: ssh"
    exit 1
fi

if [[ -z "$host" || -z "$user" || -z "$port" || -z "$login_shell" || -z "$home_parent" ]]; then
    log_error "Host, user, port, login shell, and home parent must not be empty."
    usage
    exit 2
fi

if [[ ! -f "$public_key_path" ]]; then
    log_error "Public key not found: $public_key_path"
    exit 1
fi

public_key="$(<"$public_key_path")"
public_key="${public_key//$'\r'/}"
public_key="${public_key//$'\n'/}"

if [[ -z "$public_key" ]]; then
    log_error "Public key is empty: $public_key_path"
    exit 1
fi

if [[ "$public_key" != ssh-* && "$public_key" != sk-* && "$public_key" != ecdsa-* ]]; then
    log_warning "Public key does not look like a standard OpenSSH public key. Continuing."
fi

ssh_target="$user@$host"
key_shell_works=false

key_shell_test_args=(
    -p "$port"
    -o "BatchMode=yes"
    -o "IdentitiesOnly=yes"
    -o "PreferredAuthentications=publickey"
)

if [[ -f "$private_key_path" ]]; then
    key_shell_test_args+=(
        -i "$private_key_path"
    )

    set +e
    key_shell_probe_output="$(ssh "${key_shell_test_args[@]}" "$ssh_target" "printf '%s\n' __TRUENAS_POSIX_SHELL_OK__" 2>&1)"
    key_shell_probe_rc=$?
    set -e

    if [[ "$key_shell_probe_rc" -eq 0 && "$key_shell_probe_output" == *"__TRUENAS_POSIX_SHELL_OK__"* ]]; then
        log_info "Key-based POSIX shell access already works for $ssh_target."
        key_shell_works=true
    fi
fi

ssh_bootstrap_args=(
    -p "$port"
    -o "PreferredAuthentications=password,keyboard-interactive,publickey"
    -o "NumberOfPasswordPrompts=3"
)

if [[ -f "$private_key_path" ]]; then
    ssh_bootstrap_args+=(
        -i "$private_key_path"
        -o "IdentitiesOnly=yes"
    )
fi

if [[ "$key_shell_works" != "true" ]]; then
    log_info "Installing public key for $ssh_target from $public_key_path"
    log_info "Setting TrueNAS login shell for $user to $login_shell"
    log_info "Setting TrueNAS home parent for $user to $home_parent"
    log_info "The SSH connection may prompt for the current TrueNAS password."

    cli_command="account user update uid_or_username=$(cli_quote "$user") home=$(cli_quote "$home_parent") home_create=true home_mode=$(cli_quote "700") sshpubkey=$(cli_quote "$public_key") shell=$(cli_quote "$login_shell")"

    # shellcheck disable=SC2087 # The generated CLI command is intentionally expanded locally.
    ssh -T "${ssh_bootstrap_args[@]}" "$ssh_target" <<EOF
$cli_command
exit
EOF
fi

if [[ ! -f "$private_key_path" ]]; then
    log_warning "Private key not found for middleware bootstrap: $private_key_path"
    log_warning "Run manually: ssh -o BatchMode=yes -i <private-key> $ssh_target true"
    exit 0
fi

log_info "Ensuring passwordless sudo is enabled for $user"

remote_user_env="TRUENAS_TARGET_USER=$(shell_quote "$user")"

# shellcheck disable=SC2029 # The quoted username assignment is intentionally expanded locally before SSH.
ssh "${key_shell_test_args[@]}" "$ssh_target" \
    "$remote_user_env python3 -" <<'PY'
import json
import os
import subprocess
import sys


def fail(message):
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(1)


def midclt(method, *args):
    cmd = ["midclt", "call", method]
    cmd.extend(json.dumps(arg) for arg in args)
    result = subprocess.run(
        cmd,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        fail(f"midclt {method} failed: {result.stderr.strip() or result.stdout.strip()}")
    if not result.stdout.strip():
        return None
    return json.loads(result.stdout)


username = os.environ["TRUENAS_TARGET_USER"]
users = midclt("user.query", [["username", "=", username]])
if not users:
    fail(f"TrueNAS user not found: {username}")
if len(users) != 1:
    fail(f"Expected one TrueNAS user named {username}, found {len(users)}")

user = users[0]
user_id = user.get("id")
if user_id is None:
    fail(f"TrueNAS user record for {username} did not include an id")

nopasswd = list(user.get("sudo_commands_nopasswd") or [])
if "ALL" in nopasswd:
    print(f"Passwordless sudo is already enabled for {username}.")
else:
    nopasswd.append("ALL")
    midclt("user.update", user_id, {"sudo_commands_nopasswd": nopasswd})
    print(f"Passwordless sudo enabled for {username}.")
PY

if [[ "$skip_test" == "true" ]]; then
    log_info "Skipping key-based SSH test."
    exit 0
fi

if [[ ! -f "$private_key_path" ]]; then
    log_warning "Private key not found for post-bootstrap test: $private_key_path"
    log_warning "Run manually: ssh -o BatchMode=yes -i <private-key> $ssh_target true"
    exit 0
fi

log_info "Testing key-based SSH with $private_key_path"
key_shell_test_output="$(ssh "${key_shell_test_args[@]}" "$ssh_target" "printf '%s\n' __TRUENAS_POSIX_SHELL_OK__" 2>&1)"

if [[ "$key_shell_test_output" != *"__TRUENAS_POSIX_SHELL_OK__"* ]]; then
    printf '%s\n' "$key_shell_test_output" >&2
    log_error "Key-based SSH did not reach a POSIX shell. Check the TrueNAS user shell and public key."
    exit 1
fi

log_info "Testing passwordless sudo"
ssh "${key_shell_test_args[@]}" "$ssh_target" "sudo -n true"

cat <<EOF

TrueNAS SSH key bootstrap complete.

Next checks:
  ssh truenas true
  mise exec -- task tf:truenas:plan
EOF
