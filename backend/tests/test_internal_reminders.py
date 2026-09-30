from types import SimpleNamespace


def test_reminder_endpoint_requires_dedicated_token(client) -> None:
    response = client.post("/internal/reminders/process")

    assert response.status_code == 401


def test_reminder_endpoint_does_not_allow_get(client) -> None:
    response = client.get("/internal/reminders/process")

    assert response.status_code == 405


def test_manual_reminder_endpoint_requires_a_jwt(client) -> None:
    response = client.post("/notifications/reminders/process")

    assert response.status_code == 401


def test_reminder_endpoint_rejects_a_user_jwt(client, auth_tokens, auth_header) -> None:
    response = client.post(
        "/internal/reminders/process",
        headers=auth_header(auth_tokens["owner"]),
    )

    assert response.status_code == 401


def test_manual_reminder_endpoint_rejects_an_invalid_jwt(client) -> None:
    response = client.post(
        "/notifications/reminders/process",
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 401


def test_manual_reminder_endpoint_runs_shared_job(client, monkeypatch, auth_tokens, auth_header) -> None:
    calls: list[object] = []

    def fake_run_reminder_processing(db) -> int:
        calls.append(db)
        return 3

    monkeypatch.setattr(
        "app.routes.notifications.run_reminder_processing", fake_run_reminder_processing
    )

    response = client.post(
        "/notifications/reminders/process",
        headers=auth_header(auth_tokens["owner"]),
    )

    assert response.status_code == 200
    assert response.json() == {"created": 3}
    assert len(calls) == 1


def test_reminder_endpoint_runs_existing_job(client, monkeypatch, reminder_process_header) -> None:
    calls: list[object] = []

    def fake_run_reminder_processing(db) -> int:
        calls.append(db)
        return 3

    monkeypatch.setattr(
        "app.routes.internal.run_reminder_processing", fake_run_reminder_processing
    )

    response = client.post(
        "/internal/reminders/process",
        headers=reminder_process_header,
    )

    assert response.status_code == 200
    assert response.json() == {"created": 3}
    assert len(calls) == 1


def test_reminder_endpoint_returns_service_unavailable_without_render_token(
    client, monkeypatch, reminder_process_header
) -> None:
    monkeypatch.setattr(
        "app.routes.internal.settings", SimpleNamespace(reminder_process_token="")
    )

    response = client.post(
        "/internal/reminders/process",
        headers=reminder_process_header,
    )

    assert response.status_code == 503
