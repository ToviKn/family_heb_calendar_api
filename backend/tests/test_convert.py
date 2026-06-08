def test_convert_hebrew_success(client) -> None:
    response = client.get("/convert/hebrew?year=2026&month=3&day=3")

    assert response.status_code == 200
    body = response.json()

    assert body["gregorian_date"]["year"] == 2026
    assert body["gregorian_date"]["month"] == 3
    assert body["gregorian_date"]["day"] == 3

    assert body["hebrew_date"]["year"] == 5786
    assert body["hebrew_date"]["month"] == 12
    assert body["hebrew_date"]["day"] == 14


def test_convert_gregorian_success(client) -> None:
    response = client.get("/convert/gregorian?year=5786&month=12&day=14")

    assert response.status_code == 200
    body = response.json()

    assert body["gregorian_date"]["year"] == 2026
    assert body["gregorian_date"]["month"] == 3
    assert body["gregorian_date"]["day"] == 3

    assert body["hebrew_date"]["year"] == 5786
    assert body["hebrew_date"]["month"] == 12
    assert body["hebrew_date"]["day"] == 14


def test_convert_rejects_invalid_gregorian_date(client) -> None:
    response = client.get("/convert/hebrew?year=2026&month=2&day=30")

    assert response.status_code == 422
    assert "Invalid Gregorian date" in response.json()["message"]


def test_convert_rejects_invalid_hebrew_month(client) -> None:
    response = client.get("/convert/gregorian?year=5786&month=14&day=1")

    assert response.status_code == 422
