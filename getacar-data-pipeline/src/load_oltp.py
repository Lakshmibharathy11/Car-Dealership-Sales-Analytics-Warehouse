"""Load cars / customers / transactions CSVs into the OLTP database.

Usage:
    python -m src.load_oltp                      # loads data/raw
    python -m src.load_oltp --data-dir data/generated
"""
import argparse
from pathlib import Path

import mysql.connector
import pandas as pd

from src.config import DATA_RAW_DIR, OLTP_DB
from src.db import get_connection

# Load order respects foreign-key dependencies
TABLES = [
    ("Cars", "cars.csv", ["CarID", "Name", "Price", "Company"]),
    ("Customers", "customers.csv", ["CustomerID", "FullName", "Address"]),
    ("Transactions", "transactions.csv",
     ["TransactionID", "CarID", "CustomerID", "PaymentMode", "Amount", "TransactionDate"]),
]


def load_table(cursor, table: str, csv_path: Path, columns: list[str]) -> int:
    df = pd.read_csv(csv_path, usecols=columns)[columns]
    df = df.astype(object).where(pd.notna(df), None)  # native Python types, NaN -> NULL
    placeholders = ", ".join(["%s"] * len(columns))
    query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
    cursor.executemany(query, df.values.tolist())  # batched insert
    return len(df)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DATA_RAW_DIR)
    args = parser.parse_args()

    conn = get_connection(OLTP_DB)
    cursor = conn.cursor()
    try:
        for table, filename, columns in TABLES:
            n = load_table(cursor, table, args.data_dir / filename, columns)
            print(f"Loaded {n:>6} rows -> {table}")
        conn.commit()
        print("All data loaded successfully.")
    except mysql.connector.Error as e:
        conn.rollback()
        print(f"Load failed, rolled back: {e}")
        raise
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    main()
