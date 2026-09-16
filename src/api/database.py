from pathlib import Path
import sqlite3


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data" / "nifty100.db"


def get_db_connection():
    """Create a SQLite database connection."""
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection
