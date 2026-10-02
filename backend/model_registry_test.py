from backend.model_registry import (
    DEFAULT_MODEL,
    get_model_catalog,
    validate_model,
)


def test_default_model_is_supported():
    assert DEFAULT_MODEL == "gemini-3.5-flash-lite"
    assert validate_model(None) == DEFAULT_MODEL


def test_catalog_contains_supported_models():
    ids = {item["id"] for item in get_model_catalog()}

    assert "gemini-3.5-flash-lite" in ids
    assert "gemini-3.5-flash" in ids


def test_invalid_model_is_rejected():
    try:
        validate_model("not-a-real-model")
    except ValueError as exc:
        assert "Unsupported model" in str(exc)
    else:
        raise AssertionError("Invalid model should be rejected")
