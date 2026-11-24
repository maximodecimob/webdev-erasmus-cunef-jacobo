import importlib.util
import json
import pathlib

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.utils import create_session_token

_spec = importlib.util.spec_from_file_location(
    "mcp_server", pathlib.Path(__file__).resolve().parent.parent / "mcp-server" / "server.py")
server = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(server)


def act_as(monkeypatch, user_id):
    """The MCP server acts as the one user whose ordinary session token is in MCP_TOKEN."""
    monkeypatch.setenv("MCP_TOKEN", create_session_token(user_id))


def call(name, arguments=None):
    return server.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": name, "arguments": arguments or {}}})


def payload(reply):
    assert reply["result"]["isError"] is False
    return json.loads(reply["result"]["content"][0]["text"])


def login(email):
    client = TestClient(app)
    assert client.post("/login", data={"email": email, "password": "secret123"}, follow_redirects=False).status_code == 303
    return client


def test_AC_24_mcp_list_events_equals_the_api(world, monkeypatch):
    """AC-24: mcp list events equals the api"""
    act_as(monkeypatch, world.customer["id"])
    assert payload(call("list_events")) == TestClient(app).get("/api/events").json()


def test_AC_24_mcp_buy_ticket_shows_up_in_the_api_and_errors_are_tool_results(world, monkeypatch):
    """AC-24: mcp buy ticket shows up in the api and errors are tool results"""
    event_id = world.add_event(total_tickets=1)
    act_as(monkeypatch, world.customer["id"])
    bought = payload(call("buy_ticket", {"event_id": event_id}))
    tickets = login("customer@vibe.test").get("/api/tickets").json()
    assert bought["code"] in [t["code"] for t in tickets]
    assert payload(call("my_tickets")) == tickets
    assert call("organizer_events")["result"]["isError"] is True
    act_as(monkeypatch, world.other["id"])
    sold_out = call("buy_ticket", {"event_id": event_id})
    assert sold_out["result"]["isError"] is True
    assert "sold out" in sold_out["result"]["content"][0]["text"]


def test_AC_24_mcp_other_tools_use_the_services(world, monkeypatch):
    """AC-24: mcp other tools use the services"""
    event_id = world.add_event()
    act_as(monkeypatch, world.customer["id"])
    assert payload(call("get_event", {"event_id": event_id}))["id"] == event_id
    assert call("get_event", {"event_id": 99999})["result"]["isError"] is True
    bought = payload(call("buy_ticket", {"event_id": event_id}))
    payload(call("cancel_ticket", {"ticket_id": bought["id"]}))
    assert payload(call("my_tickets")) == []
    act_as(monkeypatch, world.organizer["id"])
    assert len(payload(call("organizer_events"))) >= 1


def test_AC_25_missing_or_invalid_token_is_refused_and_changes_nothing(world, monkeypatch):
    """AC-25: missing or invalid token is refused and changes nothing"""
    event_id = world.add_event()
    before = world.count_tickets()
    for token in (None, "", "wrong", create_session_token(99999)):
        if token is None:
            monkeypatch.delenv("MCP_TOKEN", raising=False)
        else:
            monkeypatch.setenv("MCP_TOKEN", token)
        for name, args in (("buy_ticket", {"event_id": event_id}), ("list_events", {})):
            reply = call(name, args)
            assert "error" in reply and "result" not in reply
    assert world.count_tickets() == before


def test_AC_30_a_user_id_argument_cannot_make_the_token_act_as_someone_else(world, monkeypatch):
    """AC-30: a user_id argument is ignored, the tool acts as the token's user"""
    event_id = world.add_event()
    act_as(monkeypatch, world.customer["id"])
    bought = payload(call("buy_ticket", {"event_id": event_id, "user_id": world.other["id"]}))
    assert bought["code"] in [t["code"] for t in login("customer@vibe.test").get("/api/tickets").json()]
    assert "user_id" not in [p for _, _, s in server.TOOLS for p in s["properties"]]


def test_protocol_basics(world):
    init = server.handle({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "x"}})
    assert init["result"]["capabilities"] == {"tools": {}}
    assert server.handle({"jsonrpc": "2.0", "method": "notifications/initialized"}) is None
    names = [t["name"] for t in server.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})["result"]["tools"]]
    assert len(names) == 8 and "buy_ticket" in names and "find_lecture" in names
    assert server.handle({"jsonrpc": "2.0", "id": 3, "method": "nope"})["error"]["code"] == -32601
    assert call("no_such_tool")["error"]["code"] == -32602
    assert "Lecture 5" in call("find_lecture", {"number": 5})["result"]["content"][0]["text"]
    assert call("find_lecture", {"number": 99})["result"]["isError"] is True
    assert "1." in call("list_lectures")["result"]["content"][0]["text"]
