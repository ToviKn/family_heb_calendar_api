from models.models import FamilyJoinRequest, FamilyMembership, Notification



def test_create_family_success(client, auth_tokens, auth_header) -> None:
    response = client.post(
        "/families/",
        params={"name": "The Smiths"},
        headers=auth_header(auth_tokens["owner"]),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "The Smiths"
    assert "id" in data


def test_create_family_requires_authentication(client) -> None:
    response = client.post("/families/", params={"name": "NoAuth Family"})

    assert response.status_code == 401


def test_add_family_member_success(client, auth_tokens, auth_header, sample_family, sample_users) -> None:
    response = client.post(
        f"/families/{sample_family.id}/members",
        params={"user_id": sample_users["outsider"].id},
        headers=auth_header(auth_tokens["owner"]),
    )

    assert response.status_code == 200
    assert response.json()["user_id"] == sample_users["outsider"].id


def test_add_family_member_fails_for_duplicate_membership(
    client, auth_tokens, sample_family, sample_users, auth_header
) -> None:
    response = client.post(
        f"/families/{sample_family.id}/members",
        params={"user_id": sample_users["member"].id},
        headers=auth_header(auth_tokens["owner"]),
    )

    assert response.status_code == 409
    assert response.json()["message"] == "User is already a member of this family"


def test_add_family_member_non_admin_creates_join_request(
    client, auth_tokens, sample_family, sample_users, auth_header, db_session
) -> None:
    response = client.post(
        f"/families/{sample_family.id}/members",
        params={"user_id": sample_users["outsider"].id},
        headers=auth_header(auth_tokens["member"]),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "pending"
    assert response.json()["message"] == "Join request sent to family admins"

    join_request = (
        db_session.query(FamilyJoinRequest)
        .filter(
            FamilyJoinRequest.user_id == sample_users["outsider"].id,
            FamilyJoinRequest.family_id == sample_family.id,
            FamilyJoinRequest.requested_by == sample_users["member"].id,
            FamilyJoinRequest.status == "pending",
        )
        .first()
    )
    assert join_request is not None

    admin_notification = (
        db_session.query(Notification)
        .filter(
            Notification.user_id == sample_users["owner"].id,
            Notification.type == "join_request",
        )
        .first()
    )
    assert admin_notification is not None
    assert admin_notification.message == (
        f"{sample_users['member'].name} requested to add {sample_users['outsider'].name} to family {sample_family.name}"
    )
    assert admin_notification.metadata_json == {
        "actor": {"id": sample_users["member"].id, "name": sample_users["member"].name},
        "target": {"id": sample_users["outsider"].id, "name": sample_users["outsider"].name},
        "family_id": sample_family.id,
        "family_name": sample_family.name,
    }


def test_add_family_member_non_member_creates_join_request(
    client, auth_tokens, sample_family, sample_users, auth_header
) -> None:
    response = client.post(
        f"/families/{sample_family.id}/members",
        params={"user_id": sample_users["outsider"].id},
        headers=auth_header(auth_tokens["outsider"]),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "pending"
    assert response.json()["message"] == "Join request sent to family admins"


def test_add_family_member_non_admin_prevents_duplicate_pending_join_request(
    client, auth_tokens, sample_family, sample_users, auth_header
) -> None:
    first_response = client.post(
        f"/families/{sample_family.id}/members",
        params={"user_id": sample_users["outsider"].id},
        headers=auth_header(auth_tokens["member"]),
    )
    second_response = client.post(
        f"/families/{sample_family.id}/members",
        params={"user_id": sample_users["outsider"].id},
        headers=auth_header(auth_tokens["member"]),
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert second_response.json()["status"] == "pending"
    assert second_response.json()["message"] == "Join request already pending"


def test_create_family_assigns_creator_as_admin(
    client, auth_tokens, sample_users, db_session, auth_header
) -> None:
    response = client.post(
        "/families/",
        params={"name": "Admin Assignment Family"},
        headers=auth_header(auth_tokens["owner"]),
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


def test_add_family_member_returns_not_found_for_missing_family_when_actor_not_member(client, auth_tokens, sample_users, auth_header) -> None:
    response = client.post(
        "/families/9999/members",
        params={"user_id": sample_users["outsider"].id},
        headers=auth_header(auth_tokens["owner"]),
    )

    assert response.status_code == 404
    assert response.json()["message"] == "Family with identifier '9999' not found"


def test_add_family_member_returns_not_found_for_missing_user(client, auth_tokens, sample_family, auth_header) -> None:
    response = client.post(
        f"/families/{sample_family.id}/members",
        params={"user_id": 9999},
        headers=auth_header(auth_tokens["owner"]),
    )

    assert response.status_code == 404
    assert response.json()["message"] == "User with identifier '9999' not found"


def test_request_to_join_family_creates_self_join_request(
    client, auth_tokens, sample_family, sample_users, auth_header, db_session
) -> None:
    response = client.post(
        f"/families/{sample_family.id}/join-requests",
        headers=auth_header(auth_tokens["outsider"]),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "pending"
    assert response.json()["message"] == "Join request sent to family admins"

    join_request = (
        db_session.query(FamilyJoinRequest)
        .filter(
            FamilyJoinRequest.user_id == sample_users["outsider"].id,
            FamilyJoinRequest.family_id == sample_family.id,
            FamilyJoinRequest.requested_by == sample_users["outsider"].id,
            FamilyJoinRequest.status == "pending",
        )
        .first()
    )
    assert join_request is not None


def test_request_to_join_family_prevents_duplicate_pending_request(
    client, auth_tokens, sample_family, auth_header
) -> None:
    first_response = client.post(
        f"/families/{sample_family.id}/join-requests",
        headers=auth_header(auth_tokens["outsider"]),
    )
    second_response = client.post(
        f"/families/{sample_family.id}/join-requests",
        headers=auth_header(auth_tokens["outsider"]),
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert second_response.json()["status"] == "pending"
    assert second_response.json()["message"] == "Join request already pending"


def test_admin_can_list_pending_join_requests(
    client, auth_tokens, sample_family, sample_users, auth_header
) -> None:
    create_response = client.post(
        f"/families/{sample_family.id}/members",
        params={"user_id": sample_users["outsider"].id},
        headers=auth_header(auth_tokens["outsider"]),
    )
    assert create_response.status_code == 200

    response = client.get(
        f"/families/{sample_family.id}/join-requests",
        headers=auth_header(auth_tokens["owner"]),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    request = data["requests"][0]
    assert request["user_id"] == sample_users["outsider"].id
    assert request["requested_by"] == sample_users["outsider"].id
    assert request["status"] == "pending"
    assert request["user"] == {
        "id": sample_users["outsider"].id,
        "name": sample_users["outsider"].name,
        "email": sample_users["outsider"].email,
    }


def test_non_admin_cannot_list_pending_join_requests(
    client, auth_tokens, sample_family, auth_header
) -> None:
    response = client.get(
        f"/families/{sample_family.id}/join-requests",
        headers=auth_header(auth_tokens["member"]),
    )

    assert response.status_code == 403


def test_admin_can_approve_join_request(
    client, auth_tokens, sample_family, sample_users, auth_header, db_session
) -> None:
    create_response = client.post(
        f"/families/{sample_family.id}/members",
        params={"user_id": sample_users["outsider"].id},
        headers=auth_header(auth_tokens["outsider"]),
    )
    assert create_response.status_code == 200
    join_request = (
        db_session.query(FamilyJoinRequest)
        .filter(
            FamilyJoinRequest.user_id == sample_users["outsider"].id,
            FamilyJoinRequest.family_id == sample_family.id,
            FamilyJoinRequest.status == "pending",
        )
        .first()
    )
    assert join_request is not None

    response = client.post(
        f"/families/{sample_family.id}/join-requests/{join_request.id}/approve",
        headers=auth_header(auth_tokens["owner"]),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == sample_users["outsider"].id
    assert data["family_id"] == sample_family.id

    membership = (
        db_session.query(FamilyMembership)
        .filter(
            FamilyMembership.user_id == sample_users["outsider"].id,
            FamilyMembership.family_id == sample_family.id,
        )
        .first()
    )
    assert membership is not None
    assert (
        db_session.query(FamilyJoinRequest)
        .filter(FamilyJoinRequest.id == join_request.id)
        .first()
        is None
    )


def test_admin_can_reject_join_request(
    client, auth_tokens, sample_family, sample_users, auth_header, db_session
) -> None:
    create_response = client.post(
        f"/families/{sample_family.id}/members",
        params={"user_id": sample_users["outsider"].id},
        headers=auth_header(auth_tokens["outsider"]),
    )
    assert create_response.status_code == 200
    join_request = (
        db_session.query(FamilyJoinRequest)
        .filter(
            FamilyJoinRequest.user_id == sample_users["outsider"].id,
            FamilyJoinRequest.family_id == sample_family.id,
            FamilyJoinRequest.status == "pending",
        )
        .first()
    )
    assert join_request is not None

    response = client.delete(
        f"/families/{sample_family.id}/join-requests/{join_request.id}",
        headers=auth_header(auth_tokens["owner"]),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "rejected"
    assert (
        db_session.query(FamilyJoinRequest)
        .filter(FamilyJoinRequest.id == join_request.id)
        .first()
        is None
    )
    assert (
        db_session.query(FamilyMembership)
        .filter(
            FamilyMembership.user_id == sample_users["outsider"].id,
            FamilyMembership.family_id == sample_family.id,
        )
        .first()
        is None
    )
