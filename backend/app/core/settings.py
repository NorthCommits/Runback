import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Settings:
    database_url: str
    database_ssl: bool = False
    database_connect_timeout_seconds: float = 3.0
    ingest_max_body_bytes: int = 1_000_000
    ingest_max_payload_bytes: int = 65_536
    payload_storage_path: Path = Path("/var/lib/runback/payloads")
    ingest_redaction_keys: frozenset[str] = frozenset(
        {"api_key", "authorization", "cookie", "password", "secret", "set-cookie", "token"}
    )

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
            ingest_max_body_bytes=parse_positive_integer(
                os.getenv("RUNBACK_INGEST_MAX_BODY_BYTES", "1000000"),
                "RUNBACK_INGEST_MAX_BODY_BYTES",
            ),
            ingest_max_payload_bytes=parse_positive_integer(
                os.getenv("RUNBACK_INGEST_MAX_PAYLOAD_BYTES", "65536"),
                "RUNBACK_INGEST_MAX_PAYLOAD_BYTES",
            ),
            payload_storage_path=Path(
                os.getenv("RUNBACK_PAYLOAD_STORAGE_PATH", "/var/lib/runback/payloads")
            ),
            ingest_redaction_keys=parse_csv(
                os.getenv(
                    "RUNBACK_INGEST_REDACTION_KEYS",
                    "api_key,authorization,cookie,password,secret,set-cookie,token",
                )
            ),
        )


def parse_boolean(value: str) -> bool:
    normalized_value = value.strip().lower()
    if normalized_value in {"1", "true", "yes"}:
        return True
    if normalized_value in {"0", "false", "no"}:
        return False
    raise ValueError("RUNBACK_DATABASE_SSL must be true or false")


def parse_positive_integer(value: str, name: str) -> int:
    try:
        parsed_value = int(value)
    except ValueError as error:
        raise ValueError(f"{name} must be a positive integer") from error
    if parsed_value < 1:
        raise ValueError(f"{name} must be a positive integer")
    return parsed_value


def parse_csv(value: str) -> frozenset[str]:
    return frozenset(item.strip().lower() for item in value.split(",") if item.strip())
