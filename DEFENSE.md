# Defence notes

Draft written with Claude from the code. Read it, change anything that is not how you would say it, and answer the last heading yourself.

## What it does

Vibe Tickets lets customers in Madrid buy tickets for club events with a simulated payment. Organizers publish events, can read a poster with a model to fill the form, and see who bought a ticket.

## The three files I will open

1. `app/services/ticket_service.py`, because it holds the buying rules (customers only, not started, one ticket each, not sold out) and knows nothing about HTTP.
2. `app/repositories/ticket_repo.py`, because it is the only place with the SQL, and it inserts only while places are left, in one statement, so two buyers of the last place cannot both win.
3. `app/services/poster.py`, because it is the only file that names the model provider, with a timeout, a fallback and a check of the answer.

## Decisions I can defend

- Stack: FastAPI with plain HTML, CSS and JavaScript. I rejected a JS framework because the screens are small and a build step adds nothing.
- Where the rules live: in `app/services/`. Routes only map results to status codes; the MCP tools call the same services. I rejected rules in routes because the MCP server would then need a copy.
- Authentication and authorization: password with a bcrypt hash and Google sign-in with state and PKCE, both ending in one signed session cookie. Ownership checks are in the service layer (401 not signed in, 403 not yours).
- The model, and why that one: Gemini, because it reads images and has a free tier. The app works without a key.
- What the MCP server exposes, and what it deliberately does not: the same operations as the API, acting as one user through a token; no tool writes SQL and none acts as admin.
- The database shape: users, events and tickets, where tickets is the many-to-many table between customers and events. SQLite locally and Postgres on Neon in production, switched by `DATABASE_URL`. I rejected Render's free Postgres because it is deleted after 30 days.

## How I know it works

The acceptance criteria in `SPEC.md` each have a test whose title contains its id (the Traceability table). `make coverage` gates the service layer at 100% with branches and the whole app at 80%. Coverage shows which code ran, not that the asserts are good. I also looked at the pages in a browser at 380, 768 and 1280 px.

## What is wrong with it

See the ranked list in `READINESS.md`: not deployed yet, the Postgres path not run against a real Postgres, the UI keyboard walk and screenshots missing, no CSRF token.

## The thing in this repository I did not write and cannot explain

Fill this in yourself. A candidate: the small adapter in `app/database.py` that makes a Postgres connection look like a SQLite one (placeholder rewriting and `RETURNING id`), which Claude wrote.
