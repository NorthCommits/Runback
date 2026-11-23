import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Settings:
    database_url: str
    database_ssl: bool = False
    database_connect_timeout_seconds: float = 3.0

    @classmethod
    def from_environment(cls) -> "Settings":
        database_url = os.getenv(
            "RUNBACK_DATABASE_URL", "postgresql://runback:runback@localhost:5432/runback"
        )
        if not database_url.strip():
            raise ValueError("RUNBACK_DATABASE_URL must not be empty")
        return cls(
            database_url=database_url,
            database_ssl=parse_boolean(os.getenv("RUNBACK_DATABASE_SSL", "false")),
        )


def parse_boolean(value: str) -> bool:
    normalized_value = value.strip().lower()
    if normalized_value in {"1", "true", "yes"}:
        return True
    if normalized_value in {"0", "false", "no"}:
        return False
    raise ValueError("RUNBACK_DATABASE_SSL must be true or false")
