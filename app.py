from __future__ import annotations

import os
import sqlite3
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, render_template, request

BASE_DIR = Path(__file__).resolve().parent
APP_DIR = BASE_DIR / "app"
DB_PATH = Path("/tmp/movie_theater.db") if os.getenv("VERCEL") else APP_DIR / "movie_theater.db"
TICKET_PRICE = 12.0

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


def init_db() -> None:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS department_lookup (
                department_id INTEGER PRIMARY KEY,
                department_name TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS supervisors (
                supervisor_id INTEGER PRIMARY KEY,
                firstname TEXT NOT NULL,
                lastname TEXT NOT NULL,
                department_id INTEGER NOT NULL,
                FOREIGN KEY (department_id) REFERENCES department_lookup(department_id)
            );

            CREATE TABLE IF NOT EXISTS employees (
                employee_id TEXT PRIMARY KEY,
                firstname TEXT NOT NULL,
                lastname TEXT NOT NULL,
                email TEXT NOT NULL,
                job_title TEXT NOT NULL,
                status TEXT NOT NULL,
                supervisor_id INTEGER,
                department_id INTEGER NOT NULL,
                FOREIGN KEY (supervisor_id) REFERENCES supervisors(supervisor_id),
                FOREIGN KEY (department_id) REFERENCES department_lookup(department_id)
            );

            CREATE TABLE IF NOT EXISTS customers (
                customer_id TEXT PRIMARY KEY,
                firstname TEXT NOT NULL,
                lastname TEXT NOT NULL,
                email TEXT NOT NULL,
                pref_pymt_method TEXT,
                rewards_member INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS theatres (
                theatre_number INTEGER PRIMARY KEY,
                theatre_seat_count INTEGER NOT NULL,
                accessible_seating INTEGER NOT NULL DEFAULT 0,
                status INTEGER NOT NULL DEFAULT 1,
                status_notes TEXT
            );

            CREATE TABLE IF NOT EXISTS films (
                film_id INTEGER PRIMARY KEY,
                film_title TEXT NOT NULL,
                film_rating TEXT NOT NULL,
                film_length_minutes INTEGER NOT NULL,
                film_language TEXT NOT NULL DEFAULT 'English',
                film_last_showing_date TEXT
            );

            CREATE TABLE IF NOT EXISTS showings (
                showing_id INTEGER PRIMARY KEY,
                film_id INTEGER NOT NULL,
                film_theatre_number INTEGER NOT NULL,
                film_showing_datetime TEXT NOT NULL,
                film_available_seats INTEGER NOT NULL,
                FOREIGN KEY (film_id) REFERENCES films (film_id),
                FOREIGN KEY (film_theatre_number) REFERENCES theatres (theatre_number)
            );

            CREATE TABLE IF NOT EXISTS orders (
                order_number INTEGER PRIMARY KEY AUTOINCREMENT,
                order_customer_id TEXT NOT NULL,
                order_total REAL NOT NULL DEFAULT 0.0,
                order_discount REAL NOT NULL DEFAULT 0.0,
                created_at TEXT NOT NULL,
                FOREIGN KEY (order_customer_id) REFERENCES customers (customer_id)
            );

            CREATE TABLE IF NOT EXISTS tickets (
                ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_customer_id TEXT NOT NULL,
                ticket_showing_id INTEGER NOT NULL,
                ticket_order_number INTEGER NOT NULL,
                FOREIGN KEY (ticket_customer_id) REFERENCES customers (customer_id),
                FOREIGN KEY (ticket_showing_id) REFERENCES showings (showing_id),
                FOREIGN KEY (ticket_order_number) REFERENCES orders (order_number)
            );

            CREATE TABLE IF NOT EXISTS shifts (
                shift_id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id TEXT NOT NULL,
                showing_id INTEGER,
                shift_start_datetime TEXT NOT NULL,
                shift_end_datetime TEXT NOT NULL,
                shift_department_id INTEGER,
                FOREIGN KEY (employee_id) REFERENCES employees(employee_id),
                FOREIGN KEY (showing_id) REFERENCES showings(showing_id),
                FOREIGN KEY (shift_department_id) REFERENCES department_lookup(department_id)
            );

            CREATE TABLE IF NOT EXISTS concessions (
                concession_id TEXT PRIMARY KEY,
                concession_name TEXT NOT NULL,
                concession_size TEXT,
                concession_type TEXT,
                concession_price REAL NOT NULL,
                stock INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS order_concessions (
                order_number INTEGER NOT NULL,
                concession_id TEXT NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 1,
                PRIMARY KEY (order_number, concession_id),
                FOREIGN KEY (order_number) REFERENCES orders (order_number),
                FOREIGN KEY (concession_id) REFERENCES concessions (concession_id)
            );
            """
        )

        if table_count(conn, "department_lookup") == 0:
            conn.executescript(
                """
                INSERT INTO department_lookup (department_id, department_name) VALUES
                (1, 'Box Office'),
                (2, 'Concessions'),
                (3, 'Cleaning'),
                (4, 'Projection'),
                (5, 'Management');
                """
            )

        if table_count(conn, "supervisors") == 0:
            conn.executescript(
                """
                INSERT INTO supervisors (supervisor_id, firstname, lastname, department_id) VALUES
                (1, 'Patricia', 'Olsen', 5),
                (2, 'Marcus', 'Chen', 4),
                (3, 'Elena', 'Rodriguez', 2),
                (4, 'James', 'Whitaker', 1),
                (5, 'Sonya', 'Patel', 3);
                """
            )

        if table_count(conn, "employees") == 0:
            conn.executescript(
                """
                INSERT INTO employees (employee_id, firstname, lastname, email, job_title, status, supervisor_id, department_id) VALUES
                ('E01', 'Margo', 'Elia', 'margo.elia@mail.com', 'Usher', 'Full time', 4, 1),
                ('E02', 'Orso', 'Bernardetta', 'orso.bernardetta@mail.com', 'Custodian', 'Part time', 5, 3),
                ('E03', 'Teodora', 'De Luca', 'teodora.deluca@mail.com', 'Projection Assistant', 'Full time', 2, 4),
                ('E04', 'Lisandro', 'Agresta', 'lisandro.agresta@mail.com', 'Box Office Associate', 'Full time', 4, 1),
                ('E05', 'Mesut', 'Demirci', 'mesut.demirci@mail.com', 'Projectionist', 'Full time', 2, 4),
                ('E06', 'Enis', 'Terzi', 'enis.terzi@mail.com', 'Concessions Associate', 'Part time', 3, 2);
                """
            )

        if table_count(conn, "customers") == 0:
            conn.executescript(
                """
                INSERT INTO customers (customer_id, firstname, lastname, email, pref_pymt_method, rewards_member) VALUES
                ('C001', 'Ethan', 'Walker', 'ethan.walker@mail.com', 'Card', 1),
                ('C002', 'Olivia', 'Harris', 'olivia.harris@mail.com', 'Apple Pay', 0),
                ('C003', 'Noah', 'Clark', 'noah.clark@mail.com', 'Card', 1),
                ('C004', 'Ava', 'Lewis', 'ava.lewis@mail.com', 'Cash', 0),
                ('C005', 'Liam', 'Hall', 'liam.hall@mail.com', 'Card', 0);
                """
            )

        if table_count(conn, "theatres") == 0:
            conn.executescript(
                """
                INSERT INTO theatres (theatre_number, theatre_seat_count, accessible_seating, status, status_notes) VALUES
                (1, 40, 1, 1, NULL),
                (2, 40, 0, 0, 'Renovations scheduled for April-June'),
                (3, 40, 0, 1, NULL),
                (4, 56, 1, 1, NULL);
                """
            )

        if table_count(conn, "films") == 0:
            conn.executescript(
                """
                INSERT INTO films (film_id, film_title, film_rating, film_length_minutes, film_language, film_last_showing_date) VALUES
                (1, 'Dune: Part Three', 'PG-13', 165, 'English', '2026-04-20'),
                (2, 'Thunderbolts*', 'PG-13', 127, 'English', '2026-04-18'),
                (3, 'How to Train Your Dragon', 'PG', 126, 'English', '2026-04-22'),
                (4, 'Mission: Impossible - The Final Reckoning', 'PG-13', 169, 'English', '2026-04-23'),
                (5, 'Elio', 'PG', 98, 'English', '2026-04-17');
                """
            )

        if table_count(conn, "showings") == 0:
            conn.executescript(
                """
                INSERT INTO showings (showing_id, film_id, film_theatre_number, film_showing_datetime, film_available_seats) VALUES
                (1, 1, 1, '2026-04-15T18:00:00', 36),
                (2, 2, 3, '2026-04-15T19:30:00', 31),
                (3, 3, 4, '2026-04-15T20:10:00', 46),
                (4, 4, 1, '2026-04-16T17:40:00', 38),
                (5, 5, 3, '2026-04-16T21:00:00', 34);
                """
            )

        if table_count(conn, "concessions") == 0:
            conn.executescript(
                """
                INSERT INTO concessions (concession_id, concession_name, concession_size, concession_type, concession_price, stock) VALUES
                ('CN001', 'Popcorn', 'Regular', 'Snacks', 5.00, 150),
                ('CN002', 'Popcorn', 'Large', 'Snacks', 9.00, 100),
                ('CN004', 'Coke', 'Regular', 'Beverage', 3.00, 200),
                ('CN010', 'Pizza', 'Regular', 'Fast Food', 8.00, 80),
                ('CN013', 'Nachos', 'Regular', 'Snacks', 6.00, 90);
                """
            )

        if table_count(conn, "orders") == 0:
            now = datetime.now().isoformat()
            order_cursor = conn.execute(
                """
                INSERT INTO orders (order_customer_id, order_total, order_discount, created_at)
                VALUES (?, ?, ?, ?)
                """,
                ("C001", 30.0, 0.0, now),
            )
            order_no = int(order_cursor.lastrowid)
            conn.execute(
                """
                INSERT INTO tickets (ticket_customer_id, ticket_showing_id, ticket_order_number)
                VALUES
                ('C001', 1, ?),
                ('C001', 1, ?)
                """,
                (order_no, order_no),
            )
            conn.execute(
                "INSERT INTO order_concessions (order_number, concession_id, quantity) VALUES (?, ?, ?)",
                (order_no, "CN001", 1),
            )

        if table_count(conn, "shifts") == 0:
            conn.executescript(
                """
                INSERT INTO shifts (employee_id, showing_id, shift_start_datetime, shift_end_datetime, shift_department_id) VALUES
                ('E01', 1, '2026-04-15T17:30:00', '2026-04-15T22:30:00', 1),
                ('E03', 1, '2026-04-15T17:00:00', '2026-04-15T22:00:00', 4),
                ('E06', 2, '2026-04-15T18:30:00', '2026-04-15T23:00:00', 2),
                ('E02', NULL, '2026-04-15T16:00:00', '2026-04-15T21:00:00', 3);
                """
            )

        conn.commit()


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/dashboard")
def dashboard_data():
    with get_connection() as conn:
        summary = conn.execute(
            """
            SELECT
                (SELECT COUNT(*) FROM films) AS total_films,
                (SELECT COUNT(*) FROM showings) AS active_showings,
                (SELECT COUNT(*) FROM theatres WHERE status = 1) AS open_theatres,
                COALESCE((SELECT ROUND(SUM(order_total - order_discount), 2) FROM orders), 0) AS total_revenue
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
                o.order_total,
                o.order_discount,
                o.created_at,
                COUNT(t.ticket_id) AS ticket_count
            FROM orders o
            JOIN customers c ON c.customer_id = o.order_customer_id
            LEFT JOIN tickets t ON t.ticket_order_number = o.order_number
            GROUP BY o.order_number, customer_name, o.order_total, o.order_discount, o.created_at
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
            SELECT customer_id, firstname, lastname, email, pref_pymt_method, rewards_member
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
                   o.order_total, o.order_discount, o.created_at
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
            SELECT concession_id, concession_name, concession_size, concession_type, concession_price, stock
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
            SELECT concession_id, concession_name, concession_size, concession_price, stock
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
        customer = conn.execute("SELECT customer_id FROM customers WHERE customer_id = ?", (customer_id,)).fetchone()
        if customer is None:
            return jsonify({"error": "Customer not found."}), 404

        showing = conn.execute(
            "SELECT showing_id, film_available_seats FROM showings WHERE showing_id = ?",
            (showing_id,),
        ).fetchone()
        if showing is None:
            return jsonify({"error": "Showing not found."}), 404
        if showing["film_available_seats"] < ticket_qty:
            return jsonify({"error": "Not enough seats available for this showing."}), 400

        concession_total = 0.0
        cleaned_concessions: list[tuple[str, int, float]] = []
        for item in concessions_payload:
            concession_id = item.get("id")
            if not concession_id:
                continue
            try:
                qty = int(item.get("qty", 0))
            except (TypeError, ValueError):
                continue
            if qty <= 0:
                continue
            concession = conn.execute(
                "SELECT concession_price, stock FROM concessions WHERE concession_id = ?",
                (concession_id,),
            ).fetchone()
            if concession is None:
                continue
            if concession["stock"] < qty:
                return jsonify({"error": f"Not enough stock for concession {concession_id}."}), 400
            price = float(concession["concession_price"])
            concession_total += price * qty
            cleaned_concessions.append((concession_id, qty, price))

        ticket_total = ticket_qty * TICKET_PRICE
        order_total = round(ticket_total + concession_total, 2)
        now = datetime.now().isoformat()

        cursor = conn.execute(
            """
            INSERT INTO orders (order_customer_id, order_total, order_discount, created_at)
            VALUES (?, ?, 0, ?)
            """,
            (customer_id, order_total, now),
        )
        order_number = int(cursor.lastrowid)

        conn.executemany(
            """
            INSERT INTO tickets (ticket_customer_id, ticket_showing_id, ticket_order_number)
            VALUES (?, ?, ?)
            """,
            [(customer_id, showing_id, order_number) for _ in range(ticket_qty)],
        )
        for concession_id, qty, _ in cleaned_concessions:
            conn.execute(
                """
                INSERT INTO order_concessions (order_number, concession_id, quantity)
                VALUES (?, ?, ?)
                """,
                (order_number, concession_id, qty),
            )
            conn.execute(
                "UPDATE concessions SET stock = stock - ? WHERE concession_id = ?",
                (qty, concession_id),
            )

        conn.execute(
            """
            UPDATE showings
            SET film_available_seats = film_available_seats - ?
            WHERE showing_id = ?
            """,
            (ticket_qty, showing_id),
        )
        conn.commit()

    return jsonify({"orderNumber": order_number, "orderTotal": order_total}), 201


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
