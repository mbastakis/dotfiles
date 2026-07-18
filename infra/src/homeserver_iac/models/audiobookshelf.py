from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from homeserver_iac.models.common import (
    AbsolutePath,
    SecretRef,
    StableId,
    StrictModel,
    VersionedDesiredState,
)


class AudiobookshelfRootUser(StrictModel):
    username: StableId
    password: SecretRef


class AudiobookshelfLibrarySettings(StrictModel):
    cover_aspect_ratio: Literal[0, 1] = Field(alias="coverAspectRatio")
    disable_watcher: bool = Field(alias="disableWatcher")
    auto_scan_cron_expression: str | None = Field(alias="autoScanCronExpression")
    skip_matching_media_with_asin: bool = Field(alias="skipMatchingMediaWithAsin")
    skip_matching_media_with_isbn: bool = Field(alias="skipMatchingMediaWithIsbn")
    audiobooks_only: bool = Field(alias="audiobooksOnly")
    epubs_allow_scripted_content: bool = Field(alias="epubsAllowScriptedContent")
    hide_single_book_series: bool = Field(alias="hideSingleBookSeries")
    only_show_later_books_in_continue_series: bool = Field(
        alias="onlyShowLaterBooksInContinueSeries"
    )
    metadata_precedence: tuple[
        Literal[
            "folderStructure",
            "audioMetatags",
            "nfoFile",
            "txtFiles",
            "opfFile",
            "absMetadata",
        ],
        ...,
    ] = Field(alias="metadataPrecedence", min_length=6, max_length=6)
    mark_as_finished_percent_complete: int | None = Field(
        alias="markAsFinishedPercentComplete", ge=0, le=100
    )
    mark_as_finished_time_remaining: int | None = Field(alias="markAsFinishedTimeRemaining", ge=0)

    @model_validator(mode="after")
    def validate_metadata_precedence(self) -> AudiobookshelfLibrarySettings:
        if len(set(self.metadata_precedence)) != len(self.metadata_precedence):
            raise ValueError("metadataPrecedence must contain every source exactly once")
        return self


class AudiobookshelfLibrary(StrictModel):
    name: str = Field(min_length=1, max_length=128)
    media_type: Literal["book"] = Field(alias="mediaType")
    folder: AbsolutePath
    provider: StableId
    settings: AudiobookshelfLibrarySettings


class AudiobookshelfServerSettings(StrictModel):
    store_cover_with_item: bool = Field(alias="storeCoverWithItem")
    store_metadata_with_item: bool = Field(alias="storeMetadataWithItem")
    sorting_ignore_prefix: bool = Field(alias="sortingIgnorePrefix")
    sorting_prefixes: tuple[str, ...] = Field(alias="sortingPrefixes", min_length=1)
    scanner_parse_subtitle: bool = Field(alias="scannerParseSubtitle")
    scanner_find_covers: bool = Field(alias="scannerFindCovers")
    scanner_cover_provider: StableId = Field(alias="scannerCoverProvider")
    scanner_prefer_matched_metadata: bool = Field(alias="scannerPreferMatchedMetadata")
    scanner_disable_watcher: bool = Field(alias="scannerDisableWatcher")
    chromecast_enabled: bool = Field(alias="chromecastEnabled")
    allow_iframe: bool = Field(alias="allowIframe")
    home_bookshelf_view: Literal[0, 1] = Field(alias="homeBookshelfView")
    bookshelf_view: Literal[0, 1] = Field(alias="bookshelfView")
    date_format: str = Field(alias="dateFormat", min_length=1, max_length=32)
    time_format: str = Field(alias="timeFormat", min_length=1, max_length=32)
    language: StableId
    allowed_origins: tuple[str, ...] = Field(alias="allowedOrigins")

    @model_validator(mode="after")
    def validate_lists(self) -> AudiobookshelfServerSettings:
        normalized_prefixes = tuple(prefix.strip().lower() for prefix in self.sorting_prefixes)
        if any(not prefix for prefix in normalized_prefixes):
            raise ValueError("sortingPrefixes must not contain empty values")
        if normalized_prefixes != self.sorting_prefixes:
            raise ValueError("sortingPrefixes must be trimmed and lowercase")
        if len(set(self.sorting_prefixes)) != len(self.sorting_prefixes):
            raise ValueError("sortingPrefixes must be unique")
        if len(set(self.allowed_origins)) != len(self.allowed_origins):
            raise ValueError("allowedOrigins must be unique")
        if any(not origin.startswith(("http://", "https://")) for origin in self.allowed_origins):
            raise ValueError("allowedOrigins entries must be HTTP origins")
        return self


class AudiobookshelfBackupPolicy(StrictModel):
    schedule: str = Field(min_length=1)
    backups_to_keep: int = Field(alias="backupsToKeep", ge=1, le=100)
    max_backup_size: int = Field(alias="maxBackupSize", ge=0)


class AudiobookshelfOpenID(StrictModel):
    issuer_url: str = Field(alias="issuerUrl", pattern=r"^https://")
    client_id: StableId = Field(alias="clientId")
    client_secret: SecretRef = Field(alias="clientSecret")
    signing_algorithm: Literal["RS256"] = Field(alias="signingAlgorithm")
    button_text: str = Field(alias="buttonText", min_length=1, max_length=128)
    auto_launch: bool = Field(alias="autoLaunch")
    auto_register: bool = Field(alias="autoRegister")
    match_existing_by: Literal["username", "email"] = Field(alias="matchExistingBy")
    mobile_redirect_uris: tuple[str, ...] = Field(alias="mobileRedirectUris", min_length=1)
    group_claim: StableId = Field(alias="groupClaim")
    redirect_subfolder: AbsolutePath = Field(alias="redirectSubfolder")
    active_auth_methods: tuple[Literal["local", "openid"], ...] = Field(
        alias="activeAuthMethods", min_length=1
    )

    @model_validator(mode="after")
    def validate_auth_methods(self) -> AudiobookshelfOpenID:
        if len(self.active_auth_methods) != len(set(self.active_auth_methods)):
            raise ValueError("activeAuthMethods must be unique")
        if "openid" not in self.active_auth_methods:
            raise ValueError("activeAuthMethods must include openid")
        return self


class AudiobookshelfDesiredState(VersionedDesiredState):
    api_url: str = Field(alias="apiUrl", pattern=r"^https?://")
    root_user: AudiobookshelfRootUser = Field(alias="rootUser")
    library: AudiobookshelfLibrary
    server_settings: AudiobookshelfServerSettings = Field(alias="serverSettings")
    backup: AudiobookshelfBackupPolicy
    openid: AudiobookshelfOpenID

    @model_validator(mode="after")
    def validate_contract(self) -> AudiobookshelfDesiredState:
        if self.ownership.scope != "truenas.audiobookshelf_config":
            raise ValueError("ownership.scope must be 'truenas.audiobookshelf_config'")
        return self
