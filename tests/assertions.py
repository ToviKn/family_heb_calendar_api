from __future__ import annotations

from typing import Any

def assert_error_response(
    response: Any,
    expected_status: int,
    *,
    expected_message: str | None = None,
    message_contains: str | None = None,
) -> dict[str, Any]:
    assert response.status_code == expected_status
    payload = response.json()
    assert isinstance(payload, dict)
    assert isinstance(payload.get("message"), str)
    assert isinstance(payload.get("details"), dict)

    if expected_message is not None:
        assert payload["message"] == expected_message
    if message_contains is not None:
        assert message_contains.lower() in payload["message"].lower()

    return payload
