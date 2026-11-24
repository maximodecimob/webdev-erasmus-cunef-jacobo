import sqlite3

import pytest

from app.errors import AlreadyHolds, EventStarted, Invalid, NotFound
from app.repositories.ticket_repo import TicketRepository
from app.services import google_auth, organizer_service, poster, ticket_service
from app.services.auth_service import AuthService


def test_AC_1_unknown_email_or_wrong_password_does_not_sign_in(world):
    """AC-1: unknown email or wrong password does not sign in"""
    assert AuthService.authenticate("nobody@vibe.test", "secret123") is None
    assert AuthService.authenticate("customer@vibe.test", "wrong-password") is None


def test_AC_7_exchange_code_returns_the_token_answer(monkeypatch):
    """AC-7: the code exchange returns the provider answer"""
    class Res:
        def raise_for_status(self): pass
        def json(self): return {"id_token": "t"}
    monkeypatch.setattr(google_auth.httpx, "post", lambda *a, **k: Res())
    assert google_auth.exchange_code("c", "v") == {"id_token": "t"}


def test_AC_21_editing_a_missing_event_is_404_and_a_bad_date_is_422(world):
    """AC-21: a missing event is 404; AC-20: a bad date is 422"""
    with pytest.raises(NotFound):
        organizer_service.update(world.organizer, 9999, {})
    with pytest.raises(Invalid):
        organizer_service.create(world.organizer, {"title": "a", "venue": "b", "date": "not a date", "price": 1, "total_tickets": 1})


def test_AC_27_a_poster_over_5_mb_is_refused(world):
    """AC-27: a poster over 5 MB is refused"""
    event_id = world.add_event()
    with pytest.raises(Invalid):
        organizer_service.set_poster(world.organizer, event_id, b"0" * (organizer_service.MAX_POSTER_BYTES + 1), "image/png")


def test_AC_23_ask_model_sends_the_image_and_reads_the_text(monkeypatch):
    """AC-23: the model call returns the text of the first candidate"""
    class Res:
        def raise_for_status(self): pass
        def json(self): return {"candidates": [{"content": {"parts": [{"text": "hello"}]}}]}
    monkeypatch.setenv("GEMINI_API_KEY", "fake")
    monkeypatch.setattr(poster.httpx, "post", lambda *a, **k: Res())
    assert poster.ask_model(b"img", "image/png") == "hello"


def test_AC_23_a_date_without_a_zone_is_read_as_utc():
    """AC-23: a date without a zone is read as UTC"""
    assert poster._date("2030-05-01T22:00:00") == "2030-05-01T22:00:00Z"


def test_AC_2_buying_a_missing_event_is_404(world):
    """AC-2: buying a ticket for a missing event is 404"""
    with pytest.raises(NotFound):
        ticket_service.buy_ticket(world.customer, 9999)


def test_AC_4_two_clicks_at_once_are_refused_by_the_unique_index(world, monkeypatch):
    """AC-4: two clicks at once are refused by the unique index"""
    def boom(*args):
        raise sqlite3.IntegrityError()
    monkeypatch.setattr(TicketRepository, "create", boom)
    with pytest.raises(AlreadyHolds):
        ticket_service.buy_ticket(world.customer, world.add_event())


def test_AC_16_cancelling_a_missing_ticket_is_404(world):
    """AC-16: cancelling a missing ticket is 404"""
    with pytest.raises(NotFound):
        ticket_service.cancel_ticket(world.customer, 9999)


def test_AC_17_buying_for_an_event_that_started_is_refused(world):
    """AC-17: buying a ticket for an event that already started is refused"""
    with pytest.raises(EventStarted):
        ticket_service.buy_ticket(world.customer, world.add_event(days=-1))


def test_AC_19_a_date_without_a_zone_is_read_as_utc(world):
    """AC-19: an event date without a zone is read as UTC"""
    data = {"title": "a", "venue": "b", "date": "2099-01-01T22:00:00", "price": 1, "total_tickets": 1}
    assert organizer_service.create(world.organizer, data)["id"]
