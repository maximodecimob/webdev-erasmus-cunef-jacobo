import importlib.util
import json
import pathlib

import pytest
from fastapi.testclient import TestClient

from app.main import app

_spec = importlib.util.spec_from_file_location(
    "mcp_server", pathlib.Path(__file__).resolve().parent.parent / "mcp-server" / "server.py")
server = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(server)

TOKEN = "s3cret-mcp-token"


@pytest.fixture(autouse=True)
def mcp_token(monkeypatch):
    monkeypatch.setenv("MCP_TOKEN", TOKEN)


def call(name, arguments, token=TOKEN):
    args = dict(arguments) if token is None else {**arguments, "token": token}
    return server.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": name, "arguments": args}})


def payload(reply):
    assert reply["result"]["isError"] is False
    return json.loads(reply["result"]["content"][0]["text"])


def login(email):
    client = TestClient(app)
    assert client.post("/login", data={"email": email, "password": "secret123"}, follow_redirects=False).status_code == 303
    return client


def test_AC_24_mcp_list_events_equals_the_api(world):
    """AC-24: mcp list events equals the api"""
    assert payload(call("list_events", {})) == TestClient(app).get("/api/events").json()


def test_AC_24_mcp_buy_ticket_shows_up_in_the_api_and_errors_are_tool_results(world):
    """AC-24: mcp buy ticket shows up in the api and errors are tool results"""
    event_id = world.add_event(total_tickets=1)
    bought = payload(call("buy_ticket", {"user_id": world.customer["id"], "event_id": event_id}))
    tickets = login("customer@vibe.test").get("/api/tickets").json()
    assert bought["code"] in [t["code"] for t in tickets]
    assert payload(call("my_tickets", {"user_id": world.customer["id"]})) == tickets
    sold_out = call("buy_ticket", {"user_id": world.other["id"], "event_id": event_id})
    assert sold_out["result"]["isError"] is True
    assert "sold out" in sold_out["result"]["content"][0]["text"]
    refused = call("organizer_events", {"user_id": world.customer["id"]})
    assert refused["result"]["isError"] is True


def test_AC_24_mcp_other_tools_use_the_services(world):
    """AC-24: mcp other tools use the services"""
    event_id = world.add_event()
    assert payload(call("get_event", {"event_id": event_id}))["id"] == event_id
    assert call("get_event", {"event_id": 99999})["result"]["isError"] is True
    assert call("buy_ticket", {"user_id": 99999, "event_id": event_id})["result"]["isError"] is True
    bought = payload(call("buy_ticket", {"user_id": world.customer["id"], "event_id": event_id}))
    payload(call("cancel_ticket", {"user_id": world.customer["id"], "ticket_id": bought["id"]}))
    assert payload(call("my_tickets", {"user_id": world.customer["id"]})) == []
    assert len(payload(call("organizer_events", {"user_id": world.organizer["id"]}))) >= 1


@pytest.mark.parametrize("token", [None, "wrong"])
def test_AC_25_missing_or_wrong_token_is_refused_and_changes_nothing(world, token):
    """AC-25: missing or wrong token is refused and changes nothing"""
    event_id = world.add_event()
    before = world.count_tickets()
    reply = call("buy_ticket", {"user_id": world.customer["id"], "event_id": event_id}, token=token)
    assert "error" in reply and "result" not in reply
    assert world.count_tickets() == before


def test_AC_25_without_MCP_TOKEN_every_tool_call_is_refused(world, monkeypatch):
    """AC-25: without MCP TOKEN every tool call is refused"""
    monkeypatch.delenv("MCP_TOKEN")
    assert "error" in call("list_events", {}, token="")
    assert "error" in call("list_events", {}, token=None)


def test_protocol_basics(world):
    init = server.handle({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "x"}})
    assert init["result"]["capabilities"] == {"tools": {}}
    assert server.handle({"jsonrpc": "2.0", "method": "notifications/initialized"}) is None
    names = [t["name"] for t in server.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})["result"]["tools"]]
    assert len(names) == 8 and "buy_ticket" in names and "find_lecture" in names
    assert server.handle({"jsonrpc": "2.0", "id": 3, "method": "nope"})["error"]["code"] == -32601
    assert call("no_such_tool", {})["error"]["code"] == -32602
    assert "Lecture 5" in call("find_lecture", {"number": 5}, token=None)["result"]["content"][0]["text"]
    assert call("find_lecture", {"number": 99}, token=None)["result"]["isError"] is True
    assert "1." in call("list_lectures", {}, token=None)["result"]["content"][0]["text"]
