from __future__ import annotations

import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).parents[2]
TMUX_SAVE = REPO_ROOT / "literal_bin/executable_tmux-save"


def normalize_snapshot(
    tmp_path: Path,
    *,
    name: str,
    sidebar_title: str,
    live_layout: str,
) -> str:
    snapshot = tmp_path / f"{name}.txt"
    sidebar_manifest = tmp_path / f"{name}.sidebars"
    sync_manifest = tmp_path / f"{name}.sessions"
    snapshot.write_text(
        "\n".join(
            (
                "\t".join(
                    (
                        "pane",
                        "work",
                        "1",
                        "1",
                        "*",
                        "1",
                        sidebar_title,
                        "/tmp",
                        "1",
                        "bash",
                        ":/bin/bash /tmp/opencode-session-sidebar",
                    )
                ),
                "\t".join(
                    (
                        "pane",
                        "work",
                        "1",
                        "1",
                        "*",
                        "2",
                        "OpenCode",
                        "/workspace",
                        "0",
                        "opencode",
                        ":/bin/bash /tmp/opencode-launch --continue",
                    )
                ),
                f"window\twork\t1\t1\t*\t2\t{live_layout}\t1\tapp",
                "state\twork\t1",
            )
        )
        + "\n"
    )
    sidebar_manifest.write_text(
        "work\t1\t1\t\t1\t0\trestored-layout\nwork\t1\t2\t1\t0\t1\trestored-layout\n"
    )
    sync_manifest.write_text("work/1/1\t7f9d-session\n")
    environment = {
        **os.environ,
        "HOME": str(tmp_path / "home"),
        "TMUX_SAVE_SIDEBAR_MANIFEST": str(sidebar_manifest),
        "TMUX_SAVE_SYNC_MANIFEST": str(sync_manifest),
    }

    result = subprocess.run(
        ("bash", str(TMUX_SAVE), "--normalize-snapshot", str(snapshot)),
        check=False,
        capture_output=True,
        text=True,
        env=environment,
    )

    assert result.returncode == 0, result.stderr
    return snapshot.read_text()


def save_snapshot_with_sidebar_topology(
    tmp_path: Path,
    *,
    name: str,
    app_panes: tuple[tuple[int, str, bool], ...],
    saved_topology: str,
    saved_layout: str = "pre-sidebar-layout",
) -> str:
    snapshot = tmp_path / f"{name}.txt"
    inventory = tmp_path / f"{name}.inventory"
    fake_bin = tmp_path / f"{name}-bin"
    fake_bin.mkdir()
    home = tmp_path / f"{name}-home"
    home.mkdir()

    pane_lines = [
        "\t".join(
            (
                "pane",
                "work",
                "1",
                "1",
                "*",
                str(index),
                pane_id,
                "/workspace",
                "1" if active else "0",
                "bash",
                f":/bin/bash /tmp/app-{pane_id.removeprefix('%')}",
            )
        )
        for index, pane_id, active in app_panes
    ]
    pane_lines.insert(
        0,
        "pane\twork\t1\t1\t*\t1\tsidebar\t/tmp\t0\tbash\t:/bin/bash /tmp/opencode-session-sidebar",
    )
    snapshot.write_text(
        "\n".join(
            (
                *pane_lines,
                "window\twork\t1\t1\t*\t2\tlive-sidebar-layout\t1\tapp",
                "state\twork\t1",
            )
        )
        + "\n"
    )

    inventory_lines = [
        f"@1\twork\t1\t1\t%sidebar\t1\t0\t{saved_layout}\t%previous\t{saved_topology}"
    ]
    inventory_lines.extend(
        f"@1\twork\t1\t{index}\t{pane_id}\t\t{'1' if active else '0'}\t"
        f"{saved_layout}\t%previous\t{saved_topology}"
        for index, pane_id, active in app_panes
    )
    inventory.write_text("\n".join(inventory_lines) + "\n")

    fake_tmux = fake_bin / "tmux"
    fake_tmux.write_text(
        """#!/bin/bash
set -euo pipefail
case "${1:-}" in
    wait-for) exit 0 ;;
    list-panes) command cat "$TMUX_TEST_INVENTORY" ;;
    show-option)
        [[ " $* " == *" pane-base-index "* ]] && printf '1\\n'
        ;;
esac
"""
    )
    fake_tmux.chmod(0o755)

    native_save = tmp_path / f"{name}-native-save"
    native_save.write_text(
        """#!/bin/bash
set -euo pipefail
bash "$TMUX_SAVE_UNDER_TEST" --normalize-snapshot "$TMUX_TEST_SNAPSHOT"
"""
    )
    native_save.chmod(0o755)

    result = subprocess.run(
        ("bash", str(TMUX_SAVE)),
        check=False,
        capture_output=True,
        text=True,
        env={
            **os.environ,
            "HOME": str(home),
            "PATH": f"{fake_bin}:{os.environ['PATH']}",
            "TMUX_RESURRECT_NATIVE_SAVE": str(native_save),
            "TMUX_SAVE_UNDER_TEST": str(TMUX_SAVE),
            "TMUX_TEST_INVENTORY": str(inventory),
            "TMUX_TEST_SNAPSHOT": str(snapshot),
        },
    )

    assert result.returncode == 0, result.stderr
    return snapshot.read_text()


def test_tmux_snapshot_normalization_precedes_native_deduplication(tmp_path: Path) -> None:
    first = normalize_snapshot(
        tmp_path,
        name="first",
        sidebar_title="sidebar refresh 1",
        live_layout="layout-with-sidebar-a",
    )
    second = normalize_snapshot(
        tmp_path,
        name="second",
        sidebar_title="sidebar refresh 2",
        live_layout="layout-with-sidebar-b",
    )

    assert first == second
    assert "sidebar" not in first
    assert "restored-layout" in first
    assert "\t1\tOpenCode\t/workspace\t1\topencode\t" in first
    assert "opencode-restore-session 7f9d-session" in first


def test_split_while_sidebar_is_open_uses_safe_canonical_layout(tmp_path: Path) -> None:
    snapshot = save_snapshot_with_sidebar_topology(
        tmp_path,
        name="split",
        app_panes=((2, "%10", False), (3, "%11", True), (4, "%12", False)),
        saved_topology="%10,%11",
    )

    assert "%sidebar" not in snapshot
    assert "opencode-session-sidebar" not in snapshot
    assert "pre-sidebar-layout" not in snapshot
    assert "\t1\t%10\t/workspace\t0\tbash\t" in snapshot
    assert "\t2\t%11\t/workspace\t1\tbash\t" in snapshot
    assert "\t3\t%12\t/workspace\t0\tbash\t" in snapshot
    assert "window\twork\t1\t1\t*\t2\ttiled\t1\tapp" in snapshot


def test_unchanged_application_topology_reuses_saved_layout(tmp_path: Path) -> None:
    snapshot = save_snapshot_with_sidebar_topology(
        tmp_path,
        name="unchanged",
        app_panes=((2, "%10", False), (3, "%11", True)),
        saved_topology="%10,%11",
    )

    assert "%sidebar" not in snapshot
    assert "opencode-session-sidebar" not in snapshot
    assert "window\twork\t1\t1\t*\t2\tpre-sidebar-layout\t1\tapp" in snapshot


def test_close_while_sidebar_is_open_uses_safe_canonical_layout(tmp_path: Path) -> None:
    snapshot = save_snapshot_with_sidebar_topology(
        tmp_path,
        name="close",
        app_panes=((2, "%10", True),),
        saved_topology="%10,%11",
    )

    assert "%sidebar" not in snapshot
    assert "opencode-session-sidebar" not in snapshot
    assert "pre-sidebar-layout" not in snapshot
    assert "\t1\t%10\t/workspace\t1\tbash\t" in snapshot
    assert "window\twork\t1\t1\t*\t2\ttiled\t1\tapp" in snapshot


def test_marked_sidebar_is_removed_without_a_saved_layout(tmp_path: Path) -> None:
    snapshot = save_snapshot_with_sidebar_topology(
        tmp_path,
        name="missing-layout",
        app_panes=((2, "%10", True),),
        saved_topology="%10",
        saved_layout="",
    )

    assert "%sidebar" not in snapshot
    assert "opencode-session-sidebar" not in snapshot
    assert "\t1\t%10\t/workspace\t1\tbash\t" in snapshot
    assert "window\twork\t1\t1\t*\t2\ttiled\t1\tapp" in snapshot
