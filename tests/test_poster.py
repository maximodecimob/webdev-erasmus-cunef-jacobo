import json

from app.services import poster
from tests.test_ticket_api import login
from tests.test_organizer_api import future


def ask_returns(monkeypatch, text):
    monkeypatch.setenv("GEMINI_API_KEY", "fake")
    monkeypatch.setattr(poster, "ask_model", lambda image, mime: text)


def test_AC_8_without_a_model_key_the_fields_stay_empty_with_a_note(monkeypatch):
    """AC-8: without a model key the fields stay empty with a note"""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    result = poster.read_poster(b"img", "image/png")
    assert result["title"] == result["venue"] == result["date"] == "" and result["price"] is None
    assert "type" in result["note"].lower()


def test_AC_23_a_good_answer_fills_the_four_fields(monkeypatch):
    """AC-23: a good answer fills the four fields"""
    ask_returns(monkeypatch, json.dumps({"title": "Neon Night", "venue": "Sala X", "date": "2030-05-01T22:00:00Z", "price": 18}))
    result = poster.read_poster(b"img", "image/png")
    assert (result["title"], result["venue"], result["price"]) == ("Neon Night", "Sala X", 18.0)
    assert result["date"] == "2030-05-01T22:00:00Z" and result["note"] == ""


def test_AC_23_an_answer_that_is_not_json_is_ignored(monkeypatch):
    """AC-23: an answer that is not json is ignored"""
    ask_returns(monkeypatch, "Sure! Here is the poster: ...")
    result = poster.read_poster(b"img", "image/png")
    assert result["title"] == "" and result["note"]


def test_AC_23_a_bad_date_stays_empty_but_other_fields_are_kept(monkeypatch):
    """AC-23: a bad date stays empty but other fields are kept"""
    ask_returns(monkeypatch, '```json\n{"title": "Neon Night", "venue": "Sala X", "date": "next friday", "price": "free"}\n```')
    result = poster.read_poster(b"img", "image/png")
    assert result["title"] == "Neon Night" and result["date"] == "" and result["price"] is None


def test_a_failing_model_call_gives_a_note_not_an_error(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake")
    def boom(image, mime): raise RuntimeError("down")
    monkeypatch.setattr(poster, "ask_model", boom)
    assert poster.read_poster(b"img", "image/png")["note"]


def test_poster_endpoint_is_for_organizers_only(world, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    files = {"image": ("p.png", b"img", "image/png")}
    assert login("organizer@vibe.test").post("/api/organizer/poster", files=files).status_code == 200
    assert login("customer@vibe.test").post("/api/organizer/poster", files=files).status_code == 403
