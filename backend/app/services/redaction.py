import json
from dataclasses import dataclass
from typing import Any

REDACTED_VALUE = "[REDACTED]"


@dataclass(frozen=True, slots=True)
class RedactedPayload:
    content: Any
    redaction_summary: dict[str, Any]


def redact_payload(payload: Any, sensitive_keys: frozenset[str]) -> RedactedPayload:
    redacted_paths: list[str] = []

    def visit(value: Any, path: str) -> Any:
        if isinstance(value, dict):
            redacted_value: dict[str, Any] = {}
            for key, nested_value in value.items():
                nested_path = f"{path}.{key}" if path else key
                if key.lower() in sensitive_keys:
                    redacted_value[key] = REDACTED_VALUE
                    redacted_paths.append(nested_path)
                else:
                    redacted_value[key] = visit(nested_value, nested_path)
            return redacted_value
        if isinstance(value, list):
            return [visit(item, f"{path}[{index}]") for index, item in enumerate(value)]
        return value

    content = visit(payload, "")
    return RedactedPayload(
        content=content,
        redaction_summary={"redacted_fields": len(redacted_paths), "paths": redacted_paths},
    )


def payload_size_bytes(payload: Any) -> int:
    return len(json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode())
