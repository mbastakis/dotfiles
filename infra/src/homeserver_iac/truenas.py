from __future__ import annotations

import json
import os
import shlex
import stat
import tempfile
from pathlib import Path
from typing import Any

from homeserver_iac.runtime import run_json_command


class MidcltClient:
    def __init__(
        self,
        host: str = "truenas",
        *,
        connect_timeout: int = 10,
        command_timeout: float = 60.0,
        port: int | None = None,
        identity: str | None = None,
    ) -> None:
        self.host = host
        self.connect_timeout = connect_timeout
        self.command_timeout = command_timeout
        self.port = port
        self.identity = identity

    def call(self, method: str, *arguments: Any, job: bool = False) -> Any:
        remote = ["sudo", "midclt", "call"]
        if job:
            remote.append("-j")
        remote.append(method)
        remote.extend(json.dumps(argument, separators=(",", ":")) for argument in arguments)
        remote_command = shlex.join(remote)
        identity_path: str | None = None
        try:
            command = ["ssh", "-n", "-o", f"ConnectTimeout={self.connect_timeout}"]
            if self.port is not None:
                command.extend(("-p", str(self.port)))
            if self.identity is not None:
                descriptor, identity_path = tempfile.mkstemp()
                os.fchmod(descriptor, stat.S_IRUSR | stat.S_IWUSR)
                with os.fdopen(descriptor, "w") as stream:
                    stream.write(self.identity)
                    if not self.identity.endswith("\n"):
                        stream.write("\n")
                command.extend(
                    (
                        "-i",
                        identity_path,
                        "-o",
                        "BatchMode=yes",
                        "-o",
                        "StrictHostKeyChecking=yes",
                        "-o",
                        "UpdateHostKeys=no",
                    )
                )
            command.extend((self.host, remote_command))
            return run_json_command(
                tuple(command),
                timeout=self.command_timeout,
                allow_python_literals=True,
            )
        finally:
            if identity_path is not None:
                Path(identity_path).unlink(missing_ok=True)
