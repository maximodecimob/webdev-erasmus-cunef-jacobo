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
