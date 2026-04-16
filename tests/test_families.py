from models.models import FamilyMembership


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_create_family_success(client, auth_tokens) -> None:
    response = client.post(
        "/families/",
        params={"name": "The Smiths"},
        headers=_auth_header(auth_tokens["owner"]),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "The Smiths"
    assert "id" in data


def test_create_family_requires_authentication(client) -> None:
    response = client.post("/families/", params={"name": "NoAuth Family"})

    assert response.status_code == 401


def test_add_family_member_success(client, auth_tokens, sample_family, sample_users) -> None:
    response = client.post(
        f"/families/{sample_family.id}/members",
        params={"user_id": sample_users["outsider"].id},
        headers=_auth_header(auth_tokens["owner"]),
    )

    assert response.status_code == 200
    assert response.json()["user_id"] == sample_users["outsider"].id


def test_add_family_member_fails_for_duplicate_membership(
    client, auth_tokens, sample_family, sample_users
) -> None:
    response = client.post(
        f"/families/{sample_family.id}/members",
        params={"user_id": sample_users["member"].id},
        headers=_auth_header(auth_tokens["owner"]),
    )

    assert response.status_code == 409
    assert response.json()["message"] == "User is already a member of this family"


def test_add_family_member_fails_for_non_admin_member(
    client, auth_tokens, sample_family, sample_users
) -> None:
    response = client.post(
        f"/families/{sample_family.id}/members",
        params={"user_id": sample_users["outsider"].id},
        headers=_auth_header(auth_tokens["member"]),
    )

    assert response.status_code == 403
    assert response.json()["message"] == "Not authorized to add family members"


def test_add_family_member_fails_for_non_member(
    client, auth_tokens, sample_family, sample_users
) -> None:
    response = client.post(
        f"/families/{sample_family.id}/members",
        params={"user_id": sample_users["owner"].id},
        headers=_auth_header(auth_tokens["outsider"]),
    )

    assert response.status_code == 403
    assert response.json()["message"] == "User not in family"


def test_create_family_assigns_creator_as_admin(
    client, auth_tokens, sample_users, db_session
) -> None:
    response = client.post(
        "/families/",
        params={"name": "Admin Assignment Family"},
        headers=_auth_header(auth_tokens["owner"]),
    )

    assert response.status_code == 200
    family_id = response.json()["id"]

    membership = (
        db_session.query(FamilyMembership)
        .filter(
            FamilyMembership.user_id == sample_users["owner"].id,
            FamilyMembership.family_id == family_id,
        )
        .first()
    )
    assert membership is not None
    assert membership.role == "admin"
