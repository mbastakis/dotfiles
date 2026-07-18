from __future__ import annotations

from pathlib import Path
from typing import Any

from homeserver_iac import truenas


def test_ephemeral_identity_still_requires_pinned_host_trust(monkeypatch: Any) -> None:
    observed: list[str] = []

    def run(command: tuple[str, ...], **_: Any) -> dict[str, Any]:
        observed.extend(command)
        return {}

    monkeypatch.setattr(truenas, "run_json_command", run)
    truenas.MidcltClient("truenas", identity="private-client-key").call("system.info")

    assert "StrictHostKeyChecking=yes" in observed
    assert "UpdateHostKeys=no" in observed
    assert "StrictHostKeyChecking=accept-new" not in observed
    identity_path = Path(observed[observed.index("-i") + 1])
    assert not identity_path.exists()
