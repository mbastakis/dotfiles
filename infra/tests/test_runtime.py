from __future__ import annotations

import pytest

from homeserver_iac import runtime
from homeserver_iac.runtime import OperationalError, run_json_command


def test_python_boolean_literals_require_explicit_compatibility(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(runtime, "run_command", lambda *args, **kwargs: "True\n")

    with pytest.raises(OperationalError):
        run_json_command(("command",), timeout=1)

    assert run_json_command(("command",), timeout=1, allow_python_literals=True) is True
