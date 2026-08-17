# Python migration behavior baseline

This document freezes the behavior that the Python replacement must preserve
before the TypeScript Telegram bot can be removed.

## Public HTTP contract

- `GET /api/quality-costs` returns costs grouped by confidential editor
  codename and quality tier.
- `POST /api/edit` accepts JSON fields `imageBase64`, `instruction`, `quality`,
  and `editor`.
- Missing/non-string image or instruction fields return HTTP 400.
- An unknown editor codename returns HTTP 400.
- Provider/edit failures return HTTP 502.
- Successful edits return a PNG data URL plus the true `width` and `height`.
- Real editor and prompt-engineer identifiers are never returned to clients.

## Telegram contract

1. `/start` explains how to submit an edit.
2. A photo caption is treated as the edit instruction.
3. A photo without a caption is retained while the bot asks for an instruction.
4. The user selects `Studio 1` or `Studio 2`, then `Natural` or `Upscale`.
5. Prices displayed on quality buttons come from the selected editor.
6. The edited PNG is sent as a document to avoid Telegram photo compression.
7. Pending conversation state is in memory and scoped by chat ID.

## Production lifecycle contract

- Only PM2 may run the production Telegram bot.
- The PM2 application name is `ai-bot` and it has exactly one instance.
- A second process on the same host is rejected by an operating-system lock.
- A Telegram `409 Conflict` is logged as a duplicate poller and exits without
  entering a PM2 restart loop.
- The Python bot is tested with a separate test token. The production token is
  never used by the TypeScript and Python pollers at the same time.
- The TypeScript bot remains available until the Python production smoke test
  passes.
