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

## Windows setup (production)

The bot runs long-polling on a Windows machine, kept alive by PM2 as long as
that machine is on. There is no server deployment or webhook — Telegram is
polled directly from this machine.

```powershell
git clone https://github.com/TifeDiceeyy/ai-bot.git
cd ai-bot
copy .env.example .env
REM fill in FAL_KEY, BOT_TOKEN, ALLOWED_TELEGRAM_USER_ID in .env

cd python
python -m venv .venv
.venv\Scripts\pip install -e ".[dev]"
.venv\Scripts\pytest
cd ..
```

Install PM2 and the Windows helper that starts PM2's saved process list on
boot/logon (run once):

```powershell
npm install -g pm2
npm install -g pm2-windows-startup
pm2-startup install
```

Start the bot under PM2 and persist it across reboots:

```powershell
pm2 start ecosystem.python.config.cjs --only ai-bot
pm2 save
```

After this, PM2 restarts the bot on crash (`autorestart`) and relaunches it
automatically whenever the machine boots or you log back in, for as long as
the machine stays on. See "Duplicate polling protection" below for what
prevents two copies of the bot polling the same token at once.

## Production Telegram operations

PM2 is the only supported way to run the Telegram bot in production. Do not run
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

If a conflict occurs, find the other machine, PM2 application, or manual
process using the same `BOT_TOKEN`. Stop it, then run:

```bash
pm2 restart ai-bot
```

## Cutover rule

The TypeScript and Python bots must never poll with the production token at the
same time. Test Python with a separate token, stop TypeScript, start Python with
the production token, perform a smoke test, and only then remove the old
TypeScript Telegram entry point. Git history remains the rollback path.
