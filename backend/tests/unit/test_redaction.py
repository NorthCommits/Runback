from app.services.redaction import REDACTED_VALUE, payload_size_bytes, redact_payload


def test_redaction_removes_sensitive_values_before_persistence() -> None:
    result = redact_payload(
        {"Authorization": "Bearer secret", "nested": [{"password": "hunter2"}]},
        frozenset({"authorization", "password"}),
    )

    assert result.content == {
        "Authorization": REDACTED_VALUE,
        "nested": [{"password": REDACTED_VALUE}],
    }
    assert result.redaction_summary == {
        "redacted_fields": 2,
        "paths": ["Authorization", "nested[0].password"],
    }


def test_payload_size_counts_utf8_bytes() -> None:
    assert payload_size_bytes({"value": "€"}) == len('{"value":"€"}'.encode())
