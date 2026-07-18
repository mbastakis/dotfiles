import os
import re

MANAGED_TAGS = {"next", "waiting"}
TAG_RE = re.compile(r"^[A-Za-z0-9_.:-]+$")
PROJECT_RE = re.compile(r"^[A-Za-z0-9_.:-]+$")
DATE_RE = re.compile(r"^[A-Za-z0-9_.:/+-]+$")
MODIFIED_RE = re.compile(r"^\d{8}T\d{6}Z$")
UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)


def env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def require_uuid(value):
    if not UUID_RE.match(value):
        raise ValueError("invalid task uuid")
    return value.lower()


def clean_text(value, field, max_length=500):
    if value is None:
        return ""
    value = str(value).strip()
    if len(value) > max_length:
        raise ValueError(f"{field} is too long")
    return value


def clean_project(value):
    value = clean_text(value, "project", 120)
    if value and not PROJECT_RE.match(value):
        raise ValueError(
            "project may contain only letters, numbers, dot, colon, underscore, or dash"
        )
    return value


def clean_date(value, field):
    value = clean_text(value, field, 80)
    if value and not DATE_RE.match(value):
        raise ValueError(f"{field} contains invalid characters")
    return value


def clean_priority(value):
    value = clean_text(value, "priority", 1).upper()
    if value and value not in {"H", "M", "L"}:
        raise ValueError("priority must be H, M, L, or empty")
    return value


def clean_modified(value):
    value = clean_text(value, "expected_modified", 16)
    if not MODIFIED_RE.match(value):
        raise ValueError("expected_modified must be a Taskwarrior UTC timestamp")
    return value


def clean_tags(value):
    if value is None:
        return []
    if isinstance(value, str):
        raw_tags = re.split(r"[,\s]+", value.strip())
    elif isinstance(value, list):
        raw_tags = value
    else:
        raise ValueError("tags must be a list or comma-separated string")

    tags = []
    for raw_tag in raw_tags:
        tag = clean_text(raw_tag, "tag", 80)
        if not tag:
            continue
        if tag in MANAGED_TAGS:
            continue
        if not TAG_RE.match(tag):
            raise ValueError(
                "tags may contain only letters, numbers, dot, colon, underscore, or dash"
            )
        if tag not in tags:
            tags.append(tag)
    return tags


def clean_dependencies(value):
    if value is None:
        return []
    if isinstance(value, str):
        raw_dependencies = re.split(r"[,\s]+", value.strip())
    elif isinstance(value, list):
        raw_dependencies = value
    else:
        raise ValueError("dependencies must be a list or comma-separated string")

    dependencies = []
    for raw_dependency in raw_dependencies:
        dependency = clean_text(raw_dependency, "dependency", 36)
        if not dependency:
            continue
        dependency = require_uuid(dependency)
        if dependency not in dependencies:
            dependencies.append(dependency)
    return dependencies
