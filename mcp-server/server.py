"""Vibe Tickets MCP server: JSON-RPC 2.0 over stdio, one JSON message per line.

Tools: find_lecture and list_lectures (Exercise 1, read lectures.json) plus list_events, get_event,
my_tickets, buy_ticket, cancel_ticket and organizer_events, which call the same services as the HTTP API.

Authentication (AC-25): the server reads MCP_TOKEN from the environment. Every call to a Vibe Tickets
tool must carry the same value in params.arguments.token, compared with hmac.compare_digest. A missing
or wrong token, or an unset MCP_TOKEN, gives a JSON-RPC error (-32001) and no service is called.
tools/list stays open. The two lecture tools read a public local file, not the database, so they need no token.
The tools that act for a user take user_id; the service applies the same rules as the API for that user.
"""
import hmac
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from app.errors import AppError  # noqa: E402
from app.repositories.user_repo import UserRepository  # noqa: E402
from app.services import organizer_service, ticket_service  # noqa: E402
from app.services.event_service import EventService  # noqa: E402

with open(os.path.join(HERE, "lectures.json"), encoding="utf-8") as f:
    LECTURES = json.load(f)


def _int(name, description):
    return {name: {"type": "integer", "description": description}}


def _schema(props=None):
    return {"type": "object", "properties": props or {}, "required": list(props or {})}


USER = _int("user_id", "Id of the user the tool acts for")
EVENT = _int("event_id", "Id of the event")
TOOLS = [
    ("find_lecture", "Return the title and topics of one course lecture by its number, 1 to 12. Use it when asked what a lecture covers.",
     _schema(_int("number", "Lecture number, 1 to 12"))),
    ("list_lectures", "List the number and title of every course lecture. Use it when asked what the course covers.", _schema()),
    ("list_events", "List the upcoming club events with venue, date, price and tickets left. Use it to see what can be bought.", _schema()),
    ("get_event", "Return one event by id with venue, date, price and tickets left.", _schema(EVENT)),
    ("my_tickets", "List the active tickets of a customer, with event title, date and ticket code.", _schema(USER)),
    ("buy_ticket", "Buy one ticket for an event as a customer. Fails if sold out, started, or already held.", _schema({**USER, **EVENT})),
    ("cancel_ticket", "Cancel a ticket that belongs to the user, before its event starts.", _schema({**USER, **_int("ticket_id", "Id of the ticket")})),
    ("organizer_events", "List the events of an organizer with tickets sold and left. Customers are refused.", _schema(USER)),
]
LECTURE_TOOLS = ("find_lecture", "list_lectures")


def _user(args):
    user = UserRepository.get_by_id(args.get("user_id"))
    if user is None:
        raise AppError("User not found")
    return user


def run_tool(name, args):
    """Run one tool and return the text of its result. Raises AppError when a rule refuses it."""
    if name == "find_lecture":
        lecture = next((l for l in LECTURES if l["number"] == args.get("number")), None)
        if lecture is None:
            raise AppError(f"There is no lecture {args.get('number')}. The course has lectures 1 to 12.")
        return f"Lecture {lecture['number']}: {lecture['title']}. Topics: {lecture['topics']}"
    if name == "list_lectures":
        return "\n".join(f"{l['number']}. {l['title']}" for l in LECTURES)
    if name == "list_events":
        data = EventService.list_upcoming_events()
    elif name == "get_event":
        data = EventService.get_event(args.get("event_id"))
    elif name == "my_tickets":
        data = ticket_service.my_tickets(_user(args))
    elif name == "buy_ticket":
        data = ticket_service.buy_ticket(_user(args), args.get("event_id"))
    elif name == "cancel_ticket":
        ticket_service.cancel_ticket(_user(args), args.get("ticket_id"))
        data = {"cancelled": args.get("ticket_id")}
    else:
        data = organizer_service.list_own(_user(args))
    return json.dumps(data, default=str)


def _reply(id, **body):
    return {"jsonrpc": "2.0", "id": id, **body}


def _authorized(args):
    expected, given = os.environ.get("MCP_TOKEN"), args.get("token")
    return bool(expected) and isinstance(given, str) and hmac.compare_digest(given.encode(), expected.encode())


def handle(msg):
    """Return the reply for one message, or None for a notification."""
    method, id, params = msg.get("method"), msg.get("id"), msg.get("params") or {}
    if method == "initialize":
        return _reply(id, result={"protocolVersion": params.get("protocolVersion"), "capabilities": {"tools": {}},
                                  "serverInfo": {"name": "vibe-tickets", "version": "0.2.0"}})
    if method == "tools/list":
        return _reply(id, result={"tools": [{"name": n, "description": d, "inputSchema": s} for n, d, s in TOOLS]})
    if method == "tools/call":
        name, args = params.get("name"), dict(params.get("arguments") or {})
        if name not in [t[0] for t in TOOLS]:
            return _reply(id, error={"code": -32602, "message": f"Unknown tool: {name}"})
        if name not in LECTURE_TOOLS and not _authorized(args):
            return _reply(id, error={"code": -32001, "message": "Unauthorized: missing or invalid token"})
        args.pop("token", None)
        try:
            text, is_error = run_tool(name, args), False
        except AppError as error:
            text, is_error = error.message, True
        return _reply(id, result={"content": [{"type": "text", "text": text}], "isError": is_error})
    if id is not None:
        return _reply(id, error={"code": -32601, "message": f"Unknown method: {method}"})
    return None


def main():
    for line in sys.stdin:
        if line.strip():
            reply = handle(json.loads(line))
            if reply:
                sys.stdout.write(json.dumps(reply) + "\n")
                sys.stdout.flush()


if __name__ == "__main__":
    main()
