"""MySQL connection helper."""
import mysql.connector

from src import config


def get_connection(database: str | None = None):
    """Open a MySQL connection using credentials from .env."""
    return mysql.connector.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        database=database,
    )
