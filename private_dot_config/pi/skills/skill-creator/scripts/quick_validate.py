#!/usr/bin/env python3
"""Quick validation script for Pi skills."""

import re
import sys
from pathlib import Path

try:
    import yaml  # type: ignore
except ImportError:  # Keep the quick validator usable without PyYAML.
    yaml = None


class FrontmatterError(ValueError):
    pass


def _finish_block(data: dict, key: str | None, marker: str | None, lines: list[str]) -> None:
    if key and marker in {"|", ">", "|-", ">-"}:
        sep = "\n" if marker.startswith("|") else " "
        data[key] = sep.join(lines).strip()


def parse_frontmatter(frontmatter_text: str) -> dict:
    """Parse the small frontmatter subset needed for validation.

    Prefer PyYAML when installed. The fallback handles top-level scalar fields
    plus block scalar descriptions, which covers normal Pi SKILL.md files.
    """
    if yaml is not None:
        try:
            parsed = yaml.safe_load(frontmatter_text)
        except yaml.YAMLError as e:  # type: ignore[attr-defined]
            raise FrontmatterError(f"Invalid YAML in frontmatter: {e}") from e
        if not isinstance(parsed, dict):
            raise FrontmatterError("Frontmatter must be a YAML dictionary")
        return parsed

    data: dict = {}
    block_key: str | None = None
    block_marker: str | None = None
    block_lines: list[str] = []

    for raw_line in frontmatter_text.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue

        if raw_line.startswith((" ", "\t")):
            if block_key:
                block_lines.append(raw_line.strip())
            continue

        _finish_block(data, block_key, block_marker, block_lines)
        block_key = None
        block_marker = None
        block_lines = []

        if ":" not in raw_line:
            raise FrontmatterError(f"Invalid frontmatter line: {raw_line}")

        key, raw_value = raw_line.split(":", 1)
        key = key.strip()
        value = raw_value.strip()
        if not key:
            raise FrontmatterError(f"Invalid empty frontmatter key in line: {raw_line}")

        if value in {"|", ">", "|-", ">-"}:
            data[key] = ""
            block_key = key
            block_marker = value
            block_lines = []
        elif value.lower() == "true":
            data[key] = True
        elif value.lower() == "false":
            data[key] = False
        elif (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
            data[key] = value[1:-1]
        else:
            data[key] = value

    _finish_block(data, block_key, block_marker, block_lines)
    return data


def validate_skill(skill_path):
    """Basic validation of a Pi skill."""
    skill_path = Path(skill_path)

    # Check SKILL.md exists
    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        return False, "SKILL.md not found"

    # Read and validate frontmatter
    content = skill_md.read_text()
    if not content.startswith("---"):
        return False, "No YAML frontmatter found"

    # Extract frontmatter
    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return False, "Invalid frontmatter format"

    frontmatter_text = match.group(1)

    # Parse YAML frontmatter
    try:
        frontmatter = parse_frontmatter(frontmatter_text)
    except FrontmatterError as e:
        return False, str(e)

    # Define Pi-supported frontmatter properties
    ALLOWED_PROPERTIES = {
        "name",
        "description",
        "license",
        "allowed-tools",
        "metadata",
        "compatibility",
        "disable-model-invocation",
    }

    warnings: list[str] = []

    # Check for unexpected properties (Pi ignores unknown fields, so warn only)
    unexpected_keys = set(frontmatter.keys()) - ALLOWED_PROPERTIES
    if unexpected_keys:
        warnings.append(
            f"Unexpected key(s) in SKILL.md frontmatter ignored by Pi: {', '.join(sorted(unexpected_keys))}. "
            f"Known properties are: {', '.join(sorted(ALLOWED_PROPERTIES))}"
        )

    # Check required fields
    if "name" not in frontmatter:
        return False, "Missing 'name' in frontmatter"
    if "description" not in frontmatter:
        return False, "Missing 'description' in frontmatter"

    # Extract name for validation
    name = frontmatter.get("name", "")
    if not isinstance(name, str):
        return False, f"Name must be a string, got {type(name).__name__}"
    name = name.strip()
    if name:
        # Check naming convention (kebab-case: lowercase with hyphens)
        if not re.match(r"^[a-z0-9-]+$", name):
            return False, f"Name '{name}' should be kebab-case (lowercase letters, digits, and hyphens only)"
        if name.startswith("-") or name.endswith("-") or "--" in name:
            return False, f"Name '{name}' cannot start/end with hyphen or contain consecutive hyphens"
        # Check name length (max 64 characters per spec)
        if len(name) > 64:
            return False, f"Name is too long ({len(name)} characters). Maximum is 64 characters."

    # Extract and validate description
    description = frontmatter.get("description", "")
    if not isinstance(description, str):
        return False, f"Description must be a string, got {type(description).__name__}"
    description = description.strip()
    if description:
        # Check for angle brackets
        if "<" in description or ">" in description:
            return False, "Description cannot contain angle brackets (< or >)"
        # Check description length (max 1024 characters per spec)
        if len(description) > 1024:
            return False, f"Description is too long ({len(description)} characters). Maximum is 1024 characters."

    # Validate compatibility field if present (optional)
    compatibility = frontmatter.get("compatibility", "")
    if compatibility:
        if not isinstance(compatibility, str):
            return False, f"Compatibility must be a string, got {type(compatibility).__name__}"
        if len(compatibility) > 500:
            return False, f"Compatibility is too long ({len(compatibility)} characters). Maximum is 500 characters."

    # Validate disable-model-invocation field if present (optional Pi field)
    if "disable-model-invocation" in frontmatter and not isinstance(frontmatter["disable-model-invocation"], bool):
        return False, "disable-model-invocation must be a boolean"

    if warnings:
        return True, "Skill is valid with warnings: " + " | ".join(warnings)
    return True, "Skill is valid!"


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python quick_validate.py <skill_directory>")
        sys.exit(1)

    valid, message = validate_skill(sys.argv[1])
    print(message)
    sys.exit(0 if valid else 1)
