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

## Constraints
- Python 3.12 with FastAPI, PostgreSQL, and plain HTML, CSS and JavaScript in the UI.
- Passwords are stored only as a hash, never as readable text.
- Payments are simulated in our own code: no payment provider is called, and no database column, form field or log line holds a card number.
- No secret is committed: .env.example holds placeholders only, and node checks/ex2.mjs finds no secret in the repository.
- Every schema change is a numbered migration file.
- Automated tests run against a separate test database and never delete rows from the development database.

## The model feature
- Model: Gemini 2.5 Flash with vision, called from services/poster.py and nowhere else.
- Input: the poster image an organizer uploads, and nothing about any customer. The image is the only data that leaves the app.
- Output: a suggested title, date, venue and price, shown in the event form for the organizer to correct.
- When it fails: no key, a timeout of 10 seconds or a 429 all leave the form empty with a note saying to type the details in. Nothing is saved until the organizer presses save, and a date the model returns that does not parse is left blank rather than guessed.

## Auth
- Local: e-mail and password, stored as a bcrypt hash.
- Provider: Sign in with Google, the authorization-code flow on the server with state and PKCE.
- Linking: matched on the e-mail only when Google marks it as verified, so one person stays one account and ends in the same session cookie. An address Google has not verified is never linked to an existing account.

## MCP tools
| Tool | What it does | Who may call it |
| --- | --- | --- |
| `upcoming_events` | Lists future events with title, venue, date, price and the number of tickets left in each | anyone |
| `my_tickets` | Lists the tickets of the signed-in customer with their codes and event dates | the token's owner |
| `buy_ticket` | Buys one ticket for an event with a simulated payment, refusing a sold-out event | the token's owner |
| `cancel_ticket` | Cancels one of the token owner's own tickets and frees the place | the token's owner |
| `event_attendees` | Lists the customers who hold a ticket for one of the organizer's own events | an organizer |
| `read_poster` | Reads an event poster image and suggests title, date, venue and price for the organizer | an organizer |

## UI
Plain HTML, CSS and JavaScript served by FastAPI, with design tokens in one CSS file. Four screens: sign in, the list of upcoming events, one event with its buy button, and my tickets. The checklist is in docs/UI.md.

## Architecture
<!-- Exercise 3. One request traced through every layer, naming the file for each one,
     plus one place where your own code does not match this layering. -->

## Acceptance criteria
- [AC-1] A signed-in customer who opens /events sees only events whose date is in the future, each with title, venue, date, price and tickets left.
- [AC-2] A customer who buys a ticket for a sold-out event sees "This event is sold out", and no new row appears in the tickets table.
- [AC-3] A customer who buys a ticket for an event with free places sees it in My tickets with a unique code, and the tickets left of that event drop by one.
- [AC-4] A customer who already holds a ticket for an event and presses buy again gets 409 and still has one row in tickets.
- [AC-5] A customer who pays with the test card ending 0000 sees "Payment declined", and no new row appears in the tickets table.
- [AC-6] An organizer who opens one of their events sees the customers who hold a ticket for it, and a customer who opens the same event does not see that list.
- [AC-7] Signing in with Google using an address that already has a password account signs into that account, and no second row appears in users.
- [AC-8] With no model key set, uploading a poster leaves the form fields empty and shows the note to type the details in.
- [AC-12] A customer who cancels their own ticket before the event starts sees it removed from My tickets, and the tickets left of that event rise by one.

### Slice 1: sign-in and the upcoming events list
- [AC-9] A visitor who opens /events without signing in lands on /login instead.
- [AC-10] After signing in with a seeded account, /events shows the three seeded events, each with its title, date and tickets left (tickets left equals the total places until purchases exist).
- [AC-11] Deleting one event row in the database and reloading /events removes that event from the screen.

## Traceability
<!-- Filled in from Exercise 3 onward: each AC id, and the test that names it. -->
| Criterion | Test |
| --- | --- |
| AC-1 | (from Exercise 3) |

## Spec vs result
- Passed: AC-9 (/events without a session redirects to /login with 303 and /api/events returns 401), AC-10 (a seeded customer sees the three seeded events with title, date and tickets left), AC-11 (after deleting one event row in the database the list shows two events).
- Missed or reinterpreted: the agent also created a tickets table in the first migration, which belongs to a later slice, and claimed it was in the plan. Its AC-11 test deletes a row from the development database instead of using a separate test database, so I had to re-seed by hand. Tickets left shows the total places because nothing can be bought yet.
- Changed: added the constraint that tests run against a separate test database, and AC-10 now says tickets left equals the total places until purchases exist. The test database itself is still to do in Exercise 3.
