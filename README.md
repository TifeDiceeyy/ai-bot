# Studio AI

Studio AI provides image editing through a browser and a Telegram bot. The
backend and Telegram service are being migrated from TypeScript to Python. The
old TypeScript bot remains in place until the Python bot passes its production
smoke test.

## Python development setup

Python 3.12 or newer is required.

```bash
cd python
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/pytest
.venv/bin/ruff check .
.venv/bin/mypy src
```

Use a separate test bot token while developing:

```bash
BOT_TOKEN=<test-token> .venv/bin/studio-ai-bot
```

Never give the test bot and production bot the same token.

## Production host: Google Cloud

The production bot (`@Tommy007mikBot`) runs long-polling on a Google Cloud
Compute Engine VM, kept alive by PM2. There is no webhook — Telegram is polled
directly from the VM.

|                |                                                                  |
| -------------- | ---------------------------------------------------------------- |
| VM             | `tommy-bot`                                                      |
| Project        | `studio-bot-505917`                                              |
| Zone           | `us-central1-c`                                                  |
| Machine type   | `e2-micro` (Always Free tier)                                    |
| Repo on the VM | `~/ai-bot`                                                       |
| Secrets        | `~/ai-bot/.env`                                                  |
| PM2 process    | `ai-bot`                                                         |
| Logs           | `~/.pm2/logs/ai-bot-out-0.log`, `~/.pm2/logs/ai-bot-error-0.log` |

Connect from a machine with `gcloud` authenticated:

```bash
gcloud compute ssh tommy-bot --zone us-central1-c --project studio-bot-505917
```

The bot blocks new edits before the VM reaches the Always Free tier's 1 GB/month
egress limit (`python/src/studio_ai/telegram/egress_budget.py`).

### Production token rule

**The production `BOT_TOKEN` runs only on the Google Cloud VM. Never anywhere
else.** Do not put the production token in a `.env` on a laptop, desktop, the
old Windows machine, Vercel, or any other server, and do not run the bot with
it outside the VM — not even briefly for a test.

Telegram allows only one poller per token. A second copy anywhere makes the VM
bot exit with code 78, and PM2 deliberately leaves it stopped (see "Duplicate
polling protection"). This is what took the bot offline from 2026-09-21 to
2026-10-11.

For local development, create a separate test bot with @BotFather and use its
token instead (see "Python development setup").

If the production token has ever been copied somewhere else, either delete it
from there or revoke it with @BotFather (`/revoke`), put the new token in
`~/ai-bot/.env` on the VM, and run `pm2 restart ai-bot --update-env`.

## Production Telegram operations

Run these on the Google Cloud VM. PM2 on the VM is the only supported way to
run the Telegram bot in production. Do not run
`npm run bot`, `python -m studio_ai.telegram.bot`, or `studio-ai-bot` manually
while PM2 manages `ai-bot`.

Routine commands:

```bash
pm2 restart ai-bot
pm2 status ai-bot
pm2 logs ai-bot
```

Deployment intentionally replaces the named process with one instance:

```bash
pm2 delete ai-bot
pm2 start ecosystem.python.config.cjs --only ai-bot
pm2 save
pm2 status ai-bot
```

The delete command may report that `ai-bot` does not exist on a first deploy;
that is harmless. Do not run this deployment sequence until the Python bot has
passed with a separate test token and the production cutover is approved.

## Duplicate polling protection

The Python bot uses three safeguards:

1. PM2 is configured for one process in fork mode.
2. An exclusive lock file (the OS temp dir by default, override with
   `BOT_LOCK_PATH`) rejects a second process on the same machine.
3. A Telegram `409 Conflict` exits with code 78. PM2 treats this as an expected
   stop rather than repeatedly restarting and hammering Telegram.

Safeguards 1 and 2 only work on a single machine. Nothing in the code can stop
another machine from polling with the same token, which is why the production
token must stay on the Google Cloud VM only (see "Production token rule").

If a conflict occurs, find the other machine, PM2 application, or manual
process using the same `BOT_TOKEN`. Stop it, then run this on the VM:

```bash
pm2 restart ai-bot
```

## Cutover rule

The TypeScript and Python bots must never poll with the production token at the
same time. Test Python with a separate token, stop TypeScript, start Python with
the production token, perform a smoke test, and only then remove the old
TypeScript Telegram entry point. Git history remains the rollback path.
