"""Generate synthetic cars, customers and transactions CSVs with Faker.

Usage:
    python -m src.generate_data --customers 1000 --transactions 1000
"""
import argparse
import random
from pathlib import Path

import pandas as pd
from faker import Faker

from src.config import DATA_GENERATED_DIR

CAR_COMPANIES = ["Toyota", "Honda", "Ford", "BMW", "Audi",
                 "Mercedes", "Hyundai", "Chevrolet", "Kia", "Nissan"]
PAYMENT_MODES = ["Cash", "Credit Card", "Debit Card", "UPI"]


def generate_cars(faker: Faker, n: int) -> pd.DataFrame:
    rows = []
    for car_id in range(1, n + 1):
        company = random.choice(CAR_COMPANIES)
        rows.append([car_id, f"{company} {faker.word().capitalize()}",
                     round(random.uniform(15000, 50000), 2), company])
    return pd.DataFrame(rows, columns=["CarID", "Name", "Price", "Company"])


def generate_customers(faker: Faker, n: int) -> pd.DataFrame:
    rows = [[cid, faker.name(), faker.address().replace("\n", ", ")]
            for cid in range(1, n + 1)]
    return pd.DataFrame(rows, columns=["CustomerID", "FullName", "Address"])


def generate_transactions(faker: Faker, n: int, cars: pd.DataFrame, n_customers: int) -> pd.DataFrame:
    prices = dict(zip(cars["CarID"], cars["Price"]))
    rows = []
    for tid in range(1, n + 1):
        car_id = random.choice(list(prices))
        rows.append([
            tid,
            car_id,
            random.randint(1, n_customers),
            random.choice(PAYMENT_MODES),
            prices[car_id],  # amount matches the car's listed price
            faker.date_between(start_date="-1y", end_date="today"),
        ])
    return pd.DataFrame(rows, columns=["TransactionID", "CarID", "CustomerID",
                                       "PaymentMode", "Amount", "TransactionDate"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cars", type=int, default=25)
    parser.add_argument("--customers", type=int, default=1000)
    parser.add_argument("--transactions", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility")
    parser.add_argument("--out", type=Path, default=DATA_GENERATED_DIR)
    args = parser.parse_args()

    faker = Faker()
    if args.seed is not None:
        random.seed(args.seed)
        Faker.seed(args.seed)

    args.out.mkdir(parents=True, exist_ok=True)
    cars = generate_cars(faker, args.cars)
    customers = generate_customers(faker, args.customers)
    transactions = generate_transactions(faker, args.transactions, cars, args.customers)

    for name, df in [("cars", cars), ("customers", customers), ("transactions", transactions)]:
        path = args.out / f"{name}.csv"
        df.to_csv(path, index=False)
        print(f"Wrote {len(df):>6} rows -> {path}")


if __name__ == "__main__":
    main()
