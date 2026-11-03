import os
import glob
import sqlite3
from dotenv import load_dotenv

load_dotenv()

# SQLite database file. Created automatically the first time the app starts.
DATABASE_PATH = os.getenv("DATABASE_PATH", "vibe_tickets.db")

def _dict_factory(cursor, row):
    # Return each row as a dict, so the rest of the code can use row["column"]
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}

def get_connection():
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    conn.row_factory = _dict_factory
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def run_migrations():
    conn = get_connection()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version TEXT PRIMARY KEY,
                applied_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()

        migrations_dir = os.path.join(os.path.dirname(__file__), "migrations")
        migration_files = sorted(glob.glob(os.path.join(migrations_dir, "*.sql")))

        for file_path in migration_files:
            version = os.path.basename(file_path)
            already = conn.execute("SELECT 1 FROM schema_migrations WHERE version = ?;", (version,)).fetchone()
            if already:
                continue

            print(f"Applying migration: {version}")
            with open(file_path, "r", encoding="utf-8") as f:
                sql = f.read()
            conn.executescript(sql)
            conn.execute("INSERT INTO schema_migrations (version) VALUES (?);", (version,))
            conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()
