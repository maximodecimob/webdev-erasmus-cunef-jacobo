# Readiness report: Vibe Tickets

Status: the code is ready to deploy, the deployment itself is not done yet. Every claim has a "How I checked" line.

## Live URL and how to verify it

- Not live yet. `course.json` `liveUrl` is empty until the Render service exists.
- Once live: `curl https://<name>.onrender.com/health` must print `{"status":"ok","db":"ok"}`, then sign in with the seeded accounts (`customer@vibe.test`, `organizer@vibe.test`).
- How I checked: `/health` is covered by `test_AC_28` in `tests/test_organizer_api.py`; the live check is still to do.

## Environment variables

| Name | Purpose | Source | Secret |
|---|---|---|---|
| SESSION_SECRET | signs session cookies; the app refuses to start without it | random string you make | yes |
| DATABASE_URL | Neon Postgres connection string; without it the app uses SQLite | Neon console | yes |
| DATABASE_PATH | SQLite file, local development only | default `vibe_tickets.db` | no |
| PUBLIC_BASE_URL | base of the Google redirect URI | the Render URL | no |
| GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET | Google sign-in | Google Cloud console | secret, and the id is not |
| GEMINI_API_KEY / MODEL_NAME | poster reader; optional, the app works without it | aistudio.google.com | yes |
| MCP_TOKEN | session token the MCP server acts with | a signed session token | yes |

How I checked: `.env.example` lists all of them; `app/utils.py` raises "SESSION_SECRET is not set" when it is empty.

## What happens when things fail

- Database down: `/health` answers 503 `{"status":"error","db":"down"}`; other API calls answer 500 with "Something went wrong on our side. Please try again." and the details go to the server log. Checked by `test_AC_28` and `test_AC_29`.
- Broken JSON: 400 "The request body is not valid JSON". Unauthenticated write: 401. Another user's event: 403. Checked by `test_AC_29` and the AC-21 tests.
- Unknown page: 404 `{"error":"Page not found"}`. No stack trace is ever sent to the client.
- Bad deploy and rollback: not yet timed; to do on Render.
- Model provider down or no key: the poster form stays empty with a note (AC-8, AC-23).

## Four states of one screen

The events list (`app/static/events.html`) has a loading skeleton, an empty message ("No upcoming events yet"), an error box with a Retry button and the list itself. How I checked: read the code; screenshots are still to do (see known gaps).

## Request waterfall

Not measured yet. To do on the live site with the browser's Network tab.

## Security basics checked

- Secrets: `.env` is in `.gitignore` and not tracked (`git ls-files .env` prints nothing). A search of the git history for real keys is still to do.
- Authorization: every write route calls a service that checks the role and the owner (401 without a session, 403 for another user). Checked by AC-16, AC-21 and AC-27 tests.
- Not done: HTTPS (comes with Render), cookie flags not reviewed in this report, no CSRF token.

## Known gaps, ranked by risk

1. Not deployed: no Render service, no Neon database. Next step: create both, set the environment variables, set `liveUrl`.
2. The Postgres path has not been run against a real Postgres (Docker was not running when it was written), only SQLite is tested. Next step: run `DATABASE_URL=... python -m pytest` against a throwaway Postgres.
3. UI items not measured: contrast, widths 380/768/1280, 44 px touch targets, keyboard-only flow, screenshots. Next step: measure and tick in `docs/UI.md`.
4. No CSRF token on the cookie session. Next step: SameSite cookie check or token.
5. No review of a classmate's project (Exercise 5) yet.

## Model feature

- What leaves the app: only the poster image the organizer uploads, sent to the Gemini API from `app/services/poster.py`. No emails or ticket data.
- Cost: not measured; the free Gemini tier charges nothing.
- Provider down, slow or no key: 30 s timeout, then the fields stay empty with a note; the answer is re-checked before it fills the form (AC-8, AC-23).

## MCP

- Tools: see the table in `SPEC.md`. Each one calls the same service function as the HTTP route.
- Who may call: only the user the `MCP_TOKEN` belongs to; the token grants what that user can do over HTTP, never admin (AC-24, AC-25).
- Not deployed: it is a stdio server started by the agent on the developer's machine.
