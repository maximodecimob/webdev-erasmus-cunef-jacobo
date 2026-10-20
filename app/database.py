import os
import glob
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://vibe:vibe@localhost:5432/vibe_tickets")

def get_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

def run_migrations():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version VARCHAR(255) PRIMARY KEY,
                    applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()

            migrations_dir = os.path.join(os.path.dirname(__file__), "migrations")
            migration_files = sorted(glob.glob(os.path.join(migrations_dir, "*.sql")))

            for file_path in migration_files:
                version = os.path.basename(file_path)
                cur.execute("SELECT 1 FROM schema_migrations WHERE version = %s;", (version,))
                if cur.fetchone():
                    continue

                print(f"Applying migration: {version}")
                with open(file_path, "r", encoding="utf-8") as f:
                    sql = f.read()
                cur.execute(sql)
                cur.execute("INSERT INTO schema_migrations (version) VALUES (%s);", (version,))
                conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()
