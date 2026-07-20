"""WashWise / LaundryApp — Flask REST API.

Raw SQL only (mysql-connector-python), no ORM.
All queries are parameterized to prevent SQL injection.
"""

from io import BytesIO

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from werkzeug.security import check_password_hash, generate_password_hash
from mysql.connector import Error as MySQLError

import db

app = Flask(__name__)
CORS(app)  # allow requests from the frontend

DEFAULT_FEE_RATE = 0.15  # app keeps 15% of a booking as its transaction fee


@app.get("/")
def index():
    """API root — basic service info."""
    return jsonify(service="WashWise API", status="running", health="/health")


class ApiError(Exception):
    """Raised for client errors; converted to a JSON response."""

    def __init__(self, status, message):
        super().__init__(message)
        self.status = status
        self.message = message


@app.errorhandler(ApiError)
def _handle_api_error(exc):
    return jsonify(error=exc.message), exc.status


@app.errorhandler(MySQLError)
def _handle_db_error(exc):
    if getattr(exc, "errno", None) == 1062:
        return jsonify(error="that value already exists (duplicate)"), 409
    if getattr(exc, "errno", None) == 1452:
        return jsonify(error="referenced record does not exist"), 400
    return jsonify(error="database error", detail=str(exc)), 400


def get_body():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ApiError(400, "request body must be a JSON object")
    return data


def require(data, *fields):
    missing = [f for f in fields if data.get(f) in (None, "")]
    if missing:
        raise ApiError(400, "missing required field(s): " + ", ".join(missing))


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------
@app.get("/health")
def health():
    try:
        db.query("SELECT 1 AS ok", fetchone=True)
        return jsonify(status="ok", database="connected")
    except Exception as exc:  # noqa: BLE001
        return jsonify(status="error", detail=str(exc)), 500


# ---------------------------------------------------------------------------
# Buildings
# ---------------------------------------------------------------------------
@app.get("/buildings")
def list_buildings():
    return jsonify(db.query("SELECT * FROM buildings ORDER BY building_id"))


@app.post("/buildings")
def create_building():
    data = get_body()
    require(data, "name", "address")
    result = db.execute(
        "INSERT INTO buildings (name, address) VALUES (%s, %s)",
        (data["name"], data["address"]),
    )
    return jsonify(building_id=result["lastrowid"]), 201


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------
@app.get("/users")
def list_users():
    return jsonify(
        db.query(
            "SELECT user_id, building_id, name, email, role, created_at "
            "FROM users ORDER BY user_id"
        )
    )


@app.post("/users")
def create_user():
    data = get_body()
    require(data, "building_id", "name", "email", "password", "role")
    password_hash = generate_password_hash(data["password"])
    result = db.execute(
        "INSERT INTO users (building_id, name, email, password_hash, role) "
        "VALUES (%s, %s, %s, %s, %s)",
        (data["building_id"], data["name"], data["email"], password_hash, data["role"]),
    )
    return jsonify(user_id=result["lastrowid"]), 201


@app.post("/login")
def login():
    data = get_body()
    require(data, "email", "password")
    user = db.query(
        "SELECT user_id, name, email, role, password_hash FROM users WHERE email = %s",
        (data["email"],),
        fetchone=True,
    )
    if not user or not check_password_hash(user["password_hash"], data["password"]):
        return jsonify(error="invalid email or password"), 401
    return jsonify(
        user_id=user["user_id"], name=user["name"],
        email=user["email"], role=user["role"],
    )


@app.get("/users/<int:user_id>/bookings")
def user_bookings(user_id):
    return jsonify(
        db.query(
            "SELECT b.booking_id, m.machine_id, m.machine_number, m.machine_type, "
            "b.start_time, b.end_time, b.price_at_booking, b.booking_status "
            "FROM bookings b "
            "JOIN machines m ON b.machine_id = m.machine_id "
            "WHERE b.user_id = %s "
            "ORDER BY b.start_time DESC",
            (user_id,),
        )
    )


# ---------------------------------------------------------------------------
# Machines
# ---------------------------------------------------------------------------
@app.get("/machines")
def list_machines():
    clauses = []
    params = []
    building_id = request.args.get("building_id")
    status = request.args.get("status")
    if building_id:
        clauses.append("building_id = %s")
        params.append(building_id)
    if status:
        clauses.append("status = %s")
        params.append(status)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    return jsonify(
        db.query(f"SELECT * FROM machines {where} ORDER BY machine_id", params)
    )


@app.post("/machines")
def create_machine():
    data = get_body()
    require(data, "building_id", "machine_number", "machine_type",
            "cost_per_cycle", "duration_minutes")
    result = db.execute(
        "INSERT INTO machines "
        "(building_id, machine_number, machine_type, cost_per_cycle, "
        "duration_minutes, status) VALUES (%s, %s, %s, %s, %s, %s)",
        (
            data["building_id"], data["machine_number"], data["machine_type"],
            data["cost_per_cycle"], data["duration_minutes"],
            data.get("status", "available"),
        ),
    )
    return jsonify(machine_id=result["lastrowid"]), 201


@app.patch("/machines/<int:machine_id>")
def update_machine_status(machine_id):
    data = get_body()
    require(data, "status")
    allowed = {"available", "in_use", "out_of_order"}
    if data["status"] not in allowed:
        raise ApiError(400, "status must be one of: " + ", ".join(sorted(allowed)))
    result = db.execute(
        "UPDATE machines SET status = %s WHERE machine_id = %s",
        (data["status"], machine_id),
    )
    if result["rowcount"] == 0:
        exists = db.query("SELECT 1 FROM machines WHERE machine_id = %s",
                          (machine_id,), fetchone=True)
        if not exists:
            return jsonify(error="machine not found"), 404
    return jsonify(machine_id=machine_id, status=data["status"])


# ---------------------------------------------------------------------------
# Subscription plans
# ---------------------------------------------------------------------------
@app.get("/plans")
def list_plans():
    return jsonify(db.query("SELECT * FROM subscription_plans ORDER BY plan_id"))


@app.post("/plans")
def create_plan():
    data = get_body()
    require(data, "plan_name", "billing_period", "subscription_price",
            "max_machines", "analytics_level")
    result = db.execute(
        "INSERT INTO subscription_plans "
        "(plan_name, billing_period, subscription_price, max_machines, analytics_level) "
        "VALUES (%s, %s, %s, %s, %s)",
        (
            data["plan_name"], data["billing_period"], data["subscription_price"],
            data["max_machines"], data["analytics_level"],
        ),
    )
    return jsonify(plan_id=result["lastrowid"]), 201


# ---------------------------------------------------------------------------
# Building subscriptions
# ---------------------------------------------------------------------------
@app.get("/subscriptions")
def list_subscriptions():
    return jsonify(
        db.query(
            "SELECT bs.subscription_id, bl.name AS building, p.plan_name, "
            "p.subscription_price, bs.start_date, bs.end_date, bs.subscription_status "
            "FROM building_subscriptions bs "
            "JOIN buildings bl ON bs.building_id = bl.building_id "
            "JOIN subscription_plans p ON bs.plan_id = p.plan_id "
            "ORDER BY bs.subscription_id"
        )
    )


@app.post("/subscriptions")
def create_subscription():
    data = get_body()
    require(data, "building_id", "plan_id", "start_date")
    result = db.execute(
        "INSERT INTO building_subscriptions "
        "(building_id, plan_id, start_date, end_date, subscription_status) "
        "VALUES (%s, %s, %s, %s, %s)",
        (
            data["building_id"], data["plan_id"], data["start_date"],
            data.get("end_date"), data.get("subscription_status", "active"),
        ),
    )
    return jsonify(subscription_id=result["lastrowid"]), 201


# ---------------------------------------------------------------------------
# Bookings (junction table)
# ---------------------------------------------------------------------------
@app.get("/bookings")
def list_bookings():
    return jsonify(
        db.query(
            "SELECT b.booking_id, u.name AS tenant, m.machine_type, "
            "b.start_time, b.end_time, b.price_at_booking, b.booking_status "
            "FROM bookings b "
            "JOIN users u ON b.user_id = u.user_id "
            "JOIN machines m ON b.machine_id = m.machine_id "
            "ORDER BY b.booking_id"
        )
    )


@app.post("/bookings")
def create_booking():
    """Create a booking via the sp_book_machine stored procedure.

    The AFTER INSERT trigger flips the machine to 'in_use'.
    """
    data = get_body()
    require(data, "user_id", "machine_id", "start_time", "end_time", "price_at_booking")

    conflict = db.query(
        "SELECT booking_id FROM bookings "
        "WHERE machine_id = %s AND booking_status = 'confirmed' "
        "AND start_time < %s AND end_time > %s",
        (data["machine_id"], data["end_time"], data["start_time"]),
        fetchone=True,
    )
    if conflict:
        raise ApiError(409, "machine already booked for that time")

    rows = db.call_procedure(
        "sp_book_machine",
        (
            data["user_id"], data["machine_id"], data["start_time"],
            data["end_time"], data["price_at_booking"],
        ),
    )
    booking_id = rows[0]["booking_id"] if rows else None
    return jsonify(booking_id=booking_id), 201


@app.delete("/bookings/<int:booking_id>")
def cancel_booking(booking_id):
    result = db.execute(
        "UPDATE bookings SET booking_status = 'cancelled' WHERE booking_id = %s",
        (booking_id,),
    )
    if result["rowcount"] == 0:
        return jsonify(error="booking not found"), 404
    return jsonify(booking_id=booking_id, booking_status="cancelled")


@app.get("/bookings/<int:booking_id>")
def get_booking(booking_id):
    row = db.query(
        "SELECT b.booking_id, u.name AS tenant, u.email AS tenant_email, "
        "bl.name AS building, m.machine_id, m.machine_number, m.machine_type, "
        "b.start_time, b.end_time, b.price_at_booking, b.booking_status "
        "FROM bookings b "
        "JOIN users u ON b.user_id = u.user_id "
        "JOIN machines m ON b.machine_id = m.machine_id "
        "JOIN buildings bl ON m.building_id = bl.building_id "
        "WHERE b.booking_id = %s",
        (booking_id,),
        fetchone=True,
    )
    if not row:
        return jsonify(error="booking not found"), 404
    return jsonify(row)


# ---------------------------------------------------------------------------
# Booking payments (tenant pays; app keeps a transaction fee)
# ---------------------------------------------------------------------------
@app.post("/booking-payments")
def create_booking_payment():
    data = get_body()
    require(data, "booking_id", "gross_amount")
    gross = float(data["gross_amount"])
    if gross <= 0:
        raise ApiError(400, "gross_amount must be positive")
    rate = float(data.get("transaction_fee_rate", DEFAULT_FEE_RATE))
    fee = round(gross * rate, 2)
    building_amount = round(gross - fee, 2)
    result = db.execute(
        "INSERT INTO booking_payments "
        "(booking_id, gross_amount, transaction_fee_rate, transaction_fee, "
        "building_amount, payment_status, payment_date) "
        "VALUES (%s, %s, %s, %s, %s, %s, NOW())",
        (data["booking_id"], gross, rate, fee, building_amount,
         data.get("payment_status", "paid")),
    )
    return jsonify(payment_id=result["lastrowid"], transaction_fee=fee,
                   building_amount=building_amount), 201


# ---------------------------------------------------------------------------
# Subscription payments (building pays the app its SaaS fee)
# ---------------------------------------------------------------------------
@app.post("/subscription-payments")
def create_subscription_payment():
    data = get_body()
    require(data, "subscription_id", "amount", "billing_period_start",
            "billing_period_end")
    result = db.execute(
        "INSERT INTO subscription_payments "
        "(subscription_id, amount, payment_status, payment_date, "
        "billing_period_start, billing_period_end) "
        "VALUES (%s, %s, %s, NOW(), %s, %s)",
        (
            data["subscription_id"], data["amount"],
            data.get("payment_status", "paid"),
            data["billing_period_start"], data["billing_period_end"],
        ),
    )
    return jsonify(subscription_payment_id=result["lastrowid"]), 201


# ---------------------------------------------------------------------------
# Revenue report + Excel export (both streams)
# ---------------------------------------------------------------------------
@app.get("/reports/revenue")
def revenue_report():
    return jsonify(db.call_procedure("sp_revenue_report"))


@app.get("/reports/revenue/export")
def revenue_export():
    """One-click Excel export of the revenue report (both streams)."""
    from openpyxl import Workbook

    rows = db.call_procedure("sp_revenue_report")

    wb = Workbook()
    ws = wb.active
    ws.title = "Revenue"
    ws.append(["Building", "Booking Fees", "Subscription Revenue", "Total"])
    for r in rows:
        booking = float(r["booking_revenue"])
        subscription = float(r["subscription_revenue"])
        ws.append([r["building"], booking, subscription, booking + subscription])

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        download_name="revenue_report.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


if __name__ == "__main__":
    # Port 5001 (macOS AirPlay Receiver occupies 5000).
    app.run(debug=True, port=5001)
