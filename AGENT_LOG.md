# Agent log

One entry per agent session, newest at the bottom. Be honest: what went wrong is the useful part.

<!-- Copy this block for each session:

## YYYY-MM-DD · <short title>
- Goal:
- Delegated:
- Checkpoints:
- Went wrong:
- Changed by hand:

-->

## 2026-10-20 · Gemini as tutor for the stdio loop
- Goal: understand how to read stdin line by line with readline and why a stdio server must log with console.error.
- Delegated: explanation only, with a tiny example that is not an MCP server. I asked it not to write my server.
- Checkpoints: node mcp-server/check.mjs after each step.
- Went wrong: the first request was cancelled and I had to ask again after /clear.
- Changed by hand: the reading loop, the routing by method, the handlers and the error answers in server.js.

## 2026-10-20 · Gemini CLI connected to my MCP server
- Goal: check that a real agent lists my tools and calls one without being told its name; run the description experiment.
- Delegated: nothing was written by the agent. I only asked "What does lecture 7 cover?" and let it choose the tool.
- Checkpoints: check.mjs 12/12 first, then /mcp (my-project, 2 tools), then the question; Gemini called find_lecture(number: 7).
- Went wrong: nothing blocking. Changing the description to "return lecture" did not change the model's choice.
- Changed by hand: the tool descriptions in server.js, the README notes, package.json with the mcp script.

## 2026-10-20 · Gemini critique of the spec
- Goal: get Gemini to criticize my Non-goals, Goals, Constraints and Acceptance criteria without writing or editing anything.
- Delegated: only the critique, three prompts, on gemini-3.5-flash-lite because it answers in seconds.
- Checkpoints: read every answer and decided which changes went into SPEC.md.
- Went wrong: the first prompt was cancelled while I switched models; /model needed a second Return to confirm.
- Changed by hand: added AC-12 for cancelling a ticket, the event_attendees tool, the test card ending 0000 for declines, a clearer inventory non-goal and a no search or filters non-goal.

## 2026-10-20 · Plan and build slice 1
- Goal: sign-in and the upcoming events list, per SPEC.md slice 1.
- Delegated: plan, PostgreSQL in docker, migration and seed, sign-in with sessions, events list, UI, pytest tests.
- Checkpoints: read the plan, opened the events table (3 rows), requested /events and /api/events without a session, deleted a row and reloaded.
- Went wrong: gemini-3.8-flash took over a minute without answering, so I switched to flash-lite. The first seed failed because the dependencies were not installed. It created a tickets table outside the plan, and its AC-11 test deletes from the development database.
- Changed by hand: re-seeded the database after the test, added .coverage and caches to .gitignore, added a test-database constraint to the spec, and changed Test and Coverage in AGENTS.md to python3 -m pytest because plain pytest is another install without the dependencies.

## 2026-11-03 · Exercise 3: autonomy and checkpoints
- Goal: build the ticket feature through every layer: buying, My tickets, cancelling, the organizer area, the poster reader, the MCP tools and Google sign-in.
- Autonomy: the agent works alone inside one step and runs the tests. It stops before any item in the always-ask list in AGENTS.md, before every commit and push (I make them), and whenever a test would have to change.
- Checkpoints: plan review before code, tests green before each commit, I read every diff, permission prompts for the always-ask list.
- Plan (written by Claude: Gemini could not be reached this session; reviewed by me before any code):
  1. Migration `002_tickets_unique.sql`: unique index on active tickets by (event, customer). `app/errors.py` with one `AppError` (status + message). `ticket_service.py` with buy, my tickets and cancel. `ticket_repo.py` holds the SQL, check and insert in one transaction. Tests first in `tests/test_ticket_rules.py` (AC-2, 3, 4, 12, 15, 16, 17).
  2. `ticket_routes.py`: POST /api/events/{id}/tickets (201), GET /api/tickets, DELETE /api/tickets/{id} (204). One `current_user` dependency (401), one `AppError` handler. Public GET /api/events and /api/events/{id}, and `/` serves the events page. API tests for AC-14, 16, 17.
  3. Register (201, 409, 422) and GET /api/me. Organizer create, edit, delete own events, attendees for the owner only, with 403, 422 and 409 rules in `event_service.py`. Tests for AC-6 and AC-18 to 22.
  4. In parallel: the dark nightclub UI (home, login, register, event, My tickets, organizer), and after step 3 three agents on separate files: `poster.py` (timeout, fallback, fake client), the MCP tools, and Google sign-in with state and PKCE.
  5. Architecture note, logs, `node checks/ex3.mjs`, the comment-out-the-rule proof and the curl checks.
- Review by a second model (Claude agent standing in for Gemini, which I could not reach): it found 8 points. Kept: the race on the last ticket (fixed, see below), the need for a separate role check (already a service rule, customers only), turning IntegrityError into 409 (done). Rejected: 404 instead of 403 for another customer's ticket (the lab requires 403); cutting the parallel scope (the user asked for the whole app). Not done: a test for deleting an event with sold tickets.
- Changed after the review: `ticket_repo.create()` now does the places check and the insert in one SQL statement; the new test AC-2 'two buyers of the last ticket' failed before the change and passes after it.
- Changed in review: the MCP server is ported to Python so tools import the services directly (find_lecture and list_lectures stay); the payment is a demo that always succeeds, so AC-5 and the declined card are removed and there is no card form; organizers cannot buy (403); GET /api/events is public.
- Delegated: three sub-agents, each on its own files: the UI (`app/static/**` only), the Python MCP server (`mcp-server/`, `tests/test_mcp.py`) and Google sign-in (`google_auth.py`, `google_routes.py`). I wrote the poster reader and all rules and tests of steps 2 to 4 myself.
- Went wrong: Gemini could not be reached, so the plan was not critiqued by it. My script that added AC docstrings to the tests broke the indentation of every test file; the next test run caught it and I fixed it. My first AC-2 API test was wrong (the customer already held the ticket) and was rewritten. The UI agent could not open a browser, so the layout at three widths is still unchecked.
- Commits: made by Claude at the user's request (the lab asks the student to make them); the first commit also carries later repository code, so it is larger than one step. The push needs the user's GitHub login.
- What the agent did that I did not ask for: it added `hueFor`, `dateBadge` and `confirmDialog` helpers in `app/static/js/app.js`; stored Google users with a NULL password hash; made the lecture MCP tools skip the token because `check.mjs` calls them without one; removed `mcp-server/server.js`; added `tests/__init__.py`; and changed `GET /` from a redirect to the public events page.

## 2026-11-10 · Posters, show-password, Exercise 4 and 5 gaps
- Goal: show the password on login, store and show poster images, and close the gaps the course checks found (deploy files, health, errors, coverage gates, docs).
- Delegated: all of it to Claude Sonnet 5.5, with tests first for AC-27, AC-28, AC-29 and for the service branches that were not covered. Reading the course pages went to a web-fetch sub-agent.
- Checkpoints: asked me before the Postgres migration, installing psycopg, and pushing; ran the whole test suite after each change; I read the diff.
- Went wrong: Docker was not running, so the Postgres code was never run against a real Postgres. A first edit script failed halfway and was redone.
- False claim by the agent: none found about deployment; nothing is deployed.
- Changed by hand: nothing yet.
- What the agent did that I did not ask for: edited `.github/workflows/ci.yml` (coverage step now uses `make coverage` on `app/`), added a `Makefile`, wrote a draft of `DEFENSE.md`, and ran `python -m app.seed`, which reset the development database.
