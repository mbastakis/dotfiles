import os
import re
import sqlite3
import stat
import subprocess
import sys
from pathlib import Path

TEMPLATE = (
    Path(__file__).parents[1]
    / "atlas/ansible/roles/atlas_homeserver/templates/taskchampion-backup.sh.j2"
)
HOST_VARS = Path(__file__).parents[1] / "atlas/ansible/inventories/home/host_vars/atlas.yml"
HOMESERVER_TASKS = Path(__file__).parents[1] / "atlas/ansible/roles/atlas_homeserver/tasks/main.yml"


def write_executable(path: Path, content: str) -> None:
    path.write_text(content)
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


def render_script(tmp_path: Path) -> Path:
    root = tmp_path / "homeserver"
    source = root / "taskchampion-sync/data/taskchampion-sync-server.sqlite3"
    source.parent.mkdir(parents=True)
    script = TEMPLATE.read_text()
    replacements = {
        "{{ atlas_homeserver_root }}": str(root),
        "{{ atlas_homeserver_truenas_backup_host }}": "backup@truenas",
        "{{ atlas_homeserver_truenas_taskchampion_backup_path }}": "/safe/backups",
        "{{ atlas_admin_user }}": "atlas",
        'LOCK_FILE="/run/lock/taskchampion-backup.lock"': (
            f'LOCK_FILE="{tmp_path / "taskchampion-backup.lock"}"'
        ),
    }
    for old, new in replacements.items():
        script = script.replace(old, new)
    rendered = tmp_path / "taskchampion-backup.sh"
    write_executable(rendered, script)
    return rendered


def install_command_mocks(tmp_path: Path) -> tuple[Path, Path, Path]:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    log = tmp_path / "commands.log"
    captured = tmp_path / "uploaded.sqlite3"

    write_executable(
        bin_dir / "docker",
        """#!/bin/bash
set -euo pipefail
printf 'docker %s\n' "$*" >> "$COMMAND_LOG"
case " $* " in
    *" ps --status running --quiet taskchampion-sync "*) printf 'container-id\n' ;;
    *" stop --timeout 30 taskchampion-sync "*)
        [[ "${FAIL_STAGE:-}" != stop ]] || exit 42
        ;;
    *" start taskchampion-sync "*)
        [[ "${FAIL_STAGE:-}" != start ]] || exit 43
        ;;
esac
""",
    )
    write_executable(
        bin_dir / "runuser",
        """#!/bin/bash
set -euo pipefail
[[ "$1" == -u ]]
shift 2
[[ "$1" == -- ]]
shift
exec "$@"
""",
    )
    write_executable(
        bin_dir / "ssh",
        """#!/bin/bash
set -euo pipefail
printf 'ssh %s\n' "$*" >> "$COMMAND_LOG"
""",
    )
    write_executable(
        bin_dir / "rsync",
        """#!/bin/bash
set -euo pipefail
printf 'rsync %s\n' "$*" >> "$COMMAND_LOG"
[[ "${FAIL_STAGE:-}" != rsync ]] || exit 44
args=("$@")
cp "${args[${#args[@]}-2]}" "$CAPTURED_DB"
""",
    )
    write_executable(
        bin_dir / "chown",
        """#!/bin/bash
set -euo pipefail
printf 'chown %s\n' "$*" >> "$COMMAND_LOG"
""",
    )
    write_executable(
        bin_dir / "flock",
        """#!/bin/bash
set -euo pipefail
printf 'flock %s\n' "$*" >> "$COMMAND_LOG"
""",
    )
    write_executable(
        bin_dir / "python3",
        f"""#!/bin/bash
exec {sys.executable!r} "$@"
""",
    )
    return bin_dir, log, captured


def run_backup(tmp_path: Path, *, corrupt: bool = False, fail_stage: str = ""):
    script = render_script(tmp_path)
    source = tmp_path / "homeserver/taskchampion-sync/data/taskchampion-sync-server.sqlite3"
    if corrupt:
        source.write_bytes(b"not a sqlite database")
    else:
        with sqlite3.connect(source) as database:
            database.execute("CREATE TABLE tasks (id INTEGER PRIMARY KEY, description TEXT)")
            database.execute("INSERT INTO tasks (description) VALUES ('safe backup')")

    bin_dir, log, captured = install_command_mocks(tmp_path)
    env = os.environ | {
        "PATH": f"{bin_dir}:{os.environ['PATH']}",
        "COMMAND_LOG": str(log),
        "CAPTURED_DB": str(captured),
        "FAIL_STAGE": fail_stage,
    }
    result = subprocess.run([script], env=env, text=True, capture_output=True, check=False)
    return result, log.read_text().splitlines(), captured


def test_template_preserves_strict_ssh_and_serializes_locally() -> None:
    script = TEMPLATE.read_text()

    assert 'exec 9>"$LOCK_FILE"\nflock 9' in script
    assert "StrictHostKeyChecking=yes" in script
    assert "UpdateHostKeys=no" in script
    assert 'UserKnownHostsFile="$KNOWN_HOSTS"' in script
    assert 'stop --timeout 30 "$SERVICE"' in script
    assert "source.backup(backup)" in script
    assert "PRAGMA quick_check" in script


def test_inventory_pins_a_trusted_truenas_ed25519_host_key() -> None:
    host_vars = HOST_VARS.read_text()
    key = re.search(
        r"atlas_homeserver_truenas_backup_ssh_host_keys:\n  - (ssh-ed25519 [A-Za-z0-9+/]+={0,3})",
        host_vars,
    )

    assert key is not None


def test_homeserver_role_creates_the_shared_docker_network() -> None:
    tasks = HOMESERVER_TASKS.read_text()

    assert "community.docker.docker_network:\n    name: homeserver\n    state: present" in tasks
    assert "community.docker.docker_network_info:" not in tasks


def test_success_restarts_before_staged_publication_and_then_prunes(tmp_path: Path) -> None:
    result, commands, captured = run_backup(tmp_path)

    assert result.returncode == 0, result.stderr
    stop = next(i for i, command in enumerate(commands) if " stop " in command)
    start = next(i for i, command in enumerate(commands) if " start " in command)
    upload = next(i for i, command in enumerate(commands) if command.startswith("rsync "))
    publish = next(
        i for i, command in enumerate(commands) if "ssh " in command and "mv --" in command
    )
    prune = next(
        i for i, command in enumerate(commands) if "ssh " in command and "find " in command
    )
    assert stop < start < upload < publish < prune
    assert ".uploading." in commands[upload]
    assert "--protect-args" in commands[upload]
    with sqlite3.connect(captured) as database:
        assert database.execute("PRAGMA quick_check").fetchone() == ("ok",)
        assert database.execute("SELECT description FROM tasks").fetchone() == ("safe backup",)


def test_integrity_failure_restarts_without_network_transfer(tmp_path: Path) -> None:
    result, commands, captured = run_backup(tmp_path, corrupt=True)

    assert result.returncode != 0
    assert any(" stop " in command for command in commands)
    assert any(" start " in command for command in commands)
    assert not any(command.startswith(("ssh ", "rsync ")) for command in commands)
    assert not captured.exists()


def test_stop_failure_still_runs_restart_cleanup(tmp_path: Path) -> None:
    result, commands, _ = run_backup(tmp_path, fail_stage="stop")

    assert result.returncode != 0
    stop = next(i for i, command in enumerate(commands) if " stop " in command)
    start = next(i for i, command in enumerate(commands) if " start " in command)
    assert stop < start
    assert not any(command.startswith(("ssh ", "rsync ")) for command in commands)


def test_transfer_failure_cleans_remote_temp_without_pruning(tmp_path: Path) -> None:
    result, commands, _ = run_backup(tmp_path, fail_stage="rsync")

    assert result.returncode != 0
    start = next(i for i, command in enumerate(commands) if " start " in command)
    upload = next(i for i, command in enumerate(commands) if command.startswith("rsync "))
    assert start < upload
    assert any("rm -f --" in command and ".uploading." in command for command in commands)
    assert not any("mv --" in command or "find " in command for command in commands)
