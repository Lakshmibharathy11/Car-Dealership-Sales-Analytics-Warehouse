"""Execute a .sql file against MySQL, substituting {{OLTP_DB}} / {{WAREHOUSE_DB}} from .env.

Usage:
    python -m src.run_sql sql/01_oltp_schema.sql
"""
import argparse
import re
from pathlib import Path

from src import config
from src.db import get_connection


def render_sql(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    text = text.replace("{{OLTP_DB}}", config.OLTP_DB)
    text = text.replace("{{WAREHOUSE_DB}}", config.WAREHOUSE_DB)
    # Strip full-line comments, then split into statements
    text = re.sub(r"^\s*--.*$", "", text, flags=re.MULTILINE)
    return [stmt.strip() for stmt in text.split(";") if stmt.strip()]


def run_sql_file(path: Path) -> None:
    statements = render_sql(path)
    conn = get_connection()
    cursor = conn.cursor()
    try:
        for stmt in statements:
            cursor.execute(stmt)
        conn.commit()
        print(f"Executed {len(statements)} statements from {path.name}")
    finally:
        cursor.close()
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sql_file", type=Path)
    args = parser.parse_args()
    run_sql_file(args.sql_file)


if __name__ == "__main__":
    main()
