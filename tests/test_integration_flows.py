from models.models import Event, FamilyMembership, Notification


def test_full_happy_flow_register_login_family_member_event_fetch(
    client, db_session, create_user_and_login
) -> None:
    owner = create_user_and_login("flow-owner@example.com", "Flow Owner", "StrongPass1!")
    member = create_user_and_login("flow-member@example.com", "Flow Member", "StrongPass1!")

    owner_headers = {"Authorization": f"Bearer {owner['access_token']}"}

    create_family_response = client.post(
        "/families/",
        params={"name": "Flow Family"},
        headers=owner_headers,
    )
    assert create_family_response.status_code == 200
    family_id = create_family_response.json()["id"]

    add_member_response = client.post(
        f"/families/{family_id}/members",
        params={"user_id": member["user"]["id"]},
        headers=owner_headers,
    )
    assert add_member_response.status_code == 200

    event_payload = {
        "title": "Flow Event",
        "description": "Integration event",
        "calendar_type": "gregorian",
        "year": 2026,
        "month": 6,
        "day": 10,
        "repeat_type": "none",
        "family_id": family_id,
    }
    create_event_response = client.post(
        "/events/",
        json=event_payload,
        headers=owner_headers,
    )
    assert create_event_response.status_code == 201
    event_id = create_event_response.json()["id"]

    events_response = client.get(
        f"/events/family/{family_id}",
        headers=owner_headers,
    )
    assert events_response.status_code == 200
    events_payload = events_response.json()
    assert events_payload["total"] == 1
    assert events_payload["events"][0]["id"] == event_id

    membership = (
        db_session.query(FamilyMembership)
        .filter(
            FamilyMembership.user_id == member["user"]["id"],
            FamilyMembership.family_id == family_id,
        )
        .first()
    )
    assert membership is not None

    persisted_event = db_session.query(Event).filter(Event.id == event_id).first()
    assert persisted_event is not None
    assert persisted_event.title == "Flow Event"


def test_authorization_failure_flow_other_family_forbidden(
    client, create_user_and_login
) -> None:
    owner = create_user_and_login("auth-owner@example.com", "Auth Owner", "StrongPass1!")
    outsider = create_user_and_login("auth-outsider@example.com", "Auth Outsider", "StrongPass1!")

    owner_headers = {"Authorization": f"Bearer {owner['access_token']}"}
    outsider_headers = {"Authorization": f"Bearer {outsider['access_token']}"}

    family_response = client.post(
        "/families/",
        params={"name": "Private Family"},
        headers=owner_headers,
    )
    family_id = family_response.json()["id"]

    event_payload = {
        "title": "Private Event",
        "description": "Only for family",
        "calendar_type": "gregorian",
        "year": 2026,
        "month": 7,
        "day": 11,
        "repeat_type": "none",
        "family_id": family_id,
    }
    create_event = client.post("/events/", json=event_payload, headers=owner_headers)
    assert create_event.status_code == 201

    forbidden_response = client.get(
        f"/events/family/{family_id}",
        headers=outsider_headers,
    )
    assert forbidden_response.status_code == 403
    assert forbidden_response.json()["message"] == "Not authorized to get this family events"


def test_notification_flow_create_trigger_fetch_mark_read(
    client, db_session, create_user_and_login
) -> None:
    owner = create_user_and_login("notif-owner@example.com", "Notif Owner", "StrongPass1!")
    member = create_user_and_login("notif-member@example.com", "Notif Member", "StrongPass1!")
    owner_headers = {"Authorization": f"Bearer {owner['access_token']}"}
    member_headers = {"Authorization": f"Bearer {member['access_token']}"}

    family_response = client.post(
        "/families/",
        params={"name": "Notif Family"},
        headers=owner_headers,
    )
    family_id = family_response.json()["id"]

    add_member = client.post(
        f"/families/{family_id}/members",
        params={"user_id": member["user"]["id"]},
        headers=owner_headers,
    )
    assert add_member.status_code == 200

    event_payload = {
        "title": "Reminder Event",
        "description": "Reminder integration",
        "calendar_type": "gregorian",
        "year": 2026,
        "month": 8,
        "day": 12,
        "repeat_type": "none",
        "family_id": family_id,
    }
    event_response = client.post("/events/", json=event_payload, headers=owner_headers)
    assert event_response.status_code == 201
    event_id = event_response.json()["id"]

    create_notification = client.post(
        "/notifications/",
        json={"event_id": event_id},
        headers=member_headers,
    )
    assert create_notification.status_code == 201
    notification_id = create_notification.json()["id"]

    fetch_notifications = client.get("/notifications/", headers=member_headers)
    assert fetch_notifications.status_code == 200
    fetch_payload = fetch_notifications.json()
    assert fetch_payload["total"] >= 1
    unread_ids = {item["id"] for item in fetch_payload["events"] if item["is_read"] is False}
    assert notification_id in unread_ids

    mark_read_response = client.patch(
        f"/notifications/{notification_id}/read",
        headers=member_headers,
    )
    assert mark_read_response.status_code == 200
    assert mark_read_response.json()["is_read"] is True

    persisted_notification = (
        db_session.query(Notification)
        .filter(Notification.id == notification_id)
        .first()
    )
    assert persisted_notification is not None
    assert persisted_notification.is_read is True
