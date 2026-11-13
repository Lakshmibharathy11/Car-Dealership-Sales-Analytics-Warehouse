"""Central configuration: paths and database settings loaded from .env."""
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = ROOT_DIR / "data" / "raw"
DATA_GENERATED_DIR = ROOT_DIR / "data" / "generated"
SQL_DIR = ROOT_DIR / "sql"
UI_DIR = ROOT_DIR / "apps" / "ui"

load_dotenv(ROOT_DIR / ".env")


def _require(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(
            f"Missing environment variable '{name}'. "
            "Copy .env.example to .env and fill in your values."
        )
    return value


DB_HOST = _require("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = _require("DB_USER")
DB_PASSWORD = _require("DB_PASSWORD")
OLTP_DB = os.getenv("OLTP_DB", "datamasters_db")
WAREHOUSE_DB = os.getenv("WAREHOUSE_DB", "datamasters_wh")

# Demo app logins (overridable via .env)
CUSTOMER_APP_USER = os.getenv("CUSTOMER_APP_USER", "customer")
CUSTOMER_APP_PASSWORD = os.getenv("CUSTOMER_APP_PASSWORD", "customer123")
MANAGER_APP_USER = os.getenv("MANAGER_APP_USER", "manager")
MANAGER_APP_PASSWORD = os.getenv("MANAGER_APP_PASSWORD", "manager123")
