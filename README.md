# 📺 Watchlist Bot

A Discord bot that manages your group's show watchlist using a Forum channel.  
Add shows, track status, filter by tag, and let the bot pick what to watch next.

---

## Setup

### 1 — Create the bot on Discord

1. Go to <https://discord.com/developers/applications> and click **New Application**.
2. Name it (e.g. "Watchlist Bot"), then go to the **Bot** tab.
3. Click **Reset Token**, copy it — this is your `DISCORD_TOKEN`.
4. Under **Privileged Gateway Intents**, you don't need to enable anything extra.
5. Go to **OAuth2 → URL Generator**:
   - Scopes: `bot`, `applications.commands`
   - Bot Permissions: `Send Messages`, `Read Message History`, `Manage Threads`, `View Channels`
6. Copy the generated URL, open it, and invite the bot to your server.

### 2 — Set up your .env

```
cp .env.example .env
```

Edit `.env` and fill in:
- `DISCORD_TOKEN` — from step 1 above
- `FORUM_CHANNEL_ID` — right-click your forum channel in Discord, click **Copy Channel ID**  
  *(You need Developer Mode on: Settings → Advanced → Developer Mode)*

### 3 — Install and run

```bash
# Create a virtual environment (good Python practice)
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the bot
python bot.py
```

### 4 — Initialize the forum tags

In your Discord server, run `/setup` (you need Manage Channels permission).  
This creates all the status and genre tags on your forum channel.

---

## Adding or changing tags

Open `config.py` and add your tag to `GENRE_TAGS`:

```python
GENRE_TAGS = [
    "anime",
    "live-action",
    "my-new-tag",   # ← just add it here
    ...
]
```

Then run `/setup` again — it only creates tags that don't exist yet, so it's safe to re-run.

---

## Tips

**Instant slash command sync (for testing):**  
By default Discord takes up to an hour to propagate slash commands globally.  
To sync instantly to one server during development, add this to `bot.py` after `bot.tree.sync()`:

```python
# Replace 123456789 with your server (guild) ID
guild = discord.Object(id=123456789)
await bot.tree.sync(guild=guild)
```

**Keeping the bot running 24/7:**  
Use a process manager like `pm2` or `screen`, or host it on Railway / Fly.io / a cheap VPS.

**The database** is a single file `watchlist.db` created automatically in the same folder.  
Back it up occasionally if you care about the data.

---

## File overview

```
watchlist-bot/
├── bot.py          — entry point, starts the bot
├── database.py     — all SQLite read/write functions
├── config.py       — tags, colors, emoji (edit this to customize)
├── cogs/
│   └── watchlist.py — all the slash commands
├── .env            — your secrets (don't commit this!)
├── .env.example    — template for .env
└── requirements.txt
```
