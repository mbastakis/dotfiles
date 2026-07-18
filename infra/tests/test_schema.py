from homeserver_iac.schema import SCHEMA_MODELS, generate_schemas


def test_json_schemas_are_committed_and_current() -> None:
    assert len(SCHEMA_MODELS) == 10
    assert generate_schemas(check=True) == []
