-- ============================================================
-- IST 659 Final Project: Movie Theater Database
-- FINAL COMBINED SCRIPT
-- Sections:
--   1. DOWN  — drop all tables safely
--   2. UP    — create database & all 12 tables
--   3. DATA  — insert all sample records
--   4. TEST  — 3 validation queries
-- ============================================================


-- ============================================================
-- SECTION 1: DOWN SCRIPT
-- Drops all tables in reverse FK dependency order so no
-- constraint violations occur. Safe to re-run at any time.
-- ============================================================

USE master;
GO

IF EXISTS (SELECT name FROM sys.databases WHERE name = 'MovieTheaterDB')
BEGIN
    ALTER DATABASE MovieTheaterDB SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE MovieTheaterDB;
END
GO


-- ============================================================
-- SECTION 2: UP SCRIPT
-- Creates the database and all 12 tables in FK dependency
-- order. Changes from previous version:
--   - orders: order_total replaced with subtotal, tax (derived),
--             discount, and total (derived computed column)
--   - shifts: shift_department_id is now NOT NULL
--   - concessions: stock column removed (not in conceptual model)
--   - customers: city column renamed to home_city
-- ============================================================

CREATE DATABASE MovieTheaterDB;
GO

USE MovieTheaterDB;
GO

-- 1. department_lookup
CREATE TABLE department_lookup (
    department_id   INT             NOT NULL,
    department_name VARCHAR(50)     NOT NULL,
    CONSTRAINT PK_department_lookup PRIMARY KEY (department_id)
);

-- 2. supervisors
CREATE TABLE supervisors (
    supervisor_id   INT             NOT NULL,
    firstname       VARCHAR(50)     NOT NULL,
    lastname        VARCHAR(50)     NOT NULL,
    department_id   INT             NOT NULL,
    CONSTRAINT PK_supervisors PRIMARY KEY (supervisor_id),
    CONSTRAINT FK_supervisors_department FOREIGN KEY (department_id)
        REFERENCES department_lookup (department_id)
);

-- 3. employees
CREATE TABLE employees (
    employee_id     VARCHAR(10)     NOT NULL,
    firstname       VARCHAR(50)     NOT NULL,
    lastname        VARCHAR(50)     NOT NULL,
    email           VARCHAR(100)    NOT NULL,
    job_title       VARCHAR(100)    NOT NULL,
    status          VARCHAR(20)     NOT NULL,       -- 'Full time' | 'Part time'
    supervisor_id   INT             NULL,           -- nullable: top-level manager has none
    department_id   INT             NOT NULL,
    CONSTRAINT PK_employees PRIMARY KEY (employee_id),
    CONSTRAINT FK_employees_supervisor FOREIGN KEY (supervisor_id)
        REFERENCES supervisors (supervisor_id),
    CONSTRAINT FK_employees_department FOREIGN KEY (department_id)
        REFERENCES department_lookup (department_id)
);

-- 4. customers
CREATE TABLE customers (
    customer_id         VARCHAR(10)     NOT NULL,
    firstname           VARCHAR(50)     NOT NULL,
    lastname            VARCHAR(50)     NOT NULL,
    email               VARCHAR(100)    NOT NULL,
    phone               VARCHAR(20)     NULL,
    age                 INT             NULL,
    gender              CHAR(1)         NULL,
    home_city           VARCHAR(100)    NULL,
    rewards_member      BIT             NOT NULL DEFAULT 0,
    pref_pymt_method    VARCHAR(50)     NULL,
    CONSTRAINT PK_customers PRIMARY KEY (customer_id)
);

-- 5. theatres
CREATE TABLE theatres (
    theatre_number      INT             NOT NULL,
    theatre_seat_count  INT             NOT NULL,
    accessible_seating  BIT             NOT NULL,
    status              BIT             NOT NULL,   -- 1=Open, 0=Closed
    status_notes        VARCHAR(255)    NULL,       -- optional per conceptual model
    CONSTRAINT PK_theatres PRIMARY KEY (theatre_number)
);

-- 6. films
CREATE TABLE films (
    film_id                 INT             NOT NULL IDENTITY(1,1),
    film_title              VARCHAR(200)    NOT NULL,
    film_rating             VARCHAR(10)     NOT NULL,
    film_length_minutes     INT             NOT NULL,
    film_language           VARCHAR(50)     NOT NULL,
    film_last_showing_date  DATE            NULL,
    CONSTRAINT PK_films PRIMARY KEY (film_id)
);

-- 7. showings
CREATE TABLE showings (
    showing_id              INT             NOT NULL IDENTITY(1,1),
    film_id                 INT             NOT NULL,
    film_theatre_number     INT             NOT NULL,
    film_showing_datetime   DATETIME        NOT NULL,
    film_available_seats    INT             NOT NULL,
    CONSTRAINT PK_showings PRIMARY KEY (showing_id),
    CONSTRAINT FK_showings_film FOREIGN KEY (film_id)
        REFERENCES films (film_id),
    CONSTRAINT FK_showings_theatre FOREIGN KEY (film_theatre_number)
        REFERENCES theatres (theatre_number)
);

-- 8. shifts
-- shift_department_id is NOT NULL per group member feedback —
-- every shift must belong to a department.
-- showing_id remains nullable: not all shifts are tied to a showing
-- (e.g. cleaning, management, concessions stand shifts).
CREATE TABLE shifts (
    shift_id                INT             NOT NULL IDENTITY(1,1),
    employee_id             VARCHAR(10)     NOT NULL,
    showing_id              INT             NULL,
    shift_start_datetime    DATETIME        NOT NULL,
    shift_end_datetime      DATETIME        NOT NULL,
    shift_department_id     INT             NOT NULL,   -- updated: NOT NULL
    CONSTRAINT PK_shifts PRIMARY KEY (shift_id),
    CONSTRAINT FK_shifts_employee FOREIGN KEY (employee_id)
        REFERENCES employees (employee_id),
    CONSTRAINT FK_shifts_showing FOREIGN KEY (showing_id)
        REFERENCES showings (showing_id),
    CONSTRAINT FK_shifts_department FOREIGN KEY (shift_department_id)
        REFERENCES department_lookup (department_id)
);

-- 9. orders
-- Updated per group member feedback and conceptual model:
--   subtotal  [R]  — required, sum of ticket prices before tax/discount
--   tax       [D]  — derived, computed as subtotal * 0.08 (8% tax rate)
--   discount        — optional dollar amount off
--   total     [DR] — derived, computed as subtotal + tax - discount
CREATE TABLE orders (
    order_number        INT             NOT NULL IDENTITY(1,1),
    order_customer_id   VARCHAR(10)     NOT NULL,
    subtotal            DECIMAL(10,2)   NOT NULL DEFAULT 0.00,
    tax                 AS (CAST(subtotal * 0.08 AS DECIMAL(10,2))),        -- derived
    discount            DECIMAL(10,2)   NULL     DEFAULT 0.00,
    total               AS (CAST(subtotal * 1.08 - ISNULL(discount, 0)
                                AS DECIMAL(10,2))),                         -- derived
    CONSTRAINT PK_orders PRIMARY KEY (order_number),
    CONSTRAINT FK_orders_customer FOREIGN KEY (order_customer_id)
        REFERENCES customers (customer_id)
);

-- 10. tickets
CREATE TABLE tickets (
    ticket_id           INT             NOT NULL IDENTITY(1,1),
    ticket_customer_id  VARCHAR(10)     NOT NULL,
    ticket_showing_id   INT             NOT NULL,
    ticket_order_number INT             NOT NULL,
    CONSTRAINT PK_tickets PRIMARY KEY (ticket_id),
    CONSTRAINT FK_tickets_customer FOREIGN KEY (ticket_customer_id)
        REFERENCES customers (customer_id),
    CONSTRAINT FK_tickets_showing FOREIGN KEY (ticket_showing_id)
        REFERENCES showings (showing_id),
    CONSTRAINT FK_tickets_order FOREIGN KEY (ticket_order_number)
        REFERENCES orders (order_number)
);

-- 11. concessions
-- stock removed: not present in final conceptual model
CREATE TABLE concessions (
    concession_id       VARCHAR(10)     NOT NULL,
    concession_name     VARCHAR(100)    NOT NULL,
    concession_size     VARCHAR(20)     NULL,
    concession_type     VARCHAR(50)     NULL,
    concession_price    DECIMAL(10,2)   NOT NULL,
    CONSTRAINT PK_concessions PRIMARY KEY (concession_id)
);

-- 12. order_concessions (junction table)
CREATE TABLE order_concessions (
    order_number    INT             NOT NULL,
    concession_id   VARCHAR(10)     NOT NULL,
    quantity        INT             NOT NULL DEFAULT 1,
    CONSTRAINT PK_order_concessions PRIMARY KEY (order_number, concession_id),
    CONSTRAINT FK_oc_order FOREIGN KEY (order_number)
        REFERENCES orders (order_number),
    CONSTRAINT FK_oc_concession FOREIGN KEY (concession_id)
        REFERENCES concessions (concession_id)
);

GO


-- ============================================================
-- SECTION 3: SAMPLE DATA
-- Inserts in FK dependency order. IDENTITY_INSERT is used for
-- tables where we want explicit IDs for cross-referencing.
-- ============================================================

-- department_lookup
INSERT INTO department_lookup (department_id, department_name) VALUES
(1, 'Box Office'),
(2, 'Concessions'),
(3, 'Cleaning'),
(4, 'Projection'),
(5, 'Management');

-- supervisors
INSERT INTO supervisors (supervisor_id, firstname, lastname, department_id) VALUES
(1, 'Patricia', 'Olsen',     5),
(2, 'Marcus',   'Chen',      4),
(3, 'Elena',    'Rodriguez', 2),
(4, 'James',    'Whitaker',  1),
(5, 'Sonya',    'Patel',     3);

-- employees
INSERT INTO employees (employee_id, firstname, lastname, email, job_title, status, supervisor_id, department_id) VALUES
('E01', 'Margo',     'Elia',           'margo.elia@mail.com',         'Usher',                            'Full time', 4,    1),
('E02', 'Orso',      'Bernardetta',    'orso.bernardetta@mail.com',   'Custodian',                        'Part time', 5,    3),
('E03', 'Teodora',   'De Luca',        'teodora.deluca@mail.com',     'Projection Assistant',             'Full time', 2,    4),
('E04', 'Lisandro',  'Agresta',        'lisandro.agresta@mail.com',   'Box Office Associate',             'Full time', 4,    1),
('E05', 'Mesut',     'Demirci',        'mesut.demirci@mail.com',      'Projectionist',                    'Full time', 2,    4),
('E06', 'Enis',      'Terzi',          'enis.terzi@mail.com',         'Concessions Associate',            'Part time', 3,    2),
('E07', 'Dominga',   'Aguilar Pineda', 'dominga.aguilar@mail.com',    'Concessions Associate',            'Full time', 3,    2),
('E08', 'Maria',     'Rana',           'maria.rana@mail.com',         'Payroll Specialist',               'Full time', 1,    5),
('E09', 'Janet',     'Choi',           'janet.choi@mail.com',         'Projection Assistant',             'Full time', 2,    4),
('E10', 'Daniel',    'Cross',          'danny.cross@gmail.com',       'Usher',                            'Part time', 4,    1),
('E11', 'Mina',      'Villalobos',     'mina.villalobos@mail.com',    'Cinema Assistant Manager',         'Full time', 1,    5),
('E12', 'Patricia',  'Olsen',          'patricia.olsen@mail.com',     'Cinema Manager',                   'Full time', NULL, 5),
('E13', 'Marcus',    'Chen',           'marcus.chen@mail.com',        'Department Supervisor',            'Full time', 1,    4),
('E14', 'Elena',     'Rodriguez',      'elena.rodriguez@mail.com',    'Department Supervisor',            'Full time', 1,    2),
('E15', 'James',     'Whitaker',       'james.whitaker@mail.com',     'Department Supervisor',            'Full time', 1,    1),
('E16', 'Sonya',     'Patel',          'sonya.patel@mail.com',        'Department Supervisor',            'Full time', 1,    3),
('E17', 'Yawen',     'Qiu',            'yawen.qui@mail.com',          'Customer Service Representative',  'Full time', 4,    1),
('E18', 'Farzana',   'Sherazi',        'farzana.sherazi@mail.com',    'Box Office Shift Lead',            'Full time', 4,    1),
('E19', 'Aydan',     'Karga',          'aydan.karga@mail.com',        'Usher',                            'Part time', 4,    1),
('E20', 'Benjamin',  'Hart',           'ben.hart@mail.com',           'Custodian',                        'Part time', 5,    3);

-- customers
INSERT INTO customers (customer_id, firstname, lastname, email, phone, age, gender, home_city, rewards_member, pref_pymt_method) VALUES
('C001', 'Ethan',     'Walker',   'ethan.walker@mail.com',      '3155551001', 28, 'M', 'Syracuse',  1, 'Credit Card'),
('C002', 'Olivia',    'Harris',   'olivia.harris@mail.com',     '3155551002', 24, 'F', 'Buffalo',   0, 'Debit Card'),
('C003', 'Noah',      'Clark',    'noah.clark@mail.com',        '3155551003', 32, 'M', 'Albany',    1, 'Credit Card'),
('C004', 'Ava',       'Lewis',    'ava.lewis@mail.com',         '3155551004', 21, 'F', 'NYC',       0, 'Cash'),
('C005', 'Liam',      'Hall',     'liam.hall@mail.com',         '3155551005', 35, 'M', 'Rochester', 1, 'Credit Card'),
('C006', 'Sophia',    'Allen',    'sophia.allen@mail.com',      '3155551006', 27, 'F', 'Syracuse',  1, 'Mobile Pay'),
('C007', 'Mason',     'Young',    'mason.young@mail.com',       '3155551007', 30, 'M', 'Utica',     0, 'Cash'),
('C008', 'Isabella',  'King',     'isabella.king@mail.com',     '3155551008', 22, 'F', 'Ithaca',    0, 'Debit Card'),
('C009', 'James',     'Wright',   'james.wright@mail.com',      '3155551009', 40, 'M', 'NYC',       1, 'Credit Card'),
('C010', 'Mia',       'Scott',    'mia.scott@mail.com',         '3155551010', 26, 'F', 'Syracuse',  1, 'Mobile Pay'),
('C011', 'Benjamin',  'Green',    'ben.green@mail.com',         '3155551011', 34, 'M', 'Buffalo',   0, 'Cash'),
('C012', 'Charlotte', 'Adams',    'charlotte.adams@mail.com',   '3155551012', 23, 'F', 'Albany',    0, 'Debit Card'),
('C013', 'Lucas',     'Baker',    'lucas.baker@mail.com',       '3155551013', 31, 'M', 'Rochester', 1, 'Credit Card'),
('C014', 'Amelia',    'Nelson',   'amelia.nelson@mail.com',     '3155551014', 25, 'F', 'Syracuse',  1, 'Mobile Pay'),
('C015', 'Henry',     'Carter',   'henry.carter@mail.com',      '3155551015', 37, 'M', 'NYC',       0, 'Cash'),
('C016', 'Harper',    'Mitchell', 'harper.mitchell@mail.com',   '3155551016', 29, 'F', 'Buffalo',   0, 'Debit Card'),
('C017', 'Alexander', 'Perez',    'alex.perez@mail.com',        '3155551017', 33, 'M', 'Albany',    1, 'Credit Card'),
('C018', 'Evelyn',    'Roberts',  'evelyn.roberts@mail.com',    '3155551018', 20, 'F', 'Ithaca',    0, 'Cash'),
('C019', 'Daniel',    'Turner',   'daniel.turner@mail.com',     '3155551019', 41, 'M', 'Syracuse',  1, 'Credit Card'),
('C020', 'Abigail',   'Phillips', 'abigail.phillips@mail.com',  '3155551020', 28, 'F', 'Rochester', 0, 'Debit Card');

-- theatres
INSERT INTO theatres (theatre_number, theatre_seat_count, accessible_seating, status, status_notes) VALUES
(1, 40, 1, 1, NULL),
(2, 40, 0, 0, 'Renovations scheduled for April-June'),
(3, 40, 0, 1, NULL),
(4, 40, 0, 1, NULL),
(5, 25, 1, 1, NULL),
(6, 56, 1, 1, NULL),
(7, 56, 1, 0, 'Replacement projector to be installed 4/30; contact Marcus Chen with any questions');

-- films
SET IDENTITY_INSERT films ON;
INSERT INTO films (film_id, film_title, film_rating, film_length_minutes, film_language, film_last_showing_date) VALUES
(1,  'Dune: Part Three',                          'PG-13', 165, 'English', '2026-04-20'),
(2,  'Thunderbolts*',                              'PG-13', 127, 'English', '2026-04-18'),
(3,  'How to Train Your Dragon',                   'PG',    126, 'English', '2026-04-22'),
(4,  'Lilo & Stitch',                              'PG',    108, 'English', '2026-04-19'),
(5,  'F1: The Movie',                              'PG-13', 155, 'English', '2026-04-21'),
(6,  'Mission: Impossible - The Final Reckoning',  'PG-13', 169, 'English', '2026-04-23'),
(7,  'Elio',                                       'PG',     98, 'English', '2026-04-17'),
(8,  'KPop Demon Hunters',                         'PG',    110, 'English', '2026-04-24'),
(9,  'Ballerina',                                  'R',     109, 'English', '2026-04-16'),
(10, 'Weapons',                                    'R',     134, 'English', '2026-04-25');
SET IDENTITY_INSERT films OFF;

-- concessions (stock removed per final conceptual model)
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

-- showings (open theatres only: 1, 3, 4, 5, 6)
SET IDENTITY_INSERT showings ON;
INSERT INTO showings (showing_id, film_id, film_theatre_number, film_showing_datetime, film_available_seats) VALUES
(1,   1,  6, '2026-04-17 12:00:00', 50),
(2,   1,  6, '2026-04-17 16:00:00', 42),
(3,   2,  4, '2026-04-17 13:00:00', 35),
(4,   2,  4, '2026-04-17 18:30:00', 40),
(5,   3,  1, '2026-04-17 11:00:00', 38),
(6,   3,  1, '2026-04-17 15:00:00', 40),
(7,   4,  5, '2026-04-17 14:00:00', 20),
(8,   5,  6, '2026-04-17 19:00:00', 56),
(9,   6,  3, '2026-04-17 17:00:00', 33),
(10,  7,  5, '2026-04-17 10:00:00', 25),
(11,  8,  3, '2026-04-17 20:00:00', 40),
(12,  9,  4, '2026-04-17 21:00:00', 36),
(13, 10,  6, '2026-04-17 21:30:00', 54),
(14,  4,  1, '2026-04-18 13:00:00', 40),
(15,  5,  3, '2026-04-18 15:30:00', 40);
SET IDENTITY_INSERT showings OFF;

-- orders
-- subtotal is entered; tax and total are computed automatically by SQL Server.
SET IDENTITY_INSERT orders ON;
INSERT INTO orders (order_number, order_customer_id, subtotal, discount) VALUES
(1,  'C001', 23.00, 0.00),
(2,  'C002', 16.00, 0.00),
(3,  'C003', 30.00, 2.00),
(4,  'C004', 12.00, 0.00),
(5,  'C005', 37.00, 0.00),
(6,  'C006', 14.00, 0.00),
(7,  'C007', 24.00, 3.00),
(8,  'C008', 19.00, 0.00),
(9,  'C009', 42.00, 5.00),
(10, 'C010', 11.00, 0.00);
SET IDENTITY_INSERT orders OFF;

-- tickets
SET IDENTITY_INSERT tickets ON;
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
SET IDENTITY_INSERT tickets OFF;

-- order_concessions
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

-- shifts
-- shift_department_id is NOT NULL — every shift record requires a department.
SET IDENTITY_INSERT shifts ON;
INSERT INTO shifts (shift_id, employee_id, showing_id, shift_start_datetime, shift_end_datetime, shift_department_id) VALUES
(1,  'E04', 1,    '2026-04-17 11:00:00', '2026-04-17 15:00:00', 1),
(2,  'E18', 3,    '2026-04-17 12:00:00', '2026-04-17 16:00:00', 1),
(3,  'E17', 5,    '2026-04-17 10:00:00', '2026-04-17 14:00:00', 1),
(4,  'E05', 1,    '2026-04-17 11:30:00', '2026-04-17 15:00:00', 4),
(5,  'E03', 3,    '2026-04-17 12:30:00', '2026-04-17 16:00:00', 4),
(6,  'E09', 7,    '2026-04-17 13:30:00', '2026-04-17 17:00:00', 4),
(7,  'E01', 1,    '2026-04-17 11:45:00', '2026-04-17 15:15:00', 1),
(8,  'E10', 8,    '2026-04-17 18:30:00', '2026-04-17 22:30:00', 1),
(9,  'E19', 9,    '2026-04-17 16:30:00', '2026-04-17 20:30:00', 1),
(10, 'E06', NULL, '2026-04-17 10:00:00', '2026-04-17 16:00:00', 2),
(11, 'E07', NULL, '2026-04-17 14:00:00', '2026-04-17 22:00:00', 2),
(12, 'E02', NULL, '2026-04-17 21:00:00', '2026-04-18 01:00:00', 3);
SET IDENTITY_INSERT shifts OFF;

GO


-- ============================================================
-- SECTION 4: TEST QUERIES
-- ============================================================

-- ------------------------------------------------------------
-- TEST QUERY 1: Employee Roster by Department
-- Validates FK joins across employees, supervisors, and
-- department_lookup. Confirms nullable supervisor_id resolves
-- correctly (Patricia Olsen / Cinema Manager shows N/A).
-- Expected: 20 rows grouped by department.
-- ------------------------------------------------------------

SELECT
    dl.department_name                              AS Department,
    e.employee_id                                   AS EmployeeID,
    e.firstname + ' ' + e.lastname                  AS EmployeeName,
    e.job_title                                     AS JobTitle,
    e.status                                        AS EmploymentStatus,
    ISNULL(s.firstname + ' ' + s.lastname, 'N/A')  AS SupervisorName
FROM employees e
    JOIN  department_lookup dl ON e.department_id = dl.department_id
    LEFT JOIN supervisors s    ON e.supervisor_id  = s.supervisor_id
ORDER BY dl.department_name, e.lastname;

GO

-- ------------------------------------------------------------
-- TEST QUERY 2: Film Schedule with Theatre Availability
-- Validates FK joins across showings, films, and theatres.
-- Confirms seat availability and tickets sold calculate
-- correctly. Only open theatres should appear.
-- Expected: 15 rows, one per showing.
-- ------------------------------------------------------------

SELECT
    f.film_title                                        AS FilmTitle,
    f.film_rating                                       AS Rating,
    f.film_length_minutes                               AS RuntimeMinutes,
    t.theatre_number                                    AS TheatreNumber,
    t.theatre_seat_count                                AS TotalSeats,
    CASE WHEN t.accessible_seating = 1
         THEN 'Yes' ELSE 'No' END                       AS AccessibleSeating,
    CASE WHEN t.status = 1
         THEN 'Open' ELSE 'Closed' END                  AS TheatreStatus,
    sh.film_showing_datetime                            AS ShowingDateTime,
    sh.film_available_seats                             AS AvailableSeats,
    t.theatre_seat_count - sh.film_available_seats      AS TicketsSold
FROM showings sh
    JOIN films    f ON sh.film_id             = f.film_id
    JOIN theatres t ON sh.film_theatre_number = t.theatre_number
ORDER BY sh.film_showing_datetime;

GO

-- ------------------------------------------------------------
-- TEST QUERY 3: Order Summary with Tax and Totals
-- Validates the computed columns (tax, total) on the orders
-- table and confirms the subtotal + discount breakdown is
-- working correctly per the updated conceptual model.
-- Expected: 10 rows, one per order, with auto-calculated
-- tax (8%) and total (subtotal * 1.08 - discount).
-- ------------------------------------------------------------

SELECT
    o.order_number                          AS OrderNumber,
    c.firstname + ' ' + c.lastname         AS CustomerName,
    o.subtotal                              AS Subtotal,
    o.tax                                   AS Tax,
    ISNULL(o.discount, 0.00)               AS Discount,
    o.total                                 AS OrderTotal
FROM orders o
    JOIN customers c ON o.order_customer_id = c.customer_id
ORDER BY o.order_number;

GO

-- ------------------------------------------------------------
-- QUICK ROW COUNT VERIFICATION
-- Run after all inserts to confirm every table populated.
-- ------------------------------------------------------------

SELECT 'department_lookup'  AS TableName, COUNT(*) AS TotalRows FROM department_lookup  UNION ALL
SELECT 'supervisors',                     COUNT(*)              FROM supervisors          UNION ALL
SELECT 'employees',                       COUNT(*)              FROM employees            UNION ALL
SELECT 'customers',                       COUNT(*)              FROM customers            UNION ALL
SELECT 'theatres',                        COUNT(*)              FROM theatres             UNION ALL
SELECT 'films',                           COUNT(*)              FROM films                UNION ALL
SELECT 'concessions',                     COUNT(*)              FROM concessions          UNION ALL
SELECT 'showings',                        COUNT(*)              FROM showings             UNION ALL
SELECT 'orders',                          COUNT(*)              FROM orders               UNION ALL
SELECT 'tickets',                         COUNT(*)              FROM tickets              UNION ALL
SELECT 'order_concessions',               COUNT(*)              FROM order_concessions    UNION ALL
SELECT 'shifts',                          COUNT(*)              FROM shifts;

GO
