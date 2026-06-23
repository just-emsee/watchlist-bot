# ─────────────────────────────────────────────
#  bot.py  –  Entry point
# ─────────────────────────────────────────────
# Run with:  python bot.py

import os
import asyncio

import discord
from discord import guild
from discord.ext import commands
from dotenv import load_dotenv

import database as db

load_dotenv()  # reads values from .env into os.environ

# Discord needs certain "intents" enabled to receive specific events.
# default() covers everything we need (guild messages, reactions, etc.)
intents = discord.Intents.default()
intents.members = True 

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    # This fires once the bot is fully connected — safe to sync here
    print(f"✅  Logged in as {bot.user} (ID: {bot.user.id})")
    print(f"    Connected to {len(bot.guilds)} server(s)")

    # Sync slash commands to a specific guild (server) for faster updates during development.
    try :
       guild_id = id=os.getenv("DEV_GUILD_ID")
       guild = discord.Object(guild_id)
       bot.tree.copy_global_to(guild=guild)
       await bot.tree.sync(guild=guild)
       print(f"    Synced to dev guild. (ID: {guild_id})")
    except Exception : pass
        
    
    

    synced = await bot.tree.sync()
    print(f"    Synced {len(synced)} slash command(s)")


async def main():
    async with bot:
        # 1. Set up the database tables
        await db.init_db()

        # 2. Load the watchlist cog (all the /commands live there)
        await bot.load_extension("cogs.watchlist")

        # 3. Start the bot (on_ready will handle the sync once connected)
        token = os.getenv("DISCORD_TOKEN")
        if not token:
            raise ValueError("DISCORD_TOKEN is not set in your .env file!")
        await bot.start(token)


if __name__ == "__main__":
    asyncio.run(main())
