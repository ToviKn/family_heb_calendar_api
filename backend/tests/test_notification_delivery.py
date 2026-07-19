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
