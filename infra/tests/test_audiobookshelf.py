from __future__ import annotations

from typing import Any, cast

import homeserver_iac.audiobookshelf as audiobookshelf_module
from homeserver_iac.audiobookshelf import (
    AudiobookshelfClient,
    apply_audiobookshelf,
    desired_backup_payload,
    desired_library_payload,
    desired_openid_payload,
    desired_server_settings_payload,
    load_audiobookshelf_desired,
    plan_audiobookshelf,
)
from homeserver_iac.models.common import OperationKind, serialize_plan

ROOT_PASSWORD = "fixture-root-password"
OIDC_SECRET = "fixture-oidc-secret"


def discovery() -> dict[str, Any]:
    return {
        "issuer": "https://auth.mbastakis.com/application/o/audiobookshelf/",
        "authorization_endpoint": "https://auth.mbastakis.com/application/o/authorize/",
        "token_endpoint": "https://auth.mbastakis.com/application/o/token/",
        "userinfo_endpoint": "https://auth.mbastakis.com/application/o/userinfo/",
        "jwks_uri": "https://auth.mbastakis.com/application/o/audiobookshelf/jwks/",
        "end_session_endpoint": "https://auth.mbastakis.com/application/o/audiobookshelf/end-session/",
        "id_token_signing_alg_values_supported": ["RS256"],
    }


def current_state() -> dict[str, Any]:
    desired = load_audiobookshelf_desired()
    library = desired_library_payload(desired)
    return {
        "initialized": True,
        "token": "fixture-access-token",
        "libraries": [
            {
                "id": "library-runtime-id",
                "name": "Books",
                "mediaType": "book",
                "folders": [{"id": "folder-runtime-id", "path": "/books"}],
                "provider": library["provider"],
                "settings": library["settings"],
            }
        ],
        "server_settings": {
            **desired_server_settings_payload(desired),
            **desired_backup_payload(desired),
        },
        "auth_settings": desired_openid_payload(desired, discovery(), OIDC_SECRET),
    }


class FakeAudiobookshelfClient:
    def __init__(self) -> None:
        self.initialized = False
        self.libraries_state: list[dict[str, Any]] = []
        self.library_update_payload: dict[str, Any] | None = None
        self.server_settings: dict[str, Any] = {
            "backupSchedule": False,
            "backupsToKeep": 2,
            "maxBackupSize": 1,
            "sortingPrefixes": ["the", "a"],
        }
        self.auth_settings_state: dict[str, Any] = {"authActiveAuthMethods": ["local"]}

    def status(self) -> dict[str, Any]:
        return {"isInit": self.initialized}

    def initialize(self, username: str, password: str) -> None:
        assert username == "michail"
        assert password == ROOT_PASSWORD
        self.initialized = True

    def login(self, username: str, password: str) -> tuple[str, dict[str, Any]]:
        assert username == "michail"
        assert password == ROOT_PASSWORD
        return "fixture-access-token", {
            "user": {"accessToken": "fixture-access-token"},
            "serverSettings": dict(self.server_settings),
        }

    def libraries(self, token: str) -> list[dict[str, Any]]:
        assert token == "fixture-access-token"
        return self.libraries_state

    def auth_settings(self, token: str) -> dict[str, Any]:
        assert token == "fixture-access-token"
        return self.auth_settings_state

    def create_library(self, payload: dict[str, Any], token: str) -> None:
        self.libraries_state = [
            {
                "id": "library-runtime-id",
                "name": payload["name"],
                "mediaType": payload["mediaType"],
                "provider": payload["provider"],
                "settings": payload["settings"],
                "folders": [
                    {
                        "id": "folder-runtime-id",
                        "path": payload["folders"][0]["fullPath"],
                    }
                ],
            }
        ]

    def update_library(self, library_id: str, payload: dict[str, Any], token: str) -> None:
        assert library_id == "library-runtime-id"
        self.library_update_payload = payload
        self.libraries_state[0].update(payload)

    def update_settings(self, payload: dict[str, Any], token: str) -> None:
        self.server_settings.update(payload)

    def update_sorting_prefixes(self, prefixes: tuple[str, ...], token: str) -> None:
        self.server_settings["sortingPrefixes"] = list(prefixes)

    def update_auth_settings(self, payload: dict[str, Any], token: str) -> None:
        self.auth_settings_state.update(payload)


class PlainTextResponse:
    def __enter__(self) -> PlainTextResponse:
        return self

    def __exit__(self, *_args: Any) -> None:
        return None

    def read(self) -> bytes:
        return b"OK"


def test_desired_state_owns_supported_bootstrap_surface() -> None:
    desired = load_audiobookshelf_desired()

    assert desired.root_user.username == "michail"
    assert desired.library.folder == "/books"
    assert desired.backup.schedule == "0 2 * * 0"
    assert desired.backup.backups_to_keep == 8
    assert desired.library.settings.audiobooks_only is False
    assert desired.library.settings.cover_aspect_ratio == 0
    assert desired.server_settings.sorting_prefixes == ("the", "a", "an")
    assert desired.server_settings.allowed_origins == ()
    assert desired.openid.active_auth_methods == ("local", "openid")
    assert desired.openid.auto_launch is True
    assert desired.openid.group_claim == "audiobookshelf"


def test_uninitialized_plan_is_secret_safe() -> None:
    desired = load_audiobookshelf_desired()

    plan = plan_audiobookshelf(desired, {"initialized": False}, None, OIDC_SECRET)
    serialized = serialize_plan(plan)

    assert all(operation.kind is OperationKind.CREATE for operation in plan.operations)
    assert "audiobookshelf_root_password" in serialized
    assert "audiobookshelf_oidc_client_secret" in serialized
    assert ROOT_PASSWORD not in serialized
    assert OIDC_SECRET not in serialized


def test_client_accepts_successful_plain_text_response(monkeypatch: Any) -> None:
    monkeypatch.setattr(
        audiobookshelf_module.urllib.request,
        "urlopen",
        lambda request, timeout: PlainTextResponse(),
    )

    result = AudiobookshelfClient("http://audiobookshelf.test").request("POST", "/init", {})

    assert result == "OK"


def test_current_plan_is_clean() -> None:
    plan = plan_audiobookshelf(
        load_audiobookshelf_desired(), current_state(), discovery(), OIDC_SECRET
    )

    assert all(operation.kind is OperationKind.UNCHANGED for operation in plan.operations)


def test_apply_bootstraps_and_reconciles_supported_api_surface(monkeypatch: Any) -> None:
    client = FakeAudiobookshelfClient()
    monkeypatch.setattr(audiobookshelf_module, "discover_openid", lambda issuer: discovery())

    plan = apply_audiobookshelf(
        load_audiobookshelf_desired(),
        {"initialized": False},
        cast(AudiobookshelfClient, client),
        ROOT_PASSWORD,
        OIDC_SECRET,
    )

    assert plan.exit_code.value == 2
    assert client.initialized is True
    assert client.libraries_state[0]["folders"][0]["path"] == "/books"
    assert client.libraries_state[0]["settings"]["audiobooksOnly"] is False
    assert client.server_settings["backupsToKeep"] == 8
    assert client.server_settings["sortingIgnorePrefix"] is True
    assert client.server_settings["sortingPrefixes"] == ["the", "a", "an"]
    assert client.auth_settings_state["authOpenIDClientSecret"] == OIDC_SECRET
    assert client.auth_settings_state["authOpenIDAutoLaunch"] is True


def test_apply_updates_library_settings_without_replacing_folder(monkeypatch: Any) -> None:
    state = current_state()
    state["libraries"][0]["settings"]["coverAspectRatio"] = 1
    client = FakeAudiobookshelfClient()
    client.initialized = True
    client.libraries_state = state["libraries"]
    client.server_settings = state["server_settings"]
    client.auth_settings_state = state["auth_settings"]
    monkeypatch.setattr(audiobookshelf_module, "discover_openid", lambda issuer: discovery())

    apply_audiobookshelf(
        load_audiobookshelf_desired(),
        state,
        cast(AudiobookshelfClient, client),
        ROOT_PASSWORD,
        OIDC_SECRET,
    )

    assert client.library_update_payload is not None
    assert client.library_update_payload["settings"]["coverAspectRatio"] == 0
    assert "folders" not in client.library_update_payload
