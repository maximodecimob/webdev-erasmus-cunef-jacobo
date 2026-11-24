See AGENTS.md. It is the single source of instructions for any agent working in this repository. The rules below are for Claude.

## Working rules
- Write only the code the task needs. No speculative features, helpers, options or abstractions, and no comments that repeat the code. A function with one caller stays inline. Delete what you replace.
- Read the existing code before adding code, and reuse what is there.
- Tests first for every rule: write the failing test, watch it fail, then write the code. Never weaken or delete a test to make it pass.
- Business rules live in `app/services/` only. A route calls a service and maps the result to a status code. Only `app/repositories/` writes SQL. MCP tools call the same service functions as the routes.
- Run independent work in parallel with agents. When two tasks touch different files and need nothing from each other (for example the UI and the poster service), start them in the same turn. Agree the API contract first, give each agent its own files, and never let two agents edit the same file. Work that needs another task's result runs after it.
- Run `python3 -m pytest` before saying a step is done, and say what you ran.
- Do not commit, push, install dependencies or edit a migration that already ran: those are in the always-ask list in AGENTS.md.
- UI is plain HTML, CSS and JavaScript. All colours, sizes and spacing come from the design tokens in `app/static/css/styles.css`. Every screen has loading, empty, error and success states.
- The Gemini key is used only in `app/services/poster.py`.
