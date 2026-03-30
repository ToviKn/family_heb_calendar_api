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
    assert response.json() == {}


def test_add_family_member_fails_for_duplicate_membership(
    client, auth_tokens, sample_family, sample_users
) -> None:
    response = client.post(
        f"/families/{sample_family.id}/members",
        params={"user_id": sample_users["member"].id},
        headers=_auth_header(auth_tokens["owner"]),
    )

    assert response.status_code == 400
    assert "Membership already exists" in response.json()["message"]
