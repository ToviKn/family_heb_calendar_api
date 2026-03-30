from datetime import datetime, timedelta

from jose import jwt

from services.auth_service import ALGORITHM, SECRET_KEY


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _token(sub: str, *, expires_delta_minutes: int = 30) -> str:
    payload = {
        "sub": sub,
        "exp": datetime.utcnow() + timedelta(minutes=expires_delta_minutes),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def test_create_event_requires_authentication(client, event_payload) -> None:
    response = client.post("/events/", json=event_payload)
    assert response.status_code == 401


def test_create_family_requires_authentication(client) -> None:
    response = client.post("/families/", params={"name": "No auth"})
    assert response.status_code == 401


def test_create_family_rejects_invalid_token(client) -> None:
    response = client.post(
        "/families/",
        params={"name": "Invalid Token Family"},
        headers={"Authorization": "Bearer not-a-valid-token"},
    )

    assert response.status_code == 401
    assert response.json()["message"] == "Invalid token"


def test_create_family_rejects_expired_token(client) -> None:
    expired = _token("1", expires_delta_minutes=-1)
    response = client.post(
        "/families/",
        params={"name": "Expired Token Family"},
        headers=_auth_header(expired),
    )

    assert response.status_code == 401
    assert response.json()["message"] == "Invalid token"


def test_create_family_rejects_token_for_missing_user(client) -> None:
    unknown_user_token = _token("9999")
    response = client.post(
        "/families/",
        params={"name": "Unknown User Token Family"},
        headers=_auth_header(unknown_user_token),
    )

    assert response.status_code == 401
    assert response.json()["message"] == "User not found"


def test_create_family_rejects_token_with_non_numeric_subject(client) -> None:
    bad_subject_token = _token("abc")
    response = client.post(
        "/families/",
        params={"name": "Bad Subject Family"},
        headers=_auth_header(bad_subject_token),
    )

    assert response.status_code == 401
    assert response.json()["message"] == "Invalid user ID in token"


def test_create_event_non_member_surfaces_current_error_contract(
    client, auth_tokens, event_payload
) -> None:
    response = client.post(
        "/events/",
        json=event_payload,
        headers=_auth_header(auth_tokens["outsider"]),
    )

    assert response.status_code == 500
    assert response.json()["message"] == "Internal server error"
