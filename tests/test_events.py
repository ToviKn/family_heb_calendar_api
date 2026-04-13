from datetime import date

from sqlalchemy import text

def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}

def test_create_event_success(client, auth_tokens, event_payload) -> None:
    response = client.post(
        "/events/",
        json=event_payload,
        headers=_auth_header(auth_tokens["owner"]),
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == event_payload["title"]
    assert data["family_id"] == event_payload["family_id"]
    assert data["created_by"] > 0


def test_create_event_ignores_client_created_by(client, auth_tokens, event_payload) -> None:
    payload = event_payload.copy()
    payload["created_by"] = 999999

    response = client.post(
        "/events/",
        json=payload,
        headers=_auth_header(auth_tokens["owner"]),
    )

    assert response.status_code == 201
    assert response.json()["created_by"] != 999999

def test_create_event_accepts_time_only_inputs(client, auth_tokens, event_payload) -> None:
    payload = event_payload.copy()
    payload["start_time"] = "18:00:00"
    payload["end_time"] = "20:00:00"

    response = client.post(
        "/events/",
        json=payload,
        headers=_auth_header(auth_tokens["owner"]),
    )

    assert response.status_code == 201
    assert response.json()["start_time"] == "18:00:00"
    assert response.json()["end_time"] == "20:00:00"



def test_create_event_normalizes_hh_mm_inputs_to_seconds(client, auth_tokens, event_payload) -> None:
    payload = event_payload.copy()
    payload["start_time"] = "18:00"
    payload["end_time"] = "20:00"

    response = client.post(
        "/events/",
        json=payload,
        headers=_auth_header(auth_tokens["owner"]),
    )

    assert response.status_code == 201
    assert response.json()["start_time"] == "18:00:00"
    assert response.json()["end_time"] == "20:00:00"


def test_openapi_event_create_time_fields_are_time_only(client) -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    schema = response.json()["components"]["schemas"]["EventCreate"]["properties"]
    assert schema["start_time"]["anyOf"][0]["format"] == "time"
    assert schema["start_time"]["example"] == "18:00:00"
    assert schema["end_time"]["anyOf"][0]["format"] == "time"
    assert schema["end_time"]["example"] == "20:00:00"

def test_create_event_rejects_datetime_time_inputs(client, auth_tokens, event_payload) -> None:
    payload = event_payload.copy()
    payload["start_time"] = "2026-05-20T18:00:00"
    payload["end_time"] = "2026-05-20T20:00:00"

    response = client.post(
        "/events/",
        json=payload,
        headers=_auth_header(auth_tokens["owner"]),
    )

    assert response.status_code == 422

def test_create_event_rejects_placeholder_date(client, auth_tokens, event_payload) -> None:
    payload = event_payload.copy()
    payload["year"] = 1
    payload["month"] = 1
    payload["day"] = 1

    response = client.post(
        "/events/",
        json=payload,
        headers=_auth_header(auth_tokens["owner"]),
    )

    assert response.status_code == 422

def test_create_event_rejects_end_time_before_start_time(client, auth_tokens, event_payload) -> None:
    payload = event_payload.copy()
    payload["start_time"] = "20:00:00"
    payload["end_time"] = "18:00:00"

    response = client.post(
        "/events/",
        json=payload,
        headers=_auth_header(auth_tokens["owner"]),
    )

    assert response.status_code == 422

def test_create_event_validation_failure(
    client, auth_tokens, sample_family
) -> None:
    invalid_payload = {
        "title": "",
        "calendar_type": "gregorian",
        "year": 2026,
        "month": 2,
        "day": 30,
        "repeat_type": "none",
        "family_id": sample_family.id,
    }
    response = client.post(
        "/events/",
        json=invalid_payload,
        headers=_auth_header(auth_tokens["owner"]),
    )

    assert response.status_code == 422

def test_get_event_by_id_success(client, auth_tokens, event_payload) -> None:
    create_response = client.post(
        "/events/",
        json=event_payload,
        headers=_auth_header(auth_tokens["owner"]),
    )
    event_id = create_response.json()["id"]

    response = client.get(f"/events/{event_id}", headers=_auth_header(auth_tokens["owner"]))

    assert response.status_code == 200
    assert response.json()["id"] == event_id

def test_get_event_by_id_not_found(client, auth_tokens) -> None:
    response = client.get("/events/9999", headers=_auth_header(auth_tokens["owner"]))
    assert response.status_code == 404

def test_update_event_success(client, auth_tokens, event_payload) -> None:
    create_response = client.post(
        "/events/",
        json=event_payload,
        headers=_auth_header(auth_tokens["owner"]),
    )
    event_id = create_response.json()["id"]

    response = client.put(
        f"/events/{event_id}",
        json={"title": "Updated Event"},
        headers=_auth_header(auth_tokens["owner"]),
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Updated Event"


def test_update_event_ignores_client_created_by(client, auth_tokens, event_payload) -> None:
    create_response = client.post(
        "/events/",
        json=event_payload,
        headers=_auth_header(auth_tokens["owner"]),
    )
    event_id = create_response.json()["id"]
    original_created_by = create_response.json()["created_by"]

    response = client.put(
        f"/events/{event_id}",
        json={"title": "Updated Event", "created_by": 999999},
        headers=_auth_header(auth_tokens["owner"]),
    )

    assert response.status_code == 200
    assert response.json()["created_by"] == original_created_by

def test_update_event_not_found(client, auth_tokens) -> None:
    response = client.put(
        "/events/9999",
        json={"title": "Ghost Event"},
        headers=_auth_header(auth_tokens["owner"]),
    )
    assert response.status_code == 404

def test_delete_event_success(client, auth_tokens, event_payload) -> None:
    create_response = client.post(
        "/events/",
        json=event_payload,
        headers=_auth_header(auth_tokens["owner"]),
    )
    event_id = create_response.json()["id"]

    delete_response = client.delete(
        f"/events/{event_id}", headers=_auth_header(auth_tokens["owner"])
    )

    assert delete_response.status_code == 200
    assert delete_response.json()["message"] == "Event deleted successfully"

def test_delete_event_not_found(client, auth_tokens) -> None:
    response = client.delete("/events/9999", headers=_auth_header(auth_tokens["owner"]))
    assert response.status_code == 404

def test_search_events_by_date_success(client, auth_tokens, event_payload) -> None:
    client.post(
        "/events/", json=event_payload, headers=_auth_header(auth_tokens["owner"])
    )

    response = client.get(
        f"/events/?year={event_payload['year']}&month={event_payload['month']}&day={event_payload['day']}",
        headers=_auth_header(auth_tokens["owner"]),
    )

    assert response.status_code == 200
    assert len(response.json()) == 1

def test_search_events_by_date_invalid_query(client, auth_tokens) -> None:
    response = client.get(
        "/events/?year=2026&month=13&day=1", headers=_auth_header(auth_tokens["owner"])
    )
    assert response.status_code == 422

def test_today_events_endpoint_returns_list(client, auth_tokens) -> None:
    response = client.get("/events/today", headers=_auth_header(auth_tokens["owner"]))
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_upcoming_events_includes_created_event(client, auth_tokens, event_payload) -> None:
    payload = event_payload.copy()
    today = date.today()
    payload["year"] = today.year
    payload["month"] = today.month
    payload["day"] = today.day

    client.post("/events/", json=payload, headers=_auth_header(auth_tokens["owner"]))
    response = client.get("/events/upcoming?days=30", headers=_auth_header(auth_tokens["owner"]))

    assert response.status_code == 200
    assert len(response.json()) >= 1

def test_upcoming_events_rejects_invalid_days(client, auth_tokens) -> None:
    response = client.get("/events/upcoming?days=0", headers=_auth_header(auth_tokens["owner"]))
    assert response.status_code == 422

def test_family_events_pagination(client, auth_tokens, event_payload) -> None:
    client.post(
        "/events/", json=event_payload, headers=_auth_header(auth_tokens["owner"])
    )

    response = client.get(
        f"/events/family/{event_payload['family_id']}?page=1&per_page=1",
        headers=_auth_header(auth_tokens["owner"]),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert data["page"] == 1
    assert data["per_page"] == 1
    assert isinstance(data["events"], list)

def test_create_event_stores_repeat_type_as_lowercase_string(
    client, auth_tokens, event_payload, db_session
) -> None:
    payload = event_payload.copy()
    payload["repeat_type"] = "weekly"

    response = client.post(
        "/events/",
        json=payload,
        headers=_auth_header(auth_tokens["owner"]),
    )

    assert response.status_code == 201
    event_id = response.json()["id"]

    stored_repeat_type = db_session.execute(
        text("SELECT repeat_type FROM events WHERE id = :event_id"),
        {"event_id": event_id},
    ).scalar_one()

    assert stored_repeat_type == "weekly"

def test_create_event_rejects_uppercase_repeat_type(
    client, auth_tokens, event_payload
) -> None:
    payload = event_payload.copy()
    payload["repeat_type"] = "WEEKLY"

    response = client.post(
        "/events/",
        json=payload,
        headers=_auth_header(auth_tokens["owner"]),
    )

    assert response.status_code == 422
