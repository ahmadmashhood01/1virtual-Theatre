from __future__ import annotations

import os
import re
import sqlite3
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, render_template, request

from seed_data import (
    SEED_ORDER_CONCESSIONS,
    SEED_ORDER_SOURCE,
    SEED_CUSTOMERS,
    SEED_CONCESSIONS,
    SEED_DEPARTMENT,
    SEED_EMPLOYEES,
    SEED_FILMS,
    SEED_SHOWINGS,
    SEED_SHIFTS,
    SEED_SUPERVISORS,
    SEED_THEATRES,
    SEED_TICKETS,
    compute_order_totals,
    create_tables_sql,
    drop_all_sql,
    REWARDS_DISCOUNT_RATE,
    TICKET_UNIT_PRICE,
)

BASE_DIR = Path(__file__).resolve().parent
APP_DIR = BASE_DIR / "app"
DB_PATH = Path("/tmp/movie_theater.db") if os.getenv("VERCEL") else APP_DIR / "movie_theater.db"

SCHEMA_VERSION = 2

app = Flask(
    __name__,
    template_folder=str(APP_DIR / "templates"),
    static_folder=str(APP_DIR / "static"),
    static_url_path="/static",
)


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def table_count(conn: sqlite3.Connection, table_name: str) -> int:
    return int(conn.execute(f"SELECT COUNT(*) AS count FROM {table_name}").fetchone()["count"])


def _apply_schema_and_seed(conn: sqlite3.Connection) -> None:
    conn.executescript(create_tables_sql())
    conn.executescript(SEED_DEPARTMENT)
    conn.executescript(SEED_SUPERVISORS)
    conn.executescript(SEED_EMPLOYEES)
    conn.executescript(SEED_CUSTOMERS)
    conn.executescript(SEED_THEATRES)
    conn.executescript(SEED_FILMS)
    conn.executescript(SEED_CONCESSIONS)
    conn.executescript(SEED_SHOWINGS)
    created_ts = "2026-04-17T18:00:00"
    for order_num, cust_id, subtotal, discount in SEED_ORDER_SOURCE:
        tax, total = compute_order_totals(subtotal, discount)
        conn.execute(
            """
            INSERT INTO orders (order_number, order_customer_id, subtotal, tax, discount, total, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (order_num, cust_id, subtotal, tax, discount, total, created_ts),
        )
    conn.executescript(SEED_TICKETS)
    conn.executescript(SEED_ORDER_CONCESSIONS)
    conn.executescript(SEED_SHIFTS)
    conn.commit()


def init_db() -> None:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    with get_connection() as conn:
        current = conn.execute("PRAGMA user_version").fetchone()[0]
        if current < SCHEMA_VERSION:
            conn.executescript(drop_all_sql())
            _apply_schema_and_seed(conn)
            conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
            conn.commit()
        else:
            conn.executescript(create_tables_sql())
            conn.commit()


def next_customer_id(conn: sqlite3.Connection) -> str:
    rows = conn.execute("SELECT customer_id FROM customers").fetchall()
    max_n = 0
    for row in rows:
        m = re.match(r"^C(\d+)$", row["customer_id"] or "")
        if m:
            max_n = max(max_n, int(m.group(1)))
    return f"C{max_n + 1:03d}"


def parse_customer_name(full: str) -> tuple[str, str]:
    full = (full or "").strip()
    if not full:
        return "Guest", "Customer"
    parts = full.split(None, 1)
    if len(parts) == 1:
        return parts[0], "Customer"
    return parts[0], parts[1]


@app.get("/")
def index():
    return render_template("index.html", page="dashboard", title="Dashboard")


@app.get("/order")
def order_page():
    return render_template("order.html", page="order", title="New order")


@app.get("/customers")
def customers_page():
    return render_template("customers.html", page="customers", title="Customers")


@app.get("/data")
def data_page():
    return render_template("explorer.html", page="data", title="Data explorer")


@app.get("/receipt/<int:order_number>")
def receipt_page(order_number: int):
    with get_connection() as conn:
        order = conn.execute(
            """
            SELECT o.*, c.firstname, c.lastname, c.email, c.rewards_member
            FROM orders o
            JOIN customers c ON c.customer_id = o.order_customer_id
            WHERE o.order_number = ?
            """,
            (order_number,),
        ).fetchone()
        if order is None:
            return render_template(
                "receipt_not_found.html", order_number=order_number, page="", title="Receipt"
            ), 404
        ticket_rows = conn.execute(
            """
            SELECT t.ticket_showing_id, f.film_title, s.film_showing_datetime, COUNT(*) AS qty
            FROM tickets t
            JOIN showings s ON s.showing_id = t.ticket_showing_id
            JOIN films f ON f.film_id = s.film_id
            WHERE t.ticket_order_number = ?
            GROUP BY t.ticket_showing_id, f.film_title, s.film_showing_datetime
            """,
            (order_number,),
        ).fetchall()
        con_rows = conn.execute(
            """
            SELECT oc.quantity, c.concession_name, c.concession_size, c.concession_price
            FROM order_concessions oc
            JOIN concessions c ON c.concession_id = oc.concession_id
            WHERE oc.order_number = ?
            """,
            (order_number,),
        ).fetchall()
    customer_name = f"{order['firstname']} {order['lastname']}"
    items: list[dict] = []
    for tr in ticket_rows:
        qty = int(tr["qty"])
        unit = TICKET_UNIT_PRICE
        items.append(
            {
                "label": f"Tickets — {tr['film_title']}",
                "detail": tr["film_showing_datetime"],
                "qty": qty,
                "unit": unit,
                "line": round(qty * unit, 2),
            }
        )
    for cr in con_rows:
        q = int(cr["quantity"])
        p = float(cr["concession_price"])
        line = round(q * p, 2)
        label = f"{cr['concession_name']} ({cr['concession_size'] or '—'})"
        items.append(
            {
                "label": label,
                "detail": "Concession",
                "qty": q,
                "unit": p,
                "line": line,
            }
        )
    return render_template(
        "receipt.html",
        order=dict(order),
        customer_name=customer_name,
        customer_email=order["email"],
        rewards_member=bool(order["rewards_member"]),
        items=items,
    )


@app.get("/api/dashboard")
def dashboard_data():
    with get_connection() as conn:
        summary = conn.execute(
            """
            SELECT
                (SELECT COUNT(*) FROM films) AS total_films,
                (SELECT COUNT(*) FROM showings) AS active_showings,
                (SELECT COUNT(*) FROM theatres WHERE status = 1) AS open_theatres,
                COALESCE((SELECT ROUND(SUM(total), 2) FROM orders), 0) AS total_revenue
            """
        ).fetchone()

        showings = conn.execute(
            """
            SELECT s.showing_id, f.film_title, s.film_theatre_number, s.film_showing_datetime, s.film_available_seats
            FROM showings s
            JOIN films f ON f.film_id = s.film_id
            ORDER BY datetime(s.film_showing_datetime) ASC
            """
        ).fetchall()

        recent_orders = conn.execute(
            """
            SELECT
                o.order_number,
                c.firstname || ' ' || c.lastname AS customer_name,
                o.total,
                o.discount,
                o.subtotal,
                o.tax,
                o.created_at,
                COUNT(t.ticket_id) AS ticket_count
            FROM orders o
            JOIN customers c ON c.customer_id = o.order_customer_id
            LEFT JOIN tickets t ON t.ticket_order_number = o.order_number
            GROUP BY o.order_number, customer_name, o.total, o.discount, o.subtotal, o.tax, o.created_at
            ORDER BY datetime(o.created_at) DESC
            LIMIT 12
            """
        ).fetchall()

        return jsonify(
            {
                "summary": dict(summary),
                "showings": [dict(row) for row in showings],
                "recentOrders": [dict(row) for row in recent_orders],
            }
        )


@app.get("/api/admin-overview")
def admin_overview():
    with get_connection() as conn:
        customers = conn.execute(
            """
            SELECT customer_id, firstname, lastname, email, phone, home_city, rewards_member, pref_pymt_method
            FROM customers
            ORDER BY customer_id
            """
        ).fetchall()

        employees = conn.execute(
            """
            SELECT e.employee_id, e.firstname, e.lastname, e.job_title, e.status, d.department_name
            FROM employees e
            JOIN department_lookup d ON d.department_id = e.department_id
            ORDER BY e.employee_id
            """
        ).fetchall()

        shifts = conn.execute(
            """
            SELECT s.shift_id, e.firstname || ' ' || e.lastname AS employee_name, d.department_name,
                   s.showing_id, s.shift_start_datetime, s.shift_end_datetime
            FROM shifts s
            JOIN employees e ON e.employee_id = s.employee_id
            LEFT JOIN department_lookup d ON d.department_id = s.shift_department_id
            ORDER BY datetime(s.shift_start_datetime) DESC
            """
        ).fetchall()

        films = conn.execute(
            """
            SELECT film_id, film_title, film_rating, film_length_minutes, film_language, film_last_showing_date
            FROM films
            ORDER BY film_id
            """
        ).fetchall()

        theatres = conn.execute(
            """
            SELECT theatre_number, theatre_seat_count, accessible_seating, status, status_notes
            FROM theatres
            ORDER BY theatre_number
            """
        ).fetchall()

        showings = conn.execute(
            """
            SELECT s.showing_id, f.film_title, s.film_theatre_number, s.film_showing_datetime, s.film_available_seats
            FROM showings s
            JOIN films f ON f.film_id = s.film_id
            ORDER BY datetime(s.film_showing_datetime)
            """
        ).fetchall()

        orders = conn.execute(
            """
            SELECT o.order_number, c.firstname || ' ' || c.lastname AS customer_name,
                   o.subtotal, o.tax, o.discount, o.total, o.created_at
            FROM orders o
            JOIN customers c ON c.customer_id = o.order_customer_id
            ORDER BY datetime(o.created_at) DESC
            """
        ).fetchall()

        tickets = conn.execute(
            """
            SELECT t.ticket_id, t.ticket_order_number, c.firstname || ' ' || c.lastname AS customer_name,
                   f.film_title, s.film_showing_datetime
            FROM tickets t
            JOIN customers c ON c.customer_id = t.ticket_customer_id
            JOIN showings s ON s.showing_id = t.ticket_showing_id
            JOIN films f ON f.film_id = s.film_id
            ORDER BY t.ticket_id DESC
            """
        ).fetchall()

        concessions = conn.execute(
            """
            SELECT concession_id, concession_name, concession_size, concession_type, concession_price
            FROM concessions
            ORDER BY concession_name
            """
        ).fetchall()

        top_films = conn.execute(
            """
            SELECT f.film_title, COUNT(t.ticket_id) AS tickets_sold
            FROM tickets t
            JOIN showings s ON s.showing_id = t.ticket_showing_id
            JOIN films f ON f.film_id = s.film_id
            GROUP BY f.film_id, f.film_title
            ORDER BY tickets_sold DESC, f.film_title
            """
        ).fetchall()

        concessions_sales = conn.execute(
            """
            SELECT c.concession_name, c.concession_size, COALESCE(SUM(oc.quantity), 0) AS units_sold
            FROM concessions c
            LEFT JOIN order_concessions oc ON oc.concession_id = c.concession_id
            GROUP BY c.concession_id, c.concession_name, c.concession_size
            ORDER BY units_sold DESC, c.concession_name
            """
        ).fetchall()

        return jsonify(
            {
                "customers": [dict(row) for row in customers],
                "employees": [dict(row) for row in employees],
                "shifts": [dict(row) for row in shifts],
                "films": [dict(row) for row in films],
                "theatres": [dict(row) for row in theatres],
                "showings": [dict(row) for row in showings],
                "orders": [dict(row) for row in orders],
                "tickets": [dict(row) for row in tickets],
                "concessions": [dict(row) for row in concessions],
                "topFilms": [dict(row) for row in top_films],
                "concessionSales": [dict(row) for row in concessions_sales],
            }
        )


@app.get("/api/customers")
def list_customers_api():
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT customer_id, firstname, lastname, email, rewards_member
            FROM customers
            ORDER BY firstname, lastname
            """
        ).fetchall()
        return jsonify([dict(r) for r in rows])


@app.post("/api/customers")
def create_customer():
    payload = request.get_json(silent=True) or {}
    name = (payload.get("name") or "").strip()
    first = (payload.get("firstName") or "").strip()
    last = (payload.get("lastName") or "").strip()
    if first or last:
        firstname = first or "Guest"
        lastname = last or "Customer"
    else:
        firstname, lastname = parse_customer_name(name)
    email = (payload.get("email") or "").strip()
    rewards = bool(payload.get("rewardsMember", False))
    if not email:
        return jsonify({"error": "Email is required."}), 400

    with get_connection() as conn:
        dupe = conn.execute("SELECT customer_id FROM customers WHERE lower(email) = lower(?)", (email,)).fetchone()
        if dupe:
            return jsonify({"error": "A customer with that email already exists.", "customerId": dupe["customer_id"]}), 409
        new_id = next_customer_id(conn)
        conn.execute(
            """
            INSERT INTO customers (customer_id, firstname, lastname, email, phone, age, gender, home_city, rewards_member, pref_pymt_method)
            VALUES (?, ?, ?, ?, NULL, NULL, NULL, NULL, ?, NULL)
            """,
            (new_id, firstname, lastname, email, 1 if rewards else 0),
        )
        conn.commit()
    return jsonify({"customerId": new_id, "firstname": firstname, "lastname": lastname, "email": email}), 201


@app.get("/api/booking-data")
def booking_data():
    with get_connection() as conn:
        customers = conn.execute(
            """
            SELECT customer_id, firstname || ' ' || lastname AS full_name
            FROM customers
            ORDER BY firstname, lastname
            """
        ).fetchall()
        showings = conn.execute(
            """
            SELECT s.showing_id, f.film_title, s.film_theatre_number, s.film_showing_datetime, s.film_available_seats
            FROM showings s
            JOIN films f ON f.film_id = s.film_id
            ORDER BY datetime(s.film_showing_datetime)
            """
        ).fetchall()
        concessions = conn.execute(
            """
            SELECT concession_id, concession_name, concession_size, concession_price
            FROM concessions
            ORDER BY concession_name, concession_size
            """
        ).fetchall()
        return jsonify(
            {
                "customers": [dict(row) for row in customers],
                "showings": [dict(row) for row in showings],
                "concessions": [dict(row) for row in concessions],
            }
        )


@app.post("/api/orders")
def create_order():
    payload = request.get_json(silent=True) or {}
    customer_id = payload.get("customerId")
    concessions_payload = payload.get("concessions", [])

    try:
        showing_id = int(payload.get("showingId", 0))
        ticket_qty = int(payload.get("ticketQty", 0))
    except (TypeError, ValueError):
        return jsonify({"error": "Showing and ticket quantity must be valid numbers."}), 400

    if not customer_id:
        return jsonify({"error": "Customer is required."}), 400
    if showing_id <= 0 or ticket_qty <= 0:
        return jsonify({"error": "Showing and ticket quantity are required."}), 400

    with get_connection() as conn:
        customer = conn.execute(
            "SELECT customer_id, rewards_member FROM customers WHERE customer_id = ?",
            (customer_id,),
        ).fetchone()
        if customer is None:
            return jsonify({"error": "Customer not found."}), 404
        is_rewards = int(customer["rewards_member"] or 0) == 1

        showing = conn.execute(
            "SELECT showing_id, film_available_seats FROM showings WHERE showing_id = ?",
            (showing_id,),
        ).fetchone()
        if showing is None:
            return jsonify({"error": "Showing not found."}), 404
        if showing["film_available_seats"] < ticket_qty:
            return jsonify({"error": "Not enough seats available for this showing."}), 400

        ticket_line = ticket_qty * TICKET_UNIT_PRICE
        concession_subtotal = 0.0
        cleaned: list[tuple[str, int, float]] = []
        for item in concessions_payload:
            cid = item.get("id")
            if not cid:
                continue
            try:
                qty = int(item.get("qty", 0))
            except (TypeError, ValueError):
                continue
            if qty <= 0:
                continue
            rowc = conn.execute("SELECT concession_price FROM concessions WHERE concession_id = ?", (cid,)).fetchone()
            if rowc is None:
                continue
            price = float(rowc["concession_price"])
            concession_subtotal += price * qty
            cleaned.append((cid, qty, price))

        subtotal = round(ticket_line + concession_subtotal, 2)
        discount = round(subtotal * REWARDS_DISCOUNT_RATE, 2) if is_rewards else 0.0
        tax, total = compute_order_totals(subtotal, discount)
        now = datetime.now().isoformat()

        cur = conn.execute(
            """
            INSERT INTO orders (order_customer_id, subtotal, tax, discount, total, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (customer_id, subtotal, tax, discount, total, now),
        )
        order_number = int(cur.lastrowid)

        conn.executemany(
            """
            INSERT INTO tickets (ticket_customer_id, ticket_showing_id, ticket_order_number)
            VALUES (?, ?, ?)
            """,
            [(customer_id, showing_id, order_number) for _ in range(ticket_qty)],
        )
        for cid, qty, _ in cleaned:
            conn.execute(
                """
                INSERT INTO order_concessions (order_number, concession_id, quantity)
                VALUES (?, ?, ?)
                """,
                (order_number, cid, qty),
            )
        conn.execute(
            "UPDATE showings SET film_available_seats = film_available_seats - ? WHERE showing_id = ?",
            (ticket_qty, showing_id),
        )
        conn.commit()

    receipt_path = f"/receipt/{order_number}"
    return (
        jsonify(
            {
                "orderNumber": order_number,
                "subtotal": subtotal,
                "tax": tax,
                "discount": discount,
                "total": total,
                "rewardsDiscountApplied": is_rewards,
                "receiptUrl": receipt_path,
            }
        ),
        201,
    )


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
