-- ============================================================
-- IST 659 Final Project: Movie Theater Database
-- DOWN SCRIPT (Drop Tables in reverse FK dependency order)
-- ============================================================

USE MovieTheaterDB;
GO

-- Drop junction / leaf tables first
IF OBJECT_ID('order_concessions', 'U') IS NOT NULL DROP TABLE order_concessions;
IF OBJECT_ID('tickets',           'U') IS NOT NULL DROP TABLE tickets;
IF OBJECT_ID('orders',            'U') IS NOT NULL DROP TABLE orders;
IF OBJECT_ID('shifts',            'U') IS NOT NULL DROP TABLE shifts;
IF OBJECT_ID('showings',          'U') IS NOT NULL DROP TABLE showings;
IF OBJECT_ID('concessions',       'U') IS NOT NULL DROP TABLE concessions;
IF OBJECT_ID('films',             'U') IS NOT NULL DROP TABLE films;
IF OBJECT_ID('theatres',          'U') IS NOT NULL DROP TABLE theatres;
IF OBJECT_ID('customers',         'U') IS NOT NULL DROP TABLE customers;
IF OBJECT_ID('employees',         'U') IS NOT NULL DROP TABLE employees;
IF OBJECT_ID('supervisors',       'U') IS NOT NULL DROP TABLE supervisors;
IF OBJECT_ID('department_lookup', 'U') IS NOT NULL DROP TABLE department_lookup;

GO

-- Optionally drop the entire database
-- USE master;
-- GO
-- IF EXISTS (SELECT name FROM sys.databases WHERE name = 'MovieTheaterDB')
--     DROP DATABASE MovieTheaterDB;
-- GO
