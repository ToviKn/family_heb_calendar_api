from jose import jwt

from services.auth_service import ALGORITHM, SECRET_KEY
from tests.assertions import assert_error_response


def test_login_success_returns_bearer_token(client, sample_users) -> None:
    response = client.post(
        "/auth/login",
        data={"username": sample_users["owner"].email, "password": "owner-password"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["token_type"] == "bearer"
    assert payload["access_token"]


def test_login_fails_with_wrong_password(client, sample_users) -> None:
    response = client.post(
        "/auth/login",
        data={"username": sample_users["owner"].email, "password": "wrong-password"},
    )

    assert_error_response(response, 401, message_contains="invalid credentials")


def test_login_fails_with_unknown_user(client) -> None:
    response = client.post(
        "/auth/login",
        data={"username": "missing@example.com", "password": "does-not-matter"},
    )

    assert_error_response(response, 401, message_contains="invalid credentials")


def test_login_token_contains_string_subject(client, sample_users) -> None:
    response = client.post(
        "/auth/login",
        data={"username": sample_users["owner"].email, "password": "owner-password"},
    )

    token = response.json()["access_token"]
    decoded = jwt.decode(
        token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_exp": False}
    )
    assert isinstance(decoded["sub"], str)
    assert decoded["sub"] == str(sample_users["owner"].id)
