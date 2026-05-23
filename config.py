# ─────────────────────────────────────────────
#  config.py  –  Watchlist Bot Configuration
# ─────────────────────────────────────────────
# To add new genre tags, just append to GENRE_TAGS and run /setup again.

GENRE_TAGS = [
    "anime",
    "animation",
    "live-action",
    "movie",
]

STATUS_OPTIONS = ["planned", "watching", "finished"]

STATUS_COLORS = {
    "planned":  0x5865F2,  # blurple
    "watching": 0xFEE75C,  # yellow
    "finished": 0x57F287,  # green
}

STATUS_EMOJI = {
    "planned":  "📋",
    "watching": "▶️",
    "finished": "✅",
}
