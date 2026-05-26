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

STATUS_OPTIONS = ["suggestion", "planned", "on-hold", "dropped", "watching", "finished"]

STATUS_COLORS = {
    "suggestion": 0xEB459E,  # pink
    "planned":    0x5865F2,  # blurple
    "on-hold":    0xF1C53D,  # orange
    "dropped":    0xED4245,  # red
    "watching":   0xFEE75C,  # yellow
    "finished":   0x57F287,  # green
}

STATUS_EMOJI = {
    "suggestion": "💡",
    "planned":  "📋",
    "on-hold":  "⏸️",
    "dropped":  "❌",
    "watching": "▶️",
    "finished": "✅",
}
