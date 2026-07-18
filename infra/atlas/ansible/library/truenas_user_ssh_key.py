#!/usr/bin/python

from __future__ import annotations

import json
import subprocess
from typing import Any

from ansible.module_utils.basic import AnsibleModule

DOCUMENTATION = r"""
---
module: truenas_user_ssh_key
short_description: Ensure a public key is present on a TrueNAS local user
description:
  - Uses the supported local C(midclt) interface so the TrueNAS user database
    remains the source of truth for authorized SSH keys.
options:
  username:
    description: TrueNAS local username.
    required: true
    type: str
  public_key:
    description: OpenSSH public key to add without removing existing keys.
    required: true
    type: str
author:
  - Michail Bastakis
"""

EXAMPLES = r"""
- name: Authorize a backup key
  truenas_user_ssh_key:
    username: backup
    public_key: "ssh-ed25519 AAAA..."
"""

RETURN = r"""
changed:
  description: Whether the public key needed to be added.
  returned: always
  type: bool
"""


def midclt(module: AnsibleModule, method: str, *args: Any) -> Any:
    command = ["midclt", "call", method, *(json.dumps(arg) for arg in args)]
    result = subprocess.run(
        command,
        check=False,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        module.fail_json(
            msg=f"midclt {method} failed",
            stderr=result.stderr.strip(),
        )
    return json.loads(result.stdout) if result.stdout.strip() else None


def main() -> None:
    module = AnsibleModule(
        argument_spec={
            "username": {"type": "str", "required": True},
            "public_key": {"type": "str", "required": True, "no_log": False},
        },
        supports_check_mode=True,
    )

    username = module.params["username"]
    public_key = module.params["public_key"].strip()
    users = midclt(module, "user.query", [["username", "=", username]])
    if len(users) != 1:
        module.fail_json(msg=f"expected one TrueNAS user named {username}, found {len(users)}")

    user = users[0]
    existing = user.get("sshpubkey") or ""
    keys = [line.strip() for line in existing.splitlines() if line.strip()]
    if public_key in keys:
        module.exit_json(changed=False)

    if not module.check_mode:
        midclt(
            module,
            "user.update",
            user["id"],
            {"sshpubkey": "\n".join([*keys, public_key])},
        )
    module.exit_json(changed=True)


if __name__ == "__main__":
    main()
