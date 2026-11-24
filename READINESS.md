# Readiness report: Vibe Tickets

Status: deployed on Render with the Neon Postgres database, Google sign-in configured and demo data seeded (all checked on 2026-11-24). Every claim has a "How I checked" line.

## Live URL and how to verify it

- Live at https://vibe-tickets-jacobo.onrender.com (Render free web service, Ohio, built from the `Dockerfile`).
- Once live: `curl https://vibe-tickets-jacobo.onrender.com/health` must print `{"status":"ok","db":"ok"}`, then register a test account and sign in (the live database has no seeded accounts).
- How I checked: `curl https://vibe-tickets-jacobo.onrender.com/health` returned 200 `{"status":"ok","db":"ok"}` on 2026-11-10; `test_AC_28` covers the 503 case. On 2026-11-24 the live `/api/events` listed the 3 seeded events (so it reads Neon, not an empty temporary SQLite), `/auth/google` redirected to accounts.google.com (not "google_not_configured"), and the login cookie came back `HttpOnly; Secure; SameSite=lax`.

## Environment variables

| Name | Purpose | Source | Secret |
|---|---|---|---|
| SESSION_SECRET | signs session cookies; the app refuses to start without it | random string you make | yes |
| DATABASE_URL | Neon Postgres connection string; without it the app uses SQLite | Neon console | yes |
| DATABASE_PATH | SQLite file, local development only | default `vibe_tickets.db` | no |
| PUBLIC_BASE_URL | base of the Google redirect URI | the Render URL | no |
| GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET | Google sign-in | Google Cloud console | secret, and the id is not |
| GEMINI_API_KEY / MODEL_NAME | poster reader; optional, the app works without it | aistudio.google.com | yes |
| MCP_TOKEN | ordinary session token of the one user the MCP server acts as | the `vibe_session` cookie value of that user | yes |

How I checked: `.env.example` lists all of them; `app/utils.py` raises "SESSION_SECRET is not set" when it is empty.

## What happens when things fail

- Database down: `/health` answers 503 `{"status":"error","db":"down"}`; other API calls answer 500 with "Something went wrong on our side. Please try again." and the details go to the server log. Checked by `test_AC_28` and `test_AC_29`.
- Broken JSON: 400 "The request body is not valid JSON". Unauthenticated write: 401. Another user's event: 403. Checked by `test_AC_29` and the AC-21 tests.
- Unknown page: 404 `{"error":"Page not found"}`. No stack trace is ever sent to the client.
- Bad deploy and rollback: not yet timed; to do on Render. Render now checks `/health` and restarts the service if it fails.
- Model provider down or no key: the poster form stays empty with a note (AC-8, AC-23).

## Four states of one screen

The events list (`app/static/events.html`) has a loading skeleton, an empty message ("No upcoming events yet"), an error box with a Retry button and the list itself. How I checked: read the code; screenshots are still to do (see known gaps).

## Request waterfall

Not measured yet. To do on the live site with the browser's Network tab.

## Security basics checked

- Secrets: `.env` is in `.gitignore` and not tracked (`git ls-files .env` prints nothing). A search of the git history for real keys is still to do.
- Authorization: every write route calls a service that checks the role and the owner (401 without a session, 403 for another user). Checked by AC-16, AC-21 and AC-27 tests.
- Session cookie: HttpOnly, SameSite=Lax, and Secure when `PUBLIC_BASE_URL` is https (`test_AC_31`). HTTPS comes with Render. No CSRF token: SameSite=Lax is the only protection.
- MCP: acts as the one user of `MCP_TOKEN`, no user id argument, so a token holder cannot act as anyone else (`test_AC_30`).

## Known gaps, ranked by risk

1. Auto-Deploy is set to "After CI Checks Pass" (2026-11-24) but not yet proven with a deliberately failing test, and a rollback has not been timed. Next step: push a failing test, watch Render hold the deploy, then fix it.
2. Postgres: the suite was run against a throwaway Neon `dev` branch on 2026-11-10 (70 of 71 passed, the one failure was fixed); it has not been re-run on Postgres since. Next step: `TEST_DATABASE_URL=... python -m pytest`.
3. UI evidence is in `docs/ui/` (four states of the events screen and the poster reader thinking and failing, 2026-11-24). The loading and error shots were produced by stalling or rejecting `fetch` in the page, not by a real outage.
4. No CSRF token on the cookie session. Next step: a token on the write routes.
5. No review of a classmate's project (Exercise 5) yet.
6. The live demo accounts use a publicly known password (`secret123`). Next step: change both passwords before the defence.
7. The free Render service sleeps after 15 minutes, so the first request can take about a minute; open the site before the demo.

## Model feature

- What leaves the app: only the poster image the organizer uploads, sent to the Gemini API from `app/services/poster.py`. No emails or ticket data.
- Cost: not measured; the free Gemini tier charges nothing.
- Provider down, slow or no key: 30 s timeout, then the fields stay empty with a note; the answer is re-checked before it fills the form (AC-8, AC-23).

## MCP

- Tools: see the table in `SPEC.md`. Each one calls the same service function as the HTTP route.
- Who may call: only the one user whose session token is in `MCP_TOKEN`; the token grants what that user can do over HTTP, never admin, and no tool takes a user id (AC-24, AC-25, AC-30).
- Not deployed: it is a stdio server started by the agent on the developer's machine.
