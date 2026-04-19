def test_create_user_success(client) -> None:
    payload = {
        "email": "new.user@example.com",
        "name": "New User",
        "password": "StrongPassword1!",
    }

    response = client.post("/users/", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == payload["email"]
    assert data["name"] == payload["name"]
    assert isinstance(data["id"], int)
    assert "password" not in data


def test_create_user_fails_for_duplicate_email(client) -> None:
    payload = {
        "email": "duplicate@example.com",
        "name": "Original",
        "password": "StrongPassword1!",
    }
    first = client.post("/users/", json=payload)

    response = client.post("/users/", json=payload)

    assert first.status_code == 200
    assert response.status_code == 409
    assert response.json()["message"] == "Email already exists"


def test_create_user_fails_for_invalid_email(client) -> None:
    response = client.post(
        "/users/",
        json={"email": "not-an-email", "name": "Invalid", "password": "StrongPassword1!"},
    )

    assert response.status_code == 422


def test_create_user_fails_for_weak_password(client) -> None:
    response = client.post(
        "/users/",
        json={"email": "weak@example.com", "name": "Weak", "password": "weakpass"},
    )

    assert response.status_code == 422
    body = response.json()
    assert body["message"].startswith("Password must")
