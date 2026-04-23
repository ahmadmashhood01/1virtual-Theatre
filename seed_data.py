"""
Seed SQL fragments for cinema_final (SQLite) — imported by app init to keep app.py size manageable.
"""

# pylint: disable=line-too-long

TAX_RATE = 0.08
REWARDS_DISCOUNT_RATE = 0.10
TICKET_UNIT_PRICE = 12.0


def compute_order_totals(subtotal: float, discount: float) -> tuple[float, float]:
    tax = round(subtotal * TAX_RATE, 2)
    total = round(subtotal * 1.08 - discount, 2)
    return tax, total


def create_tables_sql() -> str:
    return """
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
                phone TEXT,
                age INTEGER,
                gender TEXT,
                home_city TEXT,
                rewards_member INTEGER NOT NULL DEFAULT 0,
                pref_pymt_method TEXT
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
                film_language TEXT NOT NULL,
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
                subtotal REAL NOT NULL DEFAULT 0.0,
                tax REAL NOT NULL DEFAULT 0.0,
                discount REAL NOT NULL DEFAULT 0.0,
                total REAL NOT NULL DEFAULT 0.0,
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
                shift_department_id INTEGER NOT NULL,
                FOREIGN KEY (employee_id) REFERENCES employees(employee_id),
                FOREIGN KEY (showing_id) REFERENCES showings (showing_id),
                FOREIGN KEY (shift_department_id) REFERENCES department_lookup(department_id)
            );

            CREATE TABLE IF NOT EXISTS concessions (
                concession_id TEXT PRIMARY KEY,
                concession_name TEXT NOT NULL,
                concession_size TEXT,
                concession_type TEXT,
                concession_price REAL NOT NULL
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


def drop_all_sql() -> str:
    return """
    PRAGMA foreign_keys = OFF;
    DROP TABLE IF EXISTS order_concessions;
    DROP TABLE IF EXISTS tickets;
    DROP TABLE IF EXISTS orders;
    DROP TABLE IF EXISTS shifts;
    DROP TABLE IF EXISTS showings;
    DROP TABLE IF EXISTS films;
    DROP TABLE IF EXISTS theatres;
    DROP TABLE IF EXISTS concessions;
    DROP TABLE IF EXISTS customers;
    DROP TABLE IF EXISTS employees;
    DROP TABLE IF EXISTS supervisors;
    DROP TABLE IF EXISTS department_lookup;
    PRAGMA foreign_keys = ON;
    """


# Seed rows (matches cinema_final Section 3, adapted for SQLite).
SEED_DEPARTMENT = """
INSERT INTO department_lookup (department_id, department_name) VALUES
(1, 'Box Office'),
(2, 'Concessions'),
(3, 'Cleaning'),
(4, 'Projection'),
(5, 'Management');
"""

SEED_SUPERVISORS = """
INSERT INTO supervisors (supervisor_id, firstname, lastname, department_id) VALUES
(1, 'Patricia', 'Olsen', 5),
(2, 'Marcus', 'Chen', 4),
(3, 'Elena', 'Rodriguez', 2),
(4, 'James', 'Whitaker', 1),
(5, 'Sonya', 'Patel', 3);
"""

SEED_EMPLOYEES = """
INSERT INTO employees (employee_id, firstname, lastname, email, job_title, status, supervisor_id, department_id) VALUES
('E01', 'Margo', 'Elia', 'margo.elia@mail.com', 'Usher', 'Full time', 4, 1),
('E02', 'Orso', 'Bernardetta', 'orso.bernardetta@mail.com', 'Custodian', 'Part time', 5, 3),
('E03', 'Teodora', 'De Luca', 'teodora.deluca@mail.com', 'Projection Assistant', 'Full time', 2, 4),
('E04', 'Lisandro', 'Agresta', 'lisandro.agresta@mail.com', 'Box Office Associate', 'Full time', 4, 1),
('E05', 'Mesut', 'Demirci', 'mesut.demirci@mail.com', 'Projectionist', 'Full time', 2, 4),
('E06', 'Enis', 'Terzi', 'enis.terzi@mail.com', 'Concessions Associate', 'Part time', 3, 2),
('E07', 'Dominga', 'Aguilar Pineda', 'dominga.aguilar@mail.com', 'Concessions Associate', 'Full time', 3, 2),
('E08', 'Maria', 'Rana', 'maria.rana@mail.com', 'Payroll Specialist', 'Full time', 1, 5),
('E09', 'Janet', 'Choi', 'janet.choi@mail.com', 'Projection Assistant', 'Full time', 2, 4),
('E10', 'Daniel', 'Cross', 'danny.cross@gmail.com', 'Usher', 'Part time', 4, 1),
('E11', 'Mina', 'Villalobos', 'mina.villalobos@mail.com', 'Cinema Assistant Manager', 'Full time', 1, 5),
('E12', 'Patricia', 'Olsen', 'patricia.olsen@mail.com', 'Cinema Manager', 'Full time', NULL, 5),
('E13', 'Marcus', 'Chen', 'marcus.chen@mail.com', 'Department Supervisor', 'Full time', 1, 4),
('E14', 'Elena', 'Rodriguez', 'elena.rodriguez@mail.com', 'Department Supervisor', 'Full time', 1, 2),
('E15', 'James', 'Whitaker', 'james.whitaker@mail.com', 'Department Supervisor', 'Full time', 1, 1),
('E16', 'Sonya', 'Patel', 'sonya.patel@mail.com', 'Department Supervisor', 'Full time', 1, 3),
('E17', 'Yawen', 'Qiu', 'yawen.qui@mail.com', 'Customer Service Representative', 'Full time', 4, 1),
('E18', 'Farzana', 'Sherazi', 'farzana.sherazi@mail.com', 'Box Office Shift Lead', 'Full time', 4, 1),
('E19', 'Aydan', 'Karga', 'aydan.karga@mail.com', 'Usher', 'Part time', 4, 1),
('E20', 'Benjamin', 'Hart', 'ben.hart@mail.com', 'Custodian', 'Part time', 5, 3);
"""

SEED_CUSTOMERS = """
INSERT INTO customers (customer_id, firstname, lastname, email, phone, age, gender, home_city, rewards_member, pref_pymt_method) VALUES
('C001', 'Ethan', 'Walker', 'ethan.walker@mail.com', '3155551001', 28, 'M', 'Syracuse', 1, 'Credit Card'),
('C002', 'Olivia', 'Harris', 'olivia.harris@mail.com', '3155551002', 24, 'F', 'Buffalo', 0, 'Debit Card'),
('C003', 'Noah', 'Clark', 'noah.clark@mail.com', '3155551003', 32, 'M', 'Albany', 1, 'Credit Card'),
('C004', 'Ava', 'Lewis', 'ava.lewis@mail.com', '3155551004', 21, 'F', 'NYC', 0, 'Cash'),
('C005', 'Liam', 'Hall', 'liam.hall@mail.com', '3155551005', 35, 'M', 'Rochester', 1, 'Credit Card'),
('C006', 'Sophia', 'Allen', 'sophia.allen@mail.com', '3155551006', 27, 'F', 'Syracuse', 1, 'Mobile Pay'),
('C007', 'Mason', 'Young', 'mason.young@mail.com', '3155551007', 30, 'M', 'Utica', 0, 'Cash'),
('C008', 'Isabella', 'King', 'isabella.king@mail.com', '3155551008', 22, 'F', 'Ithaca', 0, 'Debit Card'),
('C009', 'James', 'Wright', 'james.wright@mail.com', '3155551009', 40, 'M', 'NYC', 1, 'Credit Card'),
('C010', 'Mia', 'Scott', 'mia.scott@mail.com', '3155551010', 26, 'F', 'Syracuse', 1, 'Mobile Pay'),
('C011', 'Benjamin', 'Green', 'ben.green@mail.com', '3155551011', 34, 'M', 'Buffalo', 0, 'Cash'),
('C012', 'Charlotte', 'Adams', 'charlotte.adams@mail.com', '3155551012', 23, 'F', 'Albany', 0, 'Debit Card'),
('C013', 'Lucas', 'Baker', 'lucas.baker@mail.com', '3155551013', 31, 'M', 'Rochester', 1, 'Credit Card'),
('C014', 'Amelia', 'Nelson', 'amelia.nelson@mail.com', '3155551014', 25, 'F', 'Syracuse', 1, 'Mobile Pay'),
('C015', 'Henry', 'Carter', 'henry.carter@mail.com', '3155551015', 37, 'M', 'NYC', 0, 'Cash'),
('C016', 'Harper', 'Mitchell', 'harper.mitchell@mail.com', '3155551016', 29, 'F', 'Buffalo', 0, 'Debit Card'),
('C017', 'Alexander', 'Perez', 'alex.perez@mail.com', '3155551017', 33, 'M', 'Albany', 1, 'Credit Card'),
('C018', 'Evelyn', 'Roberts', 'evelyn.roberts@mail.com', '3155551018', 20, 'F', 'Ithaca', 0, 'Cash'),
('C019', 'Daniel', 'Turner', 'daniel.turner@mail.com', '3155551019', 41, 'M', 'Syracuse', 1, 'Credit Card'),
('C020', 'Abigail', 'Phillips', 'abigail.phillips@mail.com', '3155551020', 28, 'F', 'Rochester', 0, 'Debit Card');
"""

SEED_THEATRES = """
INSERT INTO theatres (theatre_number, theatre_seat_count, accessible_seating, status, status_notes) VALUES
(1, 40, 1, 1, NULL),
(2, 40, 0, 0, 'Renovations scheduled for April-June'),
(3, 40, 0, 1, NULL),
(4, 40, 0, 1, NULL),
(5, 25, 1, 1, NULL),
(6, 56, 1, 1, NULL),
(7, 56, 1, 0, 'Replacement projector to be installed 4/30; contact Marcus Chen with any questions');
"""

SEED_FILMS = """
INSERT INTO films (film_id, film_title, film_rating, film_length_minutes, film_language, film_last_showing_date) VALUES
(1,  'Dune: Part Three', 'PG-13', 165, 'English', '2026-04-20'),
(2,  'Thunderbolts*', 'PG-13', 127, 'English', '2026-04-18'),
(3,  'How to Train Your Dragon', 'PG', 126, 'English', '2026-04-22'),
(4,  'Lilo & Stitch', 'PG', 108, 'English', '2026-04-19'),
(5,  'F1: The Movie', 'PG-13', 155, 'English', '2026-04-21'),
(6,  'Mission: Impossible - The Final Reckoning', 'PG-13', 169, 'English', '2026-04-23'),
(7,  'Elio', 'PG', 98, 'English', '2026-04-17'),
(8,  'KPop Demon Hunters', 'PG', 110, 'English', '2026-04-24'),
(9,  'Ballerina', 'R', 109, 'English', '2026-04-16'),
(10, 'Weapons', 'R', 134, 'English', '2026-04-25');
"""

SEED_CONCESSIONS = """
INSERT INTO concessions (concession_id, concession_name, concession_size, concession_type, concession_price) VALUES
('CN001', 'Popcorn',      'Regular', 'Snacks',    5.00),
('CN002', 'Popcorn',      'Medium',  'Snacks',    7.00),
('CN003', 'Popcorn',      'Large',   'Snacks',    9.00),
('CN004', 'Coke',         'Regular', 'Beverage',  3.00),
('CN005', 'Coke',         'Medium',  'Beverage',  4.00),
('CN006', 'Coke',         'Large',   'Beverage',  5.00),
('CN007', 'Pepsi',        'Regular', 'Beverage',  3.00),
('CN008', 'Pepsi',        'Medium',  'Beverage',  4.00),
('CN009', 'Pepsi',        'Large',   'Beverage',  5.00),
('CN010', 'Pizza',        'Regular', 'Fast Food', 8.00),
('CN011', 'Pizza',        'Medium',  'Fast Food', 10.00),
('CN012', 'Pizza',        'Large',   'Fast Food', 12.00),
('CN013', 'Nachos',       'Regular', 'Snacks',    6.00),
('CN014', 'Nachos',       'Medium',  'Snacks',    7.50),
('CN015', 'Nachos',       'Large',   'Snacks',    9.00),
('CN016', 'French Fries', 'Regular', 'Fast Food', 4.00),
('CN017', 'French Fries', 'Medium',  'Fast Food', 5.50),
('CN018', 'French Fries', 'Large',   'Fast Food', 7.00),
('CN019', 'Ice Cream',    'Regular', 'Dessert',   3.50),
('CN020', 'Ice Cream',    'Medium',  'Dessert',   4.50);
"""

SEED_SHOWINGS = """
INSERT INTO showings (showing_id, film_id, film_theatre_number, film_showing_datetime, film_available_seats) VALUES
(1,  1,  6, '2026-04-17T12:00:00', 50),
(2,  1,  6, '2026-04-17T16:00:00', 42),
(3,  2,  4, '2026-04-17T13:00:00', 35),
(4,  2,  4, '2026-04-17T18:30:00', 40),
(5,  3,  1, '2026-04-17T11:00:00', 38),
(6,  3,  1, '2026-04-17T15:00:00', 40),
(7,  4,  5, '2026-04-17T14:00:00', 20),
(8,  5,  6, '2026-04-17T19:00:00', 56),
(9,  6,  3, '2026-04-17T17:00:00', 33),
(10, 7,  5, '2026-04-17T10:00:00', 25),
(11, 8,  3, '2026-04-17T20:00:00', 40),
(12, 9,  4, '2026-04-17T21:00:00', 36),
(13, 10, 6, '2026-04-17T21:30:00', 54),
(14, 4,  1, '2026-04-18T13:00:00', 40),
(15, 5,  3, '2026-04-18T15:30:00', 40);
"""

SEED_TICKETS = """
INSERT INTO tickets (ticket_id, ticket_customer_id, ticket_showing_id, ticket_order_number) VALUES
(1,  'C001', 1,  1),
(2,  'C001', 1,  1),
(3,  'C002', 3,  2),
(4,  'C003', 5,  3),
(5,  'C003', 5,  3),
(6,  'C004', 7,  4),
(7,  'C005', 8,  5),
(8,  'C005', 8,  5),
(9,  'C006', 10, 6),
(10, 'C007', 2,  7),
(11, 'C007', 2,  7),
(12, 'C008', 9,  8),
(13, 'C009', 1,  9),
(14, 'C009', 3,  9),
(15, 'C010', 11, 10);
"""

SEED_ORDER_CONCESSIONS = """
INSERT INTO order_concessions (order_number, concession_id, quantity) VALUES
(1,  'CN002', 2),
(1,  'CN005', 2),
(2,  'CN004', 1),
(3,  'CN013', 2),
(5,  'CN011', 1),
(5,  'CN006', 2),
(6,  'CN019', 1),
(7,  'CN001', 2),
(8,  'CN016', 1),
(8,  'CN004', 1),
(9,  'CN003', 3),
(10, 'CN007', 1);
"""

SEED_SHIFTS = """
INSERT INTO shifts (shift_id, employee_id, showing_id, shift_start_datetime, shift_end_datetime, shift_department_id) VALUES
(1,  'E04', 1,    '2026-04-17T11:00:00', '2026-04-17T15:00:00', 1),
(2,  'E18', 3,    '2026-04-17T12:00:00', '2026-04-17T16:00:00', 1),
(3,  'E17', 5,    '2026-04-17T10:00:00', '2026-04-17T14:00:00', 1),
(4,  'E05', 1,    '2026-04-17T11:30:00', '2026-04-17T15:00:00', 4),
(5,  'E03', 3,    '2026-04-17T12:30:00', '2026-04-17T16:00:00', 4),
(6,  'E09', 7,    '2026-04-17T13:30:00', '2026-04-17T17:00:00', 4),
(7,  'E01', 1,    '2026-04-17T11:45:00', '2026-04-17T15:15:00', 1),
(8,  'E10', 8,    '2026-04-17T18:30:00', '2026-04-17T22:30:00', 1),
(9,  'E19', 9,    '2026-04-17T16:30:00', '2026-04-17T20:30:00', 1),
(10, 'E06', NULL, '2026-04-17T10:00:00', '2026-04-17T16:00:00', 2),
(11, 'E07', NULL, '2026-04-17T14:00:00', '2026-04-17T22:00:00', 2),
(12, 'E02', NULL, '2026-04-17T21:00:00', '2026-04-18T01:00:00', 3);
"""

# (order_number, customer_id, subtotal, discount) — tax/total from compute_order_totals
SEED_ORDER_SOURCE = [
    (1, "C001", 23.0, 0.0),
    (2, "C002", 16.0, 0.0),
    (3, "C003", 30.0, 2.0),
    (4, "C004", 12.0, 0.0),
    (5, "C005", 37.0, 0.0),
    (6, "C006", 14.0, 0.0),
    (7, "C007", 24.0, 3.0),
    (8, "C008", 19.0, 0.0),
    (9, "C009", 42.0, 5.0),
    (10, "C010", 11.0, 0.0),
]
