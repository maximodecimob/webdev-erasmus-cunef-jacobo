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
