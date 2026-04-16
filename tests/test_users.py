def test_create_user_success(client) -> None:
    payload = {
        "email": "new.user@example.com",
        "name": "New User",
        "password": "strong-password",
    }

    response = client.post("/users/", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == payload["email"]
    assert data["name"] == payload["name"]
    assert "id" in data


def test_create_user_fails_for_duplicate_email(client) -> None:
    payload = {
        "email": "duplicate@example.com",
        "name": "Original",
        "password": "password123",
    }
    client.post("/users/", json=payload)

    response = client.post("/users/", json=payload)

    assert response.status_code == 409
    assert response.json()["message"] == "Email already exists"


def test_create_user_fails_for_invalid_email(client) -> None:
    response = client.post(
        "/users/",
        json={"email": "not-an-email", "name": "Invalid", "password": "pw"},
    )

    assert response.status_code == 422
