# Vibe Tickets

## Project option
Club events.

## Non-goals
- No real payments: payments are simulated, no real money moves and no card number is ever stored.
- No ticket resale or transfers between users.
- No split payments or group bookings.
- No staff scheduling or payroll features.
- No venue inventory such as drinks or merchandise, and no bar management. Ticket stock per event is allowed.
- No chat or messaging between users.
- No search, filters, sorting or favorites in v1: the events list is one chronological list.
- No event recommender and no text generator in v1: the only model feature is the poster reader.

## Goals
- A customer signs in, sees the upcoming club events in Madrid with the number of tickets left, and buys a ticket with a simulated payment.
- A venue organizer creates an event with a price and a limit of tickets, and sees which customers bought a ticket for it.
- A customer sees their own tickets, each with a unique code, and can cancel one before the event starts.
- Anyone, signed in or not, sees the upcoming events on the home page; buying needs an account, so every ticket belongs to a user.

## Constraints
- Python 3.12 with FastAPI, SQLite (one local file, path in `DATABASE_PATH`), and plain HTML, CSS and JavaScript in the UI.
- Passwords are stored only as a hash, never as readable text.
- Payments are simulated in our own code: no payment provider is called, and no database column, form field or log line holds a card number.
- No secret is committed: .env.example holds placeholders only, and node checks/ex2.mjs finds no secret in the repository.
- Every schema change is a numbered migration file.
- Automated tests run against a separate test database and never delete rows from the development database.

## The model feature
- Model: Gemini 2.5 Flash with vision, called from services/poster.py and nowhere else.
- Input: the poster image an organizer uploads, and nothing about any customer. The image is the only data that leaves the app.
- Output: a suggested title, date, venue and price, shown in the event form for the organizer to correct.
- When it fails: no key, a timeout of 30 seconds or a 429 all leave the form empty with a note saying to type the details in. Nothing is saved until the organizer presses save, and a date the model returns that does not parse is left blank rather than guessed.

## Auth
- Local: e-mail and password, stored as a bcrypt hash.
- Provider: Sign in with Google, the authorization-code flow on the server with state and PKCE.
- Linking: matched on the e-mail only when Google marks it as verified, so one person stays one account and ends in the same session cookie. An address Google has not verified is never linked to an existing account.

## MCP tools
| Tool | What it does | Who may call it |
| --- | --- | --- |
| `list_events` | Lists future events with title, venue, date, price and the number of tickets left in each | anyone |
| `my_tickets` | Lists the tickets of the signed-in customer with their codes and event dates | the token's owner |
| `buy_ticket` | Buys one ticket for an event with a simulated payment, refusing a sold-out event | the token's owner |
| `cancel_ticket` | Cancels one of the token owner's own tickets and frees the place | the token's owner |
| `get_event` | Shows one event with its tickets left | anyone with the token |
| `organizer_events` | Lists the organizer's own events with tickets sold | an organizer |

## UI
Plain HTML, CSS and JavaScript served by FastAPI, with design tokens in one CSS file. Dark nightclub look: near-black background, violet and magenta accents, large event cards. Six screens: the public home with the list of upcoming events and a Log in button on each, sign in, register, one event with its buy button (and, for its organizer, the buyers), my tickets, and the organizer's own events with the poster reader. The checklist is in docs/UI.md.

## Architecture
One request traced through the layers: a customer presses "Pay" on /events/3.
- Browser, going out: the view is `app/static/event.html`. Its state lives in three script variables (`ev` the event, `me` the signed-in user, `busy` while paying). The Pay button calls `api()` in `app/static/js/app.js`, the one function that makes every REST call (`POST /api/events/3/tickets`, session cookie sent by the browser).
- Route: `app/routes/ticket_routes.py` `buy()` takes the user from `current_user` (`app/deps.py`, 401 without a session) and calls the service; it holds no rule.
- Service: `app/services/ticket_service.py` `buy_ticket()` holds the rules in this order: customers only (403), event exists (404), not started (409), one active ticket per customer (409), places left (409 "This event is sold out"). Failures are `AppError` subclasses from `app/errors.py`.
- Repository: `app/repositories/ticket_repo.py` and `event_repo.py` hold the SQL (`?` placeholders) and open one connection per call (`app/database.py`): SQLite locally, Postgres when `DATABASE_URL` is set.
- Database: `tickets` in `app/migrations/001_initial_schema.sql`; `002_tickets_unique.sql` adds a unique index on active tickets, so two clicks at once cannot create two rows.
- Back out: `AppError` is turned into `{"error": "<sentence>"}` with its status by the handler in `app/main.py`. In the browser `api()` throws an Error with that sentence, and `event.html` shows it in the dialog (error state) or the ticket code (success state), then `renderEvent()` redraws from `ev`.
- Rule against overselling: `ticket_repo.create()` inserts only while active tickets are below `total_tickets`, in one statement, so two buyers of the last place cannot both succeed; the service turns a refused insert into 409.
- The MCP server (`mcp-server/server.py`) calls the same services, so it cannot bypass a rule.
- Where my code does not match the layering: `app/routes/auth_routes.py` `login_action` builds the session cookie and the HTML error page itself instead of leaving that to a service, because it came from the slice-1 code and I left it unchanged.

### Screens: where each is rendered
| Screen | Rendered | Why | While waiting |
|---|---|---|---|
| Events (`/events`) | browser, from `/api/events` | the same JSON serves the page and the MCP tools, and a page of static HTML needs no server templates | skeleton cards |
| Event (`/events/{id}`) | browser | the buy dialog and tickets-left update without reloading | skeleton block |
| Login, Register | server sends static HTML, the form posts with `fetch` | errors show in place without losing what was typed | "Signing in..." spinner |
| My tickets | browser | cancelling removes a row without reloading | skeleton rows |
| Organizer | browser | the poster reader fills the form after a slow model call | "Reading the poster..." spinner |

## Acceptance criteria
- [AC-1] A signed-in customer who opens /events sees only events whose date is in the future, each with title, venue, date, price and tickets left.
- [AC-2] A customer who buys a ticket for a sold-out event sees "This event is sold out", and no new row appears in the tickets table.
- [AC-3] A customer who buys a ticket for an event with free places sees it in My tickets with a unique code, and the tickets left of that event drop by one.
- [AC-4] A customer who already holds a ticket for an event and presses buy again gets 409 and still has one row in tickets.
- [AC-6] An organizer who opens one of their events sees the customers who hold a ticket for it, and a customer who opens the same event does not see that list.
- [AC-7] Signing in with Google using an address that already has a password account signs into that account, and no second row appears in users.
- [AC-8] With no model key set, uploading a poster leaves the form fields empty and shows the note to type the details in.
- [AC-12] A customer who cancels their own ticket before the event starts sees it removed from My tickets, and the tickets left of that event rise by one.

### Slice 1: sign-in and the upcoming events list
- [AC-9] A visitor who opens /events without signing in lands on /login instead.
- [AC-10] After signing in with a seeded account, /events shows the three seeded events, each with its title, date and tickets left (tickets left equals the total places until purchases exist).
- [AC-11] Deleting one event row in the database and reloading /events removes that event from the screen.

### Slice 2: the public home, buying, My tickets and cancelling
- [AC-13] A visitor who is not signed in opens / and sees the upcoming events with title, venue, date, price and tickets left, each with a "Log in to buy" button that leads to /login.
- [AC-14] A visitor who sends the buy request with no session gets 401, and no new row appears in tickets.
- [AC-15] A customer sees in My tickets only their own tickets, each with its code, event title and date, and never a ticket of another customer.
- [AC-16] A customer who cancels a ticket that belongs to another customer gets 403 and that ticket stays active; the same request with no session gets 401.
- [AC-17] A customer who cancels a ticket of an event that has already started gets 409 and the ticket stays active.
- [AC-26] An organizer who tries to buy a ticket gets 403, and no new row appears in tickets.

### Slice 3: accounts and the organizer area
- [AC-18] A visitor registers with an e-mail, a password of at least 8 characters and the role customer or organizer, and is signed in; an e-mail that already exists gets 409 and no second row appears in users.
- [AC-19] An organizer creates an event with title, venue, a future date, a price of 0 or more and at least 1 ticket, and sees it in their own events; a customer sending the same request gets 403.
- [AC-20] Creating or editing an event with a past date, a negative price or fewer than 1 ticket gets 422 and nothing changes in events.
- [AC-21] An organizer who edits or deletes an event of another organizer gets 403 and the event is unchanged.
- [AC-22] An organizer who lowers the total tickets of an event below the number already sold gets 409 and the event is unchanged.

### Slice 4: the poster reader
- [AC-23] A poster answer that is not valid JSON, or whose date does not parse, is ignored: the date field stays empty and the other valid fields are still filled. A good answer fills the four fields.

- [AC-27] A poster image uploaded by the organizer of an event is saved with the event, shown on the event cards and the event page, and served by `/api/events/{id}/poster`. A file that is not an image gets 422, and another user gets 403; nothing is stored in either case.

### Slice 6: running in production
- [AC-28] `/health` answers 200 `{"status":"ok","db":"ok"}`, and 503 `{"status":"error","db":"down"}` when the database cannot be reached.
- [AC-29] An unknown page gets 404 "Page not found", a request body that is not valid JSON gets 400, and other bad input gets 422, each as one readable sentence with no stack trace.

### Slice 5: the MCP tools
- [AC-24] An MCP tool and the API route give the same result for the same user, because both call the same service function: list_events lists what /api/events lists, buy_ticket creates a ticket that /api/tickets then shows, and buy_ticket refuses a sold-out event.
- [AC-25] An MCP tool call with no token or with an invalid token is refused and changes nothing.

## Traceability
<!-- Filled in from Exercise 3 onward: each AC id, and the test that names it. -->
| Criterion | Test |
| --- | --- |
| AC-1 | (from Exercise 3) |
| AC-13 | test_ticket_api.py::test_AC_13_visitor_sees_upcoming_events_and_the_home_page_without_login |
| AC-14 | test_ticket_api.py::test_AC_14_buying_without_a_session_is_401_and_creates_nothing |
| AC-15 | test_ticket_rules.py::test_AC_15_my_tickets_lists_only_the_customers_own_tickets |
| AC-16 | test_ticket_api.py::test_AC_16_cancel_without_session_is_401_and_other_customers_ticket_is_403, test_ticket_rules.py::test_AC_16_cancelling_another_customers_ticket_is_refused |
| AC-17 | test_ticket_api.py::test_AC_17_cancelling_a_started_event_is_409, test_ticket_rules.py::test_AC_17_a_ticket_of_an_event_that_started_cannot_be_cancelled |
| AC-18 | test_organizer_api.py::test_AC_18_register_signs_the_user_in, test_organizer_api.py::test_AC_18_duplicate_email_is_409_and_adds_no_row (+1) |
| AC-19 | test_organizer_api.py::test_AC_19_organizer_creates_an_event_and_sees_it_in_their_list, test_organizer_api.py::test_AC_19_customer_creating_an_event_is_403_and_visitor_401 |
| AC-20 | test_organizer_api.py::test_AC_20_invalid_events_are_422_and_change_nothing |
| AC-21 | test_organizer_api.py::test_AC_21_another_organizers_event_cannot_be_edited_or_deleted |
| AC-22 | test_organizer_api.py::test_AC_22_lowering_total_below_sold_is_409 |
| AC-23 | test_poster.py::test_AC_23_a_good_answer_fills_the_four_fields, test_poster.py::test_AC_23_an_answer_that_is_not_json_is_ignored (+1) |
| AC-24 | test_mcp.py::test_AC_24_mcp_list_events_equals_the_api, test_mcp.py::test_AC_24_mcp_buy_ticket_shows_up_in_the_api_and_errors_are_tool_results (+1) |
| AC-25 | test_mcp.py::test_AC_25_missing_or_wrong_token_is_refused_and_changes_nothing, test_mcp.py::test_AC_25_without_MCP_TOKEN_every_tool_call_is_refused |
| AC-26 | test_ticket_api.py::test_AC_26_an_organizer_buying_is_403, test_ticket_rules.py::test_AC_26_an_organizer_cannot_buy_a_ticket |
| AC-27 | test_organizer_api.py::test_AC_27_an_uploaded_poster_is_served_and_flagged_on_the_event (+2) |
| AC-28 | test_organizer_api.py::test_AC_28_health_reports_ok_and_503_when_the_database_is_down |
| AC-29 | test_organizer_api.py::test_AC_29_errors_are_one_readable_sentence_never_a_stack_trace |

## Spec vs result
- Passed: AC-9 (/events without a session redirects to /login with 303 and /api/events returns 401), AC-10 (a seeded customer sees the three seeded events with title, date and tickets left), AC-11 (after deleting one event row in the database the list shows two events).
- Missed or reinterpreted: the agent also created a tickets table in the first migration, which belongs to a later slice, and claimed it was in the plan. Its AC-11 test deletes a row from the development database instead of using a separate test database, so I had to re-seed by hand. Tickets left shows the total places because nothing can be bought yet.
- Changed: added the constraint that tests run against a separate test database, and AC-10 now says tickets left equals the total places until purchases exist. The test database itself is still to do in Exercise 3.
- Changed in Exercise 3: removed AC-5 (the declined test card). The payment is only a demo: the buyer confirms a simulated payment that always succeeds, with no card form and no payment error message. Slices 2 to 5 added (AC-13 to AC-25), the database is SQLite, and `/api/events` is public because the home page is public.
