"""Automated API tests for the WashWise backend.

The suite re-seeds the database first, so it always runs against known data.
"""

import pytest

import app as app_module
import seed


@pytest.fixture(scope="module")
def client():
    seed.reset()
    seed.seed()
    app_module.app.config["TESTING"] = True
    return app_module.app.test_client()


def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.get_json()["database"] == "connected"


def test_list_buildings(client):
    res = client.get("/buildings")
    assert res.status_code == 200
    assert len(res.get_json()) == 3


def test_users_never_expose_password(client):
    users = client.get("/users").get_json()
    assert users
    assert all("password_hash" not in u for u in users)


def test_create_user_and_login(client):
    created = client.post("/users", json={
        "building_id": 1, "name": "Pytest User", "email": "pytest@test.com",
        "password": "pw123456", "role": "tenant",
    })
    assert created.status_code == 201
    ok = client.post("/login", json={"email": "pytest@test.com", "password": "pw123456"})
    assert ok.status_code == 200
    assert ok.get_json()["role"] == "tenant"


def test_login_wrong_password(client):
    res = client.post("/login", json={"email": "pytest@test.com", "password": "nope"})
    assert res.status_code == 401


def test_missing_fields_returns_400(client):
    res = client.post("/users", json={"name": "no other fields"})
    assert res.status_code == 400
    assert "missing" in res.get_json()["error"]


def test_duplicate_email_returns_409(client):
    res = client.post("/users", json={
        "building_id": 1, "name": "Dupe", "email": "adiallo@citymail.cuny.edu",
        "password": "x", "role": "tenant",
    })
    assert res.status_code == 409


def test_booking_triggers_machine_status(client):
    created = client.post("/bookings", json={
        "user_id": 1, "machine_id": 2,
        "start_time": "2026-07-09 08:00:00", "end_time": "2026-07-09 08:30:00",
        "price_at_booking": 2.00,
    })
    assert created.status_code == 201
    booking_id = created.get_json()["booking_id"]

    machines = client.get("/machines?building_id=1").get_json()
    m2 = next(m for m in machines if m["machine_id"] == 2)
    assert m2["status"] == "in_use"

    cancelled = client.delete(f"/bookings/{booking_id}")
    assert cancelled.status_code == 200

    machines = client.get("/machines?building_id=1").get_json()
    m2 = next(m for m in machines if m["machine_id"] == 2)
    assert m2["status"] == "available"


def test_booking_payment_splits_fee(client):
    res = client.post("/booking-payments", json={
        "booking_id": 1, "gross_amount": 2.50,
    })
    assert res.status_code == 201
    body = res.get_json()
    # 15% of 2.50 = 0.375 -> 0.38 fee, 2.12 to building
    assert body["transaction_fee"] == 0.38
    assert body["building_amount"] == 2.12


def test_plans_and_subscriptions(client):
    plans = client.get("/plans").get_json()
    assert len(plans) == 3
    subs = client.get("/subscriptions").get_json()
    assert len(subs) == 3


def test_revenue_report_has_both_streams(client):
    rows = client.get("/reports/revenue").get_json()
    assert len(rows) == 3
    assert "booking_revenue" in rows[0]
    assert "subscription_revenue" in rows[0]


def test_excel_export(client):
    res = client.get("/reports/revenue/export")
    assert res.status_code == 200
    assert "spreadsheet" in res.headers["Content-Type"]
