from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
import yaml
from pydantic import ValidationError

from homeserver_iac.schema import INFRA_ROOT
from homeserver_iac.validation import (
    desired_state_files,
    format_validation_error,
    load_yaml,
    model_for_path,
    validate_desired_state,
)

FIXTURES = Path(__file__).parent / "fixtures"


def set_path(document: Any, path: list[str | int], value: Any) -> None:
    target = document
    for part in path[:-1]:
        target = target[part]
    target[path[-1]] = value


def test_all_desired_state_files_validate_without_live_apis() -> None:
    assert validate_desired_state() == desired_state_files()


@pytest.mark.parametrize("case", yaml.safe_load((FIXTURES / "invalid-cases.yaml").read_text()))
def test_invalid_fixtures_report_field_specific_errors(case: dict[str, Any]) -> None:
    path = INFRA_ROOT / case["file"]
    document = deepcopy(load_yaml(path))
    set_path(document, case["path"], case["value"])

    with pytest.raises(ValidationError) as caught:
        model_for_path(path).model_validate(document)

    safe_error = str(format_validation_error(path, caught.value))
    assert case["error"] in safe_error


def test_validation_error_omits_invalid_secret_value() -> None:
    path = INFRA_ROOT / "truenas/apps/declarations/backrest.yaml"
    document = deepcopy(load_yaml(path))
    document["values"]["admin_password"] = "super-sensitive-value"

    with pytest.raises(ValidationError) as caught:
        model_for_path(path).model_validate(document)

    safe_error = str(format_validation_error(path, caught.value))
    assert "values" in safe_error
    assert "super-sensitive-value" not in safe_error
