import pytest

from app.core.settings import Settings


def test_settings_enable_ssl_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RUNBACK_DATABASE_URL", "postgresql://runback:password@example.com/runback")
    monkeypatch.setenv("RUNBACK_DATABASE_SSL", "true")

    settings = Settings.from_environment()

    assert settings.database_ssl is True


def test_settings_reject_invalid_ssl_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RUNBACK_DATABASE_SSL", "sometimes")

    with pytest.raises(ValueError, match="RUNBACK_DATABASE_SSL"):
        Settings.from_environment()
