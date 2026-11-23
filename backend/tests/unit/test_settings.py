import pytest

from app.core.settings import Settings, parse_csv, parse_positive_integer


def test_settings_enable_ssl_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RUNBACK_DATABASE_URL", "postgresql://runback:password@example.com/runback")
    monkeypatch.setenv("RUNBACK_DATABASE_SSL", "true")

    settings = Settings.from_environment()

    assert settings.database_ssl is True


def test_settings_reject_invalid_ssl_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RUNBACK_DATABASE_SSL", "sometimes")

    with pytest.raises(ValueError, match="RUNBACK_DATABASE_SSL"):
        Settings.from_environment()


def test_ingestion_settings_parsers_validate_input() -> None:
    assert parse_positive_integer("15", "RUNBACK_INGEST_MAX_BODY_BYTES") == 15
    assert parse_csv("Secret, token, secret") == frozenset({"secret", "token"})

    with pytest.raises(ValueError, match="positive integer"):
        parse_positive_integer("0", "RUNBACK_INGEST_MAX_BODY_BYTES")
