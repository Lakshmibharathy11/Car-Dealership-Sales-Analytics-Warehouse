"""Run the full batch pipeline: OLTP schema -> CSV load -> warehouse build.

Usage:
    python -m src.pipeline                          # uses data/raw
    python -m src.pipeline --generate               # generate fresh data first
"""
import argparse
import subprocess
import sys
import time

from src.config import DATA_GENERATED_DIR, DATA_RAW_DIR, ROOT_DIR, SQL_DIR
from src.run_sql import run_sql_file


def step(name: str, fn) -> None:
    print(f"\n=== {name} ===")
    start = time.perf_counter()
    fn()
    print(f"--- done in {time.perf_counter() - start:.2f}s")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generate", action="store_true",
                        help="Generate synthetic data and load it instead of data/raw")
    args = parser.parse_args()

    data_dir = DATA_GENERATED_DIR if args.generate else DATA_RAW_DIR

    def run_module(module: str, *extra: str) -> None:
        subprocess.run([sys.executable, "-m", module, *extra], cwd=ROOT_DIR, check=True)

    if args.generate:
        step("1. Generate synthetic data", lambda: run_module("src.generate_data"))
    step("2. Create OLTP schema", lambda: run_sql_file(SQL_DIR / "01_oltp_schema.sql"))
    step("3. Load CSVs into OLTP", lambda: run_module("src.load_oltp", "--data-dir", str(data_dir)))
    step("4. Build warehouse + aggregates", lambda: run_sql_file(SQL_DIR / "02_build_warehouse.sql"))
    print("\nPipeline complete.")


if __name__ == "__main__":
    main()
