# Usage

One row per agent session. In Gemini CLI, type `/stats` before you quit and copy the input and output tokens. Copilot shows credits instead of tokens: write those in the credits column. The free tier charges nothing, so record what the session **would cost at the provider's published list price**, and note once below the table which price list you used. Leave the cost empty for rows that only show credits.

| Date | Tool | Input tokens | Output tokens | Credits (if no tokens) | List-price cost |
|---|---|---|---|---|---|
| 2026-10-20 | Gemini CLI (tutor: readline, stdout vs stderr) | 81 386 | 2 341 | | $0.03 |
| 2026-10-20 | Gemini CLI (MCP test: find_lecture, description experiment) | 26 949 | 95 | | $0.02 |

Price list used: Google Gemini API list prices, no cache discount: gemini-3.5-flash-lite $0.30 in / $2.50 out per 1M tokens; gemini-3.8-flash $0.75 in / $3.75 out per 1M tokens.
