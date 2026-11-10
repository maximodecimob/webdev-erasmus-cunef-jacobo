import os
import tempfile

# Must run before app.database is imported: tests use their own SQLite file, never the development database.
os.environ.setdefault("SESSION_SECRET", "test-secret")
os.environ["DATABASE_PATH"] = os.path.join(tempfile.mkdtemp(), "test.db")

import datetime
from types import SimpleNamespace

import pytest

from app.database import get_connection
from app.repositories.user_repo import UserRepository
from app.seed import seed_database


def _text(days):
    when = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None) + datetime.timedelta(days=days)
    return when.strftime("%Y-%m-%d %H:%M:%S")


def _run(sql, params=()):
    conn = get_connection()
    try:
        cur = conn.execute(sql, params)
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


@pytest.fixture
def world():
    """Seeded database plus helpers to add the rows a test needs."""
    seed_database()
    other_id = _run("INSERT INTO users (email, password_hash, role) VALUES ('other@vibe.test', 'x', 'customer')")
    return SimpleNamespace(
        customer=UserRepository.get_by_email("customer@vibe.test"),
        other=UserRepository.get_by_id(other_id),
        organizer=UserRepository.get_by_email("organizer@vibe.test"),
        add_event=lambda total_tickets=100, days=7, title="Test Event": _run(
            "INSERT INTO events (title, venue, date, price, total_tickets, organizer_id) VALUES (?, 'Test Venue', ?, 10, ?, 2)",
            (title, _text(days), total_tickets)),
        add_ticket=lambda event_id, customer_id, code="SEED-1": _run(
            "INSERT INTO tickets (event_id, customer_id, code) VALUES (?, ?, ?)", (event_id, customer_id, code)),
        count_tickets=lambda: get_connection().execute("SELECT COUNT(*) AS n FROM tickets").fetchone()["n"],
    )


@pytest.fixture
def second_organizer(world):
    from app.utils import create_session_token
    uid = _run("INSERT INTO users (email, password_hash, role) VALUES ('org2@vibe.test', 'x', 'organizer')")
    return SimpleNamespace(id=uid, token=create_session_token(uid))
