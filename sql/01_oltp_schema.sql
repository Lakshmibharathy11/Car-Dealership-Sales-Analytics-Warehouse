-- =============================================================
-- 01_oltp_schema.sql
-- Operational (OLTP) schema — normalized, 3NF.
-- Run with:  python -m src.run_sql sql/01_oltp_schema.sql
-- {{OLTP_DB}} is replaced from .env at run time.
-- =============================================================

USE {{OLTP_DB}};

-- Drop in FK-dependency order
DROP TABLE IF EXISTS Transactions;
DROP TABLE IF EXISTS Customers;
DROP TABLE IF EXISTS Cars;

CREATE TABLE Cars (
    CarID    INT AUTO_INCREMENT PRIMARY KEY,
    Name     VARCHAR(100)   NOT NULL,
    Price    DECIMAL(10, 2) NOT NULL,
    Company  VARCHAR(100)   NOT NULL
);

CREATE TABLE Customers (
    CustomerID INT AUTO_INCREMENT PRIMARY KEY,
    FullName   VARCHAR(100) NOT NULL,
    Address    TEXT         NOT NULL
);

CREATE TABLE Transactions (
    TransactionID   INT AUTO_INCREMENT PRIMARY KEY,
    CarID           INT NOT NULL,
    CustomerID      INT NOT NULL,
    PaymentMode     ENUM('Cash', 'Credit Card', 'Debit Card', 'UPI') NOT NULL,
    Amount          DECIMAL(10, 2) NOT NULL,
    TransactionDate DATE NOT NULL,
    FOREIGN KEY (CarID)      REFERENCES Cars(CarID)           ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (CustomerID) REFERENCES Customers(CustomerID) ON DELETE CASCADE ON UPDATE CASCADE
);
