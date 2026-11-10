import os
import glob
import sqlite3
from dotenv import load_dotenv

load_dotenv()

# With DATABASE_URL set (Neon on Render) the app uses Postgres; without it, the SQLite file below.
DATABASE_URL = os.getenv("DATABASE_URL")
POSTGRES = bool(DATABASE_URL)
if POSTGRES:
    import psycopg
    from psycopg.rows import dict_row
    IntegrityErrors = (sqlite3.IntegrityError, psycopg.IntegrityError)
else:
    IntegrityErrors = (sqlite3.IntegrityError,)

# SQLite database file. Created automatically the first time the app starts.
DATABASE_PATH = os.getenv("DATABASE_PATH", "vibe_tickets.db")

def _dict_factory(cursor, row):
    # Return each row as a dict, so the rest of the code can use row["column"]
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}

class _Cursor:
    def __init__(self, cur):
        self._cur = cur
        self.rowcount = cur.rowcount

    def fetchone(self):
        return self._cur.fetchone()

    def fetchall(self):
        return self._cur.fetchall()

    @property
    def lastrowid(self):
        return self._cur.fetchone()["id"]


class _PgConnection:
    """Gives a Postgres connection the small part of the sqlite3 API the repositories use."""
    def __init__(self, conn):
        self._conn = conn
        self.commit, self.rollback, self.close = conn.commit, conn.rollback, conn.close

    def execute(self, sql, params=()):
        sql = sql.replace("?", "%s")
        if sql.lstrip().upper().startswith("INSERT INTO") and "schema_migrations" not in sql:
            sql = sql.rstrip().rstrip(";") + " RETURNING id"
        return _Cursor(self._conn.execute(sql, params or None))

    executescript = execute


def _postgres_ddl(sql):
    return (sql.replace("INTEGER PRIMARY KEY", "SERIAL PRIMARY KEY").replace("BLOB", "BYTEA")
            .replace("REAL", "DOUBLE PRECISION")
            .replace("DEFAULT CURRENT_TIMESTAMP", "DEFAULT to_char(now() AT TIME ZONE 'utc', 'YYYY-MM-DD HH24:MI:SS')"))


def ping():
    conn = get_connection()
    try:
        conn.execute("SELECT 1").fetchone()
    finally:
        conn.close()


def get_connection():
    if POSTGRES:
        return _PgConnection(psycopg.connect(DATABASE_URL, row_factory=dict_row))
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    conn.row_factory = _dict_factory
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

MIGRATIONS_TABLE = """
    CREATE TABLE IF NOT EXISTS schema_migrations (
        version TEXT PRIMARY KEY,
        applied_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
"""


def run_migrations():
    conn = get_connection()
    try:
        conn.execute(_postgres_ddl(MIGRATIONS_TABLE) if POSTGRES else MIGRATIONS_TABLE)
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
            if POSTGRES:
                sql = _postgres_ddl(sql)
            conn.executescript(sql)
            conn.execute("INSERT INTO schema_migrations (version) VALUES (?);", (version,))
            conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()
