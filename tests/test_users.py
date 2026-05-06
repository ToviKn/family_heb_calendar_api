from services.auth_service import verify_password


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


def test_change_password_success(client, db_session, auth_tokens, sample_users, auth_header) -> None:
    response = client.post(
        "/users/change-password",
        json={"current_password": "owner-password", "new_password": "NewStrongPass1!"},
        headers=auth_header(auth_tokens["owner"]),
    )

    assert response.status_code == 200
    assert response.json() == {"status": "success", "message": "Password updated successfully"}

    db_session.refresh(sample_users["owner"])
    assert verify_password("NewStrongPass1!", sample_users["owner"].password_hash)
    assert not verify_password("owner-password", sample_users["owner"].password_hash)


def test_change_password_fails_with_wrong_current_password(client, db_session, auth_tokens, sample_users, auth_header) -> None:
    old_hash = sample_users["owner"].password_hash
    response = client.post(
        "/users/change-password",
        json={"current_password": "wrong-password", "new_password": "NewStrongPass1!"},
        headers=auth_header(auth_tokens["owner"]),
    )

    assert response.status_code == 400
    assert response.json()["message"] == "Current password is incorrect"

    db_session.refresh(sample_users["owner"])
    assert sample_users["owner"].password_hash == old_hash


def test_change_password_requires_authentication(client) -> None:
    response = client.post(
        "/users/change-password",
        json={"current_password": "owner-password", "new_password": "NewStrongPass1!"},
    )

    assert response.status_code == 401


def test_change_password_rejects_reuse_of_current_password(client, db_session, auth_tokens, sample_users, auth_header) -> None:
    old_hash = sample_users["owner"].password_hash
    response = client.post(
        "/users/change-password",
        json={"current_password": "owner-password", "new_password": "owner-password"},
        headers=auth_header(auth_tokens["owner"]),
    )

    assert response.status_code == 400
    assert response.json()["message"] == "New password must be different from current password"
    db_session.refresh(sample_users["owner"])
    assert sample_users["owner"].password_hash == old_hash


def test_change_password_returns_password_policy_errors(
    client, db_session, auth_tokens, sample_users, auth_header
) -> None:
    old_hash = sample_users["owner"].password_hash
    response = client.post(
        "/users/change-password",
        json={"current_password": "owner-password", "new_password": "short"},
        headers=auth_header(auth_tokens["owner"]),
    )

    assert response.status_code == 400
    assert response.json()["message"] == "Password must be at least 10 characters"
    assert response.json()["details"] == {"field": "new_password"}

    db_session.refresh(sample_users["owner"])
    assert sample_users["owner"].password_hash == old_hash
