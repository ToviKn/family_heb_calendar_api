from app.models.push import PushSubscriptionCreate
from app.services.notification_preferences_service import get_or_create_preferences


def test_preferences_default_enabled(db_session, sample_users):
    preferences = get_or_create_preferences(db_session, sample_users["owner"].id)

    assert preferences.email_enabled is True
    assert preferences.push_enabled is True
    assert preferences.notify_today is True
    assert preferences.notify_day_before is True


def test_push_subscription_payload_requires_https():
    try:
        PushSubscriptionCreate.model_validate({
            "endpoint": "http://example.com/push",
            "keys": {"p256dh": "key", "auth": "auth"},
        })
    except ValueError:
        return

    raise AssertionError("Expected non-HTTPS endpoint validation to fail")


def test_push_subscribe_and_unsubscribe(client, auth_tokens):
    headers = {"Authorization": f"Bearer {auth_tokens['owner']}"}
    payload = {
        "endpoint": "https://push.example.com/subscription/1",
        "keys": {"p256dh": "public-key", "auth": "auth-secret"},
    }

    response = client.post("/api/push/subscribe", json=payload, headers=headers)
    assert response.status_code == 201
    assert response.json()["endpoint"] == payload["endpoint"]

    delete_response = client.request(
        "DELETE",
        "/api/push/unsubscribe",
        json={"endpoint": payload["endpoint"]},
        headers=headers,
    )
    assert delete_response.status_code == 204


def test_preferences_endpoint_round_trip(client, auth_tokens):
    headers = {"Authorization": f"Bearer {auth_tokens['owner']}"}

    response = client.put(
        "/api/notification-preferences/",
        json={"email_enabled": False, "push_enabled": True, "notify_today": False},
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["email_enabled"] is False
    assert body["push_enabled"] is True
    assert body["notify_today"] is False
    assert body["notify_day_before"] is True

from datetime import datetime

from app.models.models import Notification
from app.services.notification_dispatcher import dispatch_notification
from app.services.notification_templates import resolve_template
from app.storage.enums import NotificationType


def test_dispatcher_uses_templates_for_non_reminder_notification(monkeypatch, db_session, sample_users):
    user = sample_users["owner"]
    notification = Notification(
        user_id=user.id,
        event_id=None,
        message="Member requested to join family Test Family",
        type=NotificationType.JOIN_REQUEST.value,
        is_read=False,
        created_at=datetime.utcnow(),
        metadata_json={
            "notification_kind": "join_request",
            "target": {"id": sample_users["member"].id, "name": sample_users["member"].name},
            "family_name": "Test Family",
        },
    )
    db_session.add(notification)
    db_session.commit()
    db_session.refresh(notification)
    sent: dict[str, str] = {}

    def fake_send_email(to_email: str, subject: str, text_body: str, html_body: str) -> bool:
        sent["to_email"] = to_email
        sent["subject"] = subject
        sent["text_body"] = text_body
        sent["html_body"] = html_body
        return True

    monkeypatch.setattr("app.services.notification_dispatcher.send_email", fake_send_email)

    dispatch_notification(db_session, notification)

    assert sent["to_email"] == user.email
    assert sent["subject"] == "Family join request"
    assert "requested to join family Test Family" in sent["text_body"]


def test_template_registry_covers_required_notification_kinds(sample_users):
    user = sample_users["owner"]
    required_kinds = [
        "event_reminder",
        "family_invitation",
        "joined_family",
        "join_request",
        "join_request_approved",
        "join_request_rejected",
        "event_created",
        "event_updated",
        "event_deleted",
    ]

    for kind in required_kinds:
        notification = Notification(
            user_id=user.id,
            event_id=None,
            message="Template smoke test",
            type=NotificationType.SYSTEM.value,
            metadata_json={"notification_kind": kind, "event_title": "Dinner", "family_name": "Test Family"},
        )
        template = resolve_template(notification, user)

        assert template.email_subject
        assert template.email_text_body
        assert template.email_html_body
        assert template.push_title
        assert template.push_body
