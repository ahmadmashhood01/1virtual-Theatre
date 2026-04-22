-- ============================================================
-- IST 659 Final Project: Movie Theater Database
-- UP SCRIPT (Create Tables & Insert Data)
-- ============================================================

USE master;
GO

IF EXISTS (SELECT name FROM sys.databases WHERE name = 'MovieTheaterDB')
    DROP DATABASE MovieTheaterDB;
GO

CREATE DATABASE MovieTheaterDB;
GO

USE MovieTheaterDB;
GO

-- ============================================================
-- TABLE CREATION (in FK dependency order)
-- ============================================================

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
    status          VARCHAR(20)     NOT NULL,  -- 'Full time' | 'Part time'
    supervisor_id   INT             NULL,
    department_id   INT             NOT NULL,
    CONSTRAINT PK_employees PRIMARY KEY (employee_id),
    CONSTRAINT FK_employees_supervisor FOREIGN KEY (supervisor_id)
        REFERENCES supervisors (supervisor_id),
    CONSTRAINT FK_employees_department FOREIGN KEY (department_id)
        REFERENCES department_lookup (department_id)
);

-- 4. customers
CREATE TABLE customers (
    customer_id     VARCHAR(10)     NOT NULL,
    firstname       VARCHAR(50)     NOT NULL,
    lastname        VARCHAR(50)     NOT NULL,
    email           VARCHAR(100)    NOT NULL,
    phone           VARCHAR(20)     NULL,
    age             INT             NULL,
    gender          CHAR(1)         NULL,
    city            VARCHAR(100)    NULL,
    pref_pymt_method VARCHAR(50)    NULL,
    rewards_member  BIT             NOT NULL DEFAULT 0,
    CONSTRAINT PK_customers PRIMARY KEY (customer_id)
);

-- 5. theatres
CREATE TABLE theatres (
    theatre_number      INT         NOT NULL,
    theatre_seat_count  INT         NOT NULL,
    accessible_seating  BIT         NOT NULL DEFAULT 0,
    status              BIT         NOT NULL DEFAULT 1,  -- 1=Open, 0=Closed
    status_notes        VARCHAR(255) NULL,
    CONSTRAINT PK_theatres PRIMARY KEY (theatre_number)
);

-- 6. films
CREATE TABLE films (
    film_id                 INT             NOT NULL IDENTITY(1,1),
    film_title              VARCHAR(200)    NOT NULL,
    film_rating             VARCHAR(10)     NOT NULL,
    film_length_minutes     INT             NOT NULL,
    film_language           VARCHAR(50)     NOT NULL DEFAULT 'English',
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
CREATE TABLE shifts (
    shift_id            INT             NOT NULL IDENTITY(1,1),
    employee_id         VARCHAR(10)     NOT NULL,
    showing_id          INT             NULL,
    shift_start_datetime DATETIME       NOT NULL,
    shift_end_datetime  DATETIME        NOT NULL,
    shift_department_id INT             NULL,
    CONSTRAINT PK_shifts PRIMARY KEY (shift_id),
    CONSTRAINT FK_shifts_employee FOREIGN KEY (employee_id)
        REFERENCES employees (employee_id),
    CONSTRAINT FK_shifts_showing FOREIGN KEY (showing_id)
        REFERENCES showings (showing_id),
    CONSTRAINT FK_shifts_department FOREIGN KEY (shift_department_id)
        REFERENCES department_lookup (department_id)
);

-- 9. orders
CREATE TABLE orders (
    order_number        INT             NOT NULL IDENTITY(1,1),
    order_customer_id   VARCHAR(10)     NOT NULL,
    order_total         DECIMAL(10,2)   NOT NULL DEFAULT 0.00,
    order_discount      DECIMAL(10,2)   NULL DEFAULT 0.00,
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
CREATE TABLE concessions (
    concession_id   VARCHAR(10)     NOT NULL,
    concession_name VARCHAR(100)    NOT NULL,
    concession_size VARCHAR(20)     NULL,
    concession_type VARCHAR(50)     NULL,
    concession_price DECIMAL(10,2)  NOT NULL,
    stock           INT             NULL DEFAULT 0,
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
-- DATA INSERTS
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
INSERT INTO customers (customer_id, firstname, lastname, email, phone, age, gender, city) VALUES
('C001', 'Ethan',     'Walker',   'ethan.walker@mail.com',      '3155551001', 28, 'M', 'Syracuse'),
('C002', 'Olivia',    'Harris',   'olivia.harris@mail.com',     '3155551002', 24, 'F', 'Buffalo'),
('C003', 'Noah',      'Clark',    'noah.clark@mail.com',        '3155551003', 32, 'M', 'Albany'),
('C004', 'Ava',       'Lewis',    'ava.lewis@mail.com',         '3155551004', 21, 'F', 'NYC'),
('C005', 'Liam',      'Hall',     'liam.hall@mail.com',         '3155551005', 35, 'M', 'Rochester'),
('C006', 'Sophia',    'Allen',    'sophia.allen@mail.com',      '3155551006', 27, 'F', 'Syracuse'),
('C007', 'Mason',     'Young',    'mason.young@mail.com',       '3155551007', 30, 'M', 'Utica'),
('C008', 'Isabella',  'King',     'isabella.king@mail.com',     '3155551008', 22, 'F', 'Ithaca'),
('C009', 'James',     'Wright',   'james.wright@mail.com',      '3155551009', 40, 'M', 'NYC'),
('C010', 'Mia',       'Scott',    'mia.scott@mail.com',         '3155551010', 26, 'F', 'Syracuse'),
('C011', 'Benjamin',  'Green',    'ben.green@mail.com',         '3155551011', 34, 'M', 'Buffalo'),
('C012', 'Charlotte', 'Adams',    'charlotte.adams@mail.com',   '3155551012', 23, 'F', 'Albany'),
('C013', 'Lucas',     'Baker',    'lucas.baker@mail.com',       '3155551013', 31, 'M', 'Rochester'),
('C014', 'Amelia',    'Nelson',   'amelia.nelson@mail.com',     '3155551014', 25, 'F', 'Syracuse'),
('C015', 'Henry',     'Carter',   'henry.carter@mail.com',      '3155551015', 37, 'M', 'NYC'),
('C016', 'Harper',    'Mitchell', 'harper.mitchell@mail.com',   '3155551016', 29, 'F', 'Buffalo'),
('C017', 'Alexander', 'Perez',    'alex.perez@mail.com',        '3155551017', 33, 'M', 'Albany'),
('C018', 'Evelyn',    'Roberts',  'evelyn.roberts@mail.com',    '3155551018', 20, 'F', 'Ithaca'),
('C019', 'Daniel',    'Turner',   'daniel.turner@mail.com',     '3155551019', 41, 'M', 'Syracuse'),
('C020', 'Abigail',   'Phillips', 'abigail.phillips@mail.com',  '3155551020', 28, 'F', 'Rochester');

-- theatres
INSERT INTO theatres (theatre_number, theatre_seat_count, accessible_seating, status, status_notes) VALUES
(1, 40, 1, 1, NULL),
(2, 40, 0, 0, 'Renovations scheduled for April-June'),
(3, 40, 0, 1, NULL),
(4, 40, 0, 1, NULL),
(5, 25, 1, 1, NULL),
(6, 56, 1, 1, NULL),
(7, 56, 1, 0, 'Replacement projector set to be installed 4/30; contact Marcus Chen with any questions');

-- films
SET IDENTITY_INSERT films ON;
INSERT INTO films (film_id, film_title, film_rating, film_length_minutes, film_language, film_last_showing_date) VALUES
(1,  'Dune: Part Three',                          'PG-13', 165, 'English', '2026-04-20'),
(2,  'Thunderbolts*',                              'PG-13', 127, 'English', '2026-04-18'),
(3,  'How to Train Your Dragon',                   'PG',    126, 'English', '2026-04-22'),
(4,  'Lilo & Stitch',                              'PG',    108, 'English', '2026-04-19'),
(5,  'F1: The Movie',                              'PG-13', 155, 'English', '2026-04-21'),
(6,  'Mission: Impossible – The Final Reckoning',  'PG-13', 169, 'English', '2026-04-23'),
(7,  'Elio',                                       'PG',     98, 'English', '2026-04-17'),
(8,  'KPop Demon Hunters',                         'PG',    110, 'English', '2026-04-24'),
(9,  'Ballerina',                                  'R',     109, 'English', '2026-04-16'),
(10, 'Weapons',                                    'R',     134, 'English', '2026-04-25');
SET IDENTITY_INSERT films OFF;

-- concessions
INSERT INTO concessions (concession_id, concession_name, concession_size, concession_type, concession_price, stock) VALUES
('CN001', 'Popcorn',      'Regular', 'Snacks',    5.00, 150),
('CN002', 'Popcorn',      'Medium',  'Snacks',    7.00, 120),
('CN003', 'Popcorn',      'Large',   'Snacks',    9.00, 100),
('CN004', 'Coke',         'Regular', 'Beverage',  3.00, 200),
('CN005', 'Coke',         'Medium',  'Beverage',  4.00, 180),
('CN006', 'Coke',         'Large',   'Beverage',  5.00, 160),
('CN007', 'Pepsi',        'Regular', 'Beverage',  3.00, 190),
('CN008', 'Pepsi',        'Medium',  'Beverage',  4.00, 170),
('CN009', 'Pepsi',        'Large',   'Beverage',  5.00, 150),
('CN010', 'Pizza',        'Regular', 'Fast Food', 8.00,  80),
('CN011', 'Pizza',        'Medium',  'Fast Food',10.00,  60),
('CN012', 'Pizza',        'Large',   'Fast Food',12.00,  50),
('CN013', 'Nachos',       'Regular', 'Snacks',    6.00,  90),
('CN014', 'Nachos',       'Medium',  'Snacks',    7.50,  70),
('CN015', 'Nachos',       'Large',   'Snacks',    9.00,  60),
('CN016', 'French Fries', 'Regular', 'Fast Food', 4.00, 110),
('CN017', 'French Fries', 'Medium',  'Fast Food', 5.50,  90),
('CN018', 'French Fries', 'Large',   'Fast Food', 7.00,  70),
('CN019', 'Ice Cream',    'Regular', 'Dessert',   3.50, 100),
('CN020', 'Ice Cream',    'Medium',  'Dessert',   4.50,  80);

GO
