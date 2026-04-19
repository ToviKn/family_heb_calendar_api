from datetime import date

from models.models import Notification
from services import notification_service


def test_event_creation_creates_notifications_for_family_members(
    client, db_session, auth_tokens, event_payload, sample_users, auth_header
) -> None:
    response = client.post(
        "/events/",
        json=event_payload,
        headers=auth_header(auth_tokens["owner"]),
    )

    assert response.status_code == 201
    created_event_id = response.json()["id"]

    notifications = (
        db_session.query(Notification)
        .filter(Notification.event_id == created_event_id)
        .all()
    )
    assert len(notifications) == 1
    assert notifications[0].user_id == sample_users["member"].id

def test_get_and_mark_read_notifications(client, db_session, auth_tokens, sample_users, auth_header) -> None:
    notification = Notification(
        user_id=sample_users["owner"].id,
        message="Hello",
        type="system",
        is_read=False,
    )
    db_session.add(notification)
    db_session.commit()
    db_session.refresh(notification)

    get_response = client.get(
        "/notifications/", headers=auth_header(auth_tokens["owner"])
    )
    assert get_response.status_code == 200
    assert len(get_response.json()) == 1

    mark_response = client.patch(
        f"/notifications/{notification.id}/read",
        headers=auth_header(auth_tokens["owner"]),
    )
    assert mark_response.status_code == 200
    assert mark_response.json()["is_read"] is True

def test_create_notification_creates_server_driven_event_reminder(
    client, auth_tokens, event_payload, sample_users, auth_header
) -> None:
    event_response = client.post(
        "/events/",
        json=event_payload,
        headers=auth_header(auth_tokens["owner"]),
    )
    event_data = event_response.json()
    event_id = event_data["id"]

    response = client.post(
        "/notifications/",
        json={"event_id": event_id},
        headers=auth_header(auth_tokens["owner"]),
    )

    assert response.status_code == 201
    data = response.json()
    assert data["user_id"] == sample_users["owner"].id
    assert data["event_id"] == event_id
    assert data["type"] == "EVENT_REMINDER"
    assert (
        data["message"]
        == f"Reminder: {event_payload['title']} on {event_data['next_occurrence']}"
    )

def test_create_notification_prevents_duplicate_user_event_type(
    client, db_session, auth_tokens, event_payload, sample_users, auth_header
) -> None:
    event_response = client.post(
        "/events/",
        json=event_payload,
        headers=auth_header(auth_tokens["owner"]),
    )
    event_id = event_response.json()["id"]

    first_response = client.post(
        "/notifications/",
        json={"event_id": event_id},
        headers=auth_header(auth_tokens["owner"]),
    )
    second_response = client.post(
        "/notifications/",
        json={"event_id": event_id},
        headers=auth_header(auth_tokens["owner"]),
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201
    assert first_response.json()["id"] == second_response.json()["id"]

    notifications = (
        db_session.query(Notification)
        .filter(
            Notification.user_id == sample_users["owner"].id,
            Notification.type == "EVENT_REMINDER",
            Notification.event_id == event_id,
        )
        .all()
    )
    assert len(notifications) == 1

def test_create_notification_returns_404_for_missing_event(client, auth_tokens, auth_header) -> None:
    response = client.post(
        "/notifications/",
        json={"event_id": 999999},
        headers=auth_header(auth_tokens["owner"]),
    )

    assert response.status_code == 404
    assert response.json()["message"] == "Event with identifier '999999' not found"

def test_create_notification_returns_403_for_non_family_member(
    client, auth_tokens, event_payload, auth_header
) -> None:
    event_response = client.post(
        "/events/",
        json=event_payload,
        headers=auth_header(auth_tokens["owner"]),
    )
    event_id = event_response.json()["id"]

    response = client.post(
        "/notifications/",
        json={"event_id": event_id},
        headers=auth_header(auth_tokens["outsider"]),
    )

    assert response.status_code == 403
    assert response.json()["message"] == "User not in family"

def test_process_event_reminders_creates_due_reminders_once(
    client, db_session, auth_tokens, event_payload, auth_header
) -> None:
    due_payload = {
        **event_payload,
        "year": date.today().year,
        "month": date.today().month,
        "day": date.today().day,
        "start_time": "18:00:00",
        "end_time": "20:00:00",
    }

    event_response = client.post(
        "/events/",
        json=due_payload,
        headers=auth_header(auth_tokens["owner"]),
    )
    event_id = event_response.json()["id"]

    assert (
        db_session.query(Notification)
        .filter(
            Notification.event_id == event_id,
            Notification.type == "EVENT_REMINDER",
        )
        .count()
        == 0
    )

    first_process = client.post(
        "/notifications/reminders/process",
        headers=auth_header(auth_tokens["owner"]),
    )
    second_process = client.post(
        "/notifications/reminders/process",
        headers=auth_header(auth_tokens["owner"]),
    )

    assert first_process.status_code == 200
    assert first_process.json()["created"] == 2
    assert second_process.status_code == 200
    assert second_process.json()["created"] == 0

    reminder_notifications = (
        db_session.query(Notification)
        .filter(
            Notification.event_id == event_id,
            Notification.type == "EVENT_REMINDER",
        )
        .all()
    )
    assert len(reminder_notifications) == 2

def test_process_event_reminders_includes_today_events_without_time(
    client, db_session, auth_tokens, event_payload, auth_header
) -> None:
    today_payload = {
        **event_payload,
        "year": date.today().year,
        "month": date.today().month,
        "day": date.today().day,
        "start_time": None,
        "end_time": None,
    }

    event_response = client.post(
        "/events/",
        json=today_payload,
        headers=auth_header(auth_tokens["owner"]),
    )
    event_id = event_response.json()["id"]

    process_response = client.post(
        "/notifications/reminders/process",
        headers=auth_header(auth_tokens["owner"]),
    )

    assert process_response.status_code == 200
    assert process_response.json()["created"] == 2
    assert (
        db_session.query(Notification)
        .filter(
            Notification.event_id == event_id,
            Notification.type == "EVENT_REMINDER",
        )
        .count()
        == 2
    )

def test_process_event_reminders_includes_tomorrow_events(
    client, db_session, auth_tokens, event_payload, auth_header
) -> None:
    tomorrow = date.today().fromordinal(date.today().toordinal() + 1)
    tomorrow_payload = {
        **event_payload,
        "year": tomorrow.year,
        "month": tomorrow.month,
        "day": tomorrow.day,
        "start_time": "08:30:00",
        "end_time": "09:30:00",
    }

    event_response = client.post(
        "/events/",
        json=tomorrow_payload,
        headers=auth_header(auth_tokens["owner"]),
    )
    event_id = event_response.json()["id"]

    process_response = client.post(
        "/notifications/reminders/process",
        headers=auth_header(auth_tokens["owner"]),
    )

    assert process_response.status_code == 200
    assert process_response.json()["created"] == 2
    assert (
        db_session.query(Notification)
        .filter(
            Notification.event_id == event_id,
            Notification.type == "EVENT_REMINDER",
        )
        .count()
        == 2
    )

def test_process_event_reminders_skips_events_outside_one_day_window(
    client, db_session, auth_tokens, event_payload, auth_header
) -> None:
    future = date.today().fromordinal(date.today().toordinal() + 2)
    future_payload = {
        **event_payload,
        "year": future.year,
        "month": future.month,
        "day": future.day,
        "start_time": "08:30:00",
        "end_time": "09:30:00",
    }

    event_response = client.post(
        "/events/",
        json=future_payload,
        headers=auth_header(auth_tokens["owner"]),
    )
    event_id = event_response.json()["id"]

    process_response = client.post(
        "/notifications/reminders/process",
        headers=auth_header(auth_tokens["owner"]),
    )

    assert process_response.status_code == 200
    assert process_response.json()["created"] == 0
    assert (
        db_session.query(Notification)
        .filter(
            Notification.event_id == event_id,
            Notification.type == "EVENT_REMINDER",
        )
        .count()
        == 0
    )

def test_process_event_reminders_is_idempotent_for_recurring_events(
    client, db_session, auth_tokens, event_payload, auth_header
) -> None:
    recurring_payload = {
        **event_payload,
        "year": date.today().year,
        "month": date.today().month,
        "day": date.today().day,
        "repeat_type": "daily",
        "start_time": "09:00:00",
        "end_time": "10:00:00",
    }

    event_response = client.post(
        "/events/",
        json=recurring_payload,
        headers=auth_header(auth_tokens["owner"]),
    )
    event_id = event_response.json()["id"]

    first_process = client.post(
        "/notifications/reminders/process",
        headers=auth_header(auth_tokens["owner"]),
    )
    second_process = client.post(
        "/notifications/reminders/process",
        headers=auth_header(auth_tokens["owner"]),
    )

    assert first_process.status_code == 200
    assert first_process.json()["created"] == 2
    assert second_process.status_code == 200
    assert second_process.json()["created"] == 0
    assert (
        db_session.query(Notification)
        .filter(
            Notification.event_id == event_id,
            Notification.type == "EVENT_REMINDER",
        )
        .count()
        == 2
    )

def test_process_event_reminders_uses_stored_next_occurrence(
    client, db_session, auth_tokens, event_payload, monkeypatch, auth_header
) -> None:
    today_payload = {
        **event_payload,
        "year": date.today().year,
        "month": date.today().month,
        "day": date.today().day,
    }

    event_response = client.post(
        "/events/",
        json=today_payload,
        headers=auth_header(auth_tokens["owner"]),
    )
    event_id = event_response.json()["id"]

    def fail_if_recalculated(_event: object, _reference_date: date | None = None) -> None:
        raise AssertionError("calculate_next_occurrence should not be called")

    monkeypatch.setattr(
        notification_service, "calculate_next_occurrence", fail_if_recalculated
    )

    created = notification_service.process_event_reminders(db_session)

    assert created == 2
    assert (
        db_session.query(Notification)
        .filter(
            Notification.event_id == event_id,
            Notification.type == "EVENT_REMINDER",
        )
        .count()
        == 2
    )


def test_get_notifications_returns_empty_list_for_new_user(client, auth_tokens, auth_header) -> None:
    response = client.get("/notifications/", headers=auth_header(auth_tokens["owner"]))

    assert response.status_code == 200
    assert response.json() == []


def test_delete_notification_success(client, db_session, auth_tokens, sample_users, auth_header) -> None:
    notification = Notification(
        user_id=sample_users["owner"].id,
        message="delete-me",
        type="system",
        is_read=False,
    )
    db_session.add(notification)
    db_session.commit()

    response = client.delete(
        f"/notifications/{notification.id}",
        headers=auth_header(auth_tokens["owner"]),
    )

    assert response.status_code == 204


def test_delete_notification_not_found_for_user(client, auth_tokens, auth_header) -> None:
    response = client.delete(
        "/notifications/9999",
        headers=auth_header(auth_tokens["owner"]),
    )

    assert response.status_code == 404
    assert response.json()["message"] == "Notification with identifier '9999' not found"
