# Readiness report: Vibe Tickets

Status: deployed on Render, but still on temporary SQLite until `DATABASE_URL` (Neon) is set there, so data is lost on every redeploy. Every claim has a "How I checked" line.

## Live URL and how to verify it

- Live at https://vibe-tickets-jacobo.onrender.com (Render free web service, Ohio, built from the `Dockerfile`).
- Once live: `curl https://vibe-tickets-jacobo.onrender.com/health` must print `{"status":"ok","db":"ok"}`, then register a test account and sign in (the live database has no seeded accounts).
- How I checked: `curl https://vibe-tickets-jacobo.onrender.com/health` returned 200 `{"status":"ok","db":"ok"}` on 2026-11-10; `test_AC_28` covers the 503 case.

## Environment variables

| Name | Purpose | Source | Secret |
|---|---|---|---|
| SESSION_SECRET | signs session cookies; the app refuses to start without it | random string you make | yes |
| DATABASE_URL | Neon Postgres connection string; without it the app uses SQLite | Neon console | yes |
| DATABASE_PATH | SQLite file, local development only | default `vibe_tickets.db` | no |
| PUBLIC_BASE_URL | base of the Google redirect URI | the Render URL | no |
| GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET | Google sign-in | Google Cloud console | secret, and the id is not |
| MCP_TOKEN | session token the MCP server acts with | a signed session token | yes |

How I checked: `.env.example` lists all of them; `app/utils.py` raises "SESSION_SECRET is not set" when it is empty.

## What happens when things fail

- Database down: `/health` answers 503 `{"status":"error","db":"down"}`; other API calls answer 500 with "Something went wrong on our side. Please try again." and the details go to the server log. Checked by `test_AC_28` and `test_AC_29`.
- Broken JSON: 400 "The request body is not valid JSON". Unauthenticated write: 401. Another user's event: 403. Checked by `test_AC_29` and the AC-21 tests.
- Unknown page: 404 `{"error":"Page not found"}`. No stack trace is ever sent to the client.
- Bad deploy and rollback: not yet timed; to do on Render.

## Four states of one screen

The events list (`app/static/events.html`) has a loading skeleton, an empty message ("No upcoming events yet"), an error box with a Retry button and the list itself. How I checked: read the code; screenshots are still to do (see known gaps).

## Request waterfall

Not measured yet. To do on the live site with the browser's Network tab.

## Security basics checked

- Secrets: `.env` is in `.gitignore` and not tracked (`git ls-files .env` prints nothing). A search of the git history for real keys is still to do.
- Authorization: every write route calls a service that checks the role and the owner (401 without a session, 403 for another user). Checked by AC-16, AC-21 and AC-27 tests.
- Not done: HTTPS (comes with Render), cookie flags not reviewed in this report, no CSRF token.

## Known gaps, ranked by risk

1. Render runs on temporary SQLite: `DATABASE_URL` for the Neon production branch is not set there yet, and Google sign-in is not configured on the live site. Next step: set `DATABASE_URL`, `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in Render.
2. The Postgres path has not been run against a real Postgres (Docker was not running when it was written), only SQLite is tested. Next step: run `DATABASE_URL=... python -m pytest` against a throwaway Postgres.
3. UI items not measured: contrast, widths 380/768/1280, 44 px touch targets, keyboard-only flow, screenshots. Next step: measure and tick in `docs/UI.md`.
4. No CSRF token on the cookie session. Next step: SameSite cookie check or token.
5. No review of a classmate's project (Exercise 5) yet.

## Model feature

- There is none: the app has no model feature, so no user data leaves the app for a model provider and there is no provider cost or outage to handle.

## MCP

- Tools: see the table in `SPEC.md`. Each one calls the same service function as the HTTP route.
- Who may call: only the user the `MCP_TOKEN` belongs to; the token grants what that user can do over HTTP, never admin (AC-24, AC-25).
- Not deployed: it is a stdio server started by the agent on the developer's machine.
