-- =============================================================
-- 02_build_warehouse.sql
-- Builds the analytical warehouse (star schema + aggregates)
-- from the OLTP database. Full refresh: safe to re-run.
-- Run with:  python -m src.run_sql sql/02_build_warehouse.sql
-- {{OLTP_DB}} / {{WAREHOUSE_DB}} are replaced from .env at run time.
-- The warehouse database must already exist.
-- =============================================================

USE {{WAREHOUSE_DB}};

DROP TABLE IF EXISTS TotalRevenueSummary;
DROP TABLE IF EXISTS TopPerformingCars;
DROP TABLE IF EXISTS RevenueTrends;
DROP TABLE IF EXISTS DateDim;
DROP TABLE IF EXISTS Transactions;
DROP TABLE IF EXISTS Customers;
DROP TABLE IF EXISTS Cars;

-- ---------- Dimensions ----------
CREATE TABLE Cars AS SELECT * FROM {{OLTP_DB}}.Cars;
ALTER TABLE Cars ADD PRIMARY KEY (CarID);

CREATE TABLE Customers AS SELECT * FROM {{OLTP_DB}}.Customers;
ALTER TABLE Customers ADD PRIMARY KEY (CustomerID);

-- ---------- Fact ----------
CREATE TABLE Transactions AS SELECT * FROM {{OLTP_DB}}.Transactions;
ALTER TABLE Transactions ADD PRIMARY KEY (TransactionID);
CREATE INDEX idx_tx_date ON Transactions (TransactionDate);
CREATE INDEX idx_tx_car  ON Transactions (CarID);

-- ---------- Date dimension ----------
CREATE TABLE DateDim (
    DateID     INT      NOT NULL PRIMARY KEY,   -- YYYYMMDD
    FullDate   DATE     NOT NULL UNIQUE,
    Day        TINYINT  NOT NULL,
    WeekNumber TINYINT  NOT NULL,
    Month      TINYINT  NOT NULL,
    Quarter    TINYINT  NOT NULL,
    Year       SMALLINT NOT NULL
);

INSERT INTO DateDim (DateID, FullDate, Day, WeekNumber, Month, Quarter, Year)
SELECT DISTINCT
    CAST(DATE_FORMAT(TransactionDate, '%Y%m%d') AS UNSIGNED),
    TransactionDate,
    DAY(TransactionDate),
    WEEK(TransactionDate, 3),
    MONTH(TransactionDate),
    QUARTER(TransactionDate),
    YEAR(TransactionDate)
FROM Transactions;

-- ---------- Aggregate tables ----------
CREATE TABLE RevenueTrends (
    Month        INT            NOT NULL,
    Year         INT            NOT NULL,
    TotalRevenue DECIMAL(14, 2) NOT NULL,
    PRIMARY KEY (Month, Year)
);

INSERT INTO RevenueTrends (Month, Year, TotalRevenue)
SELECT MONTH(TransactionDate), YEAR(TransactionDate), SUM(Amount)
FROM Transactions
GROUP BY YEAR(TransactionDate), MONTH(TransactionDate);

CREATE TABLE TopPerformingCars (
    CarName    VARCHAR(100) NOT NULL PRIMARY KEY,
    TotalSales INT          NOT NULL
);

INSERT INTO TopPerformingCars (CarName, TotalSales)
SELECT c.Name, COUNT(*)
FROM Transactions t
JOIN Cars c ON t.CarID = c.CarID
GROUP BY c.Name;

CREATE TABLE TotalRevenueSummary (
    TotalRevenue DECIMAL(14, 2) NOT NULL
);

INSERT INTO TotalRevenueSummary (TotalRevenue)
SELECT COALESCE(SUM(Amount), 0) FROM Transactions;
