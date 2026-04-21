import pytest


def test_auth_login_requires_password_field(client, sample_users) -> None:
    response = client.post(
        "/auth/login",
        data={"username": sample_users["owner"].email},
    )

    assert response.status_code == 422


@pytest.mark.parametrize(
    ("path", "query"),
    [
        ("/convert/hebrew", {"year": 2026, "month": 2, "day": 30}),
        ("/convert/hebrew", {"year": 2026, "month": 13, "day": 1}),
        ("/convert/gregorian", {"year": 5786, "month": 14, "day": 1}),
        ("/convert/gregorian", {"year": 5786, "month": 12, "day": 50}),
    ],
)
def test_convert_endpoints_reject_invalid_query_values(client, path, query) -> None:
    response = client.get(path, params=query)

    assert response.status_code == 422


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("post", "/events/"),
        ("get", "/events/"),
        ("get", "/events/today"),
        ("get", "/events/upcoming"),
        ("get", "/events/family/1"),
        ("get", "/events/1"),
        ("put", "/events/1"),
        ("delete", "/events/1"),
        ("post", "/families/"),
        ("post", "/families/1/members"),
        ("post", "/notifications/"),
        ("get", "/notifications/"),
        ("patch", "/notifications/1/read"),
        ("delete", "/notifications/1"),
        ("post", "/notifications/reminders/process"),
    ],
)
def test_protected_endpoints_require_authentication(client, method, path, event_payload) -> None:
    kwargs = {}
    if path == "/events/" and method == "post":
        kwargs["json"] = event_payload
    elif path == "/events/" and method == "get":
        kwargs["params"] = {"year": event_payload["year"], "month": event_payload["month"], "day": event_payload["day"]}
    elif path == "/events/upcoming":
        kwargs["params"] = {"days": 30}
    elif path == "/events/1" and method == "put":
        kwargs["json"] = {"title": "Nope"}
    elif path == "/families/":
        kwargs["params"] = {"name": "No Auth Family"}
    elif path == "/families/1/members":
        kwargs["params"] = {"user_id": 1}
    elif path == "/notifications/" and method == "post":
        kwargs["json"] = {"event_id": 1}

    response = getattr(client, method)(path, **kwargs)

    assert response.status_code == 401


@pytest.mark.parametrize(
    "password",
    [
        "",  # empty
        "short1A!",  # too short
        "alllowercase123!",  # missing uppercase
        "ALLUPPERCASE123!",  # missing lowercase
        "NoNumbers!!!",  # missing number
        "NoSpecial1234",  # missing special
    ],
)
def test_create_user_rejects_password_policy_variants(client, password) -> None:
    response = client.post(
        "/users/",
        json={
            "email": "policy@example.com",
            "name": "Policy User",
            "password": password,
        },
    )

    assert response.status_code == 422
    assert "Password" in response.json()["message"]
