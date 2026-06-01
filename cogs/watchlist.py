# ─────────────────────────────────────────────
#  cogs/watchlist.py  –  All watchlist commands
# ─────────────────────────────────────────────

import random

import discord
from discord import app_commands
from discord.ext import commands

import database as db
from config import GENRE_TAGS, STATUS_COLORS, STATUS_EMOJI, STATUS_OPTIONS
from database import tags_str_to_list


def _tag_display(tags: list[str]) -> str:
    return " ".join(f"`{t}`" for t in tags) if tags else "*none*"


# ── confirmation buttons ──────────────────────

class ConfirmView(discord.ui.View):
    def __init__(self, author: discord.User):
        super().__init__(timeout=30)
        self.author = author
        self.confirmed = False

    async def _check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("This isn't for you!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Yes, remove it", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not await self._check(interaction):
            return
        self.confirmed = True
        await interaction.response.defer()
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not await self._check(interaction):
            return
        await interaction.response.defer()
        self.stop()


# ── the cog ──────────────────────────────────

class Watchlist(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def _build_embed(self, title: str, status: str, tags: list[str], added_by_name: str, notes: str = "") -> discord.Embed:
        embed = discord.Embed(title=title, color=STATUS_COLORS[status])
        embed.add_field(name="Status",   value=f"{STATUS_EMOJI[status]} {status.capitalize()}", inline=True)
        embed.add_field(name="Tags",     value=_tag_display(tags),                               inline=True)
        embed.add_field(name="Added by", value=added_by_name,                                    inline=True)
        if notes:
            embed.add_field(name="📝 Note", value=notes, inline=False)
        return embed

    async def _title_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        titles = await db.get_all_titles(interaction.guild_id)
        return [
            app_commands.Choice(name=t, value=t)
            for t in titles if current.lower() in t.lower()
        ][:25]
    
    async def _tag_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
    # Split what's typed so far — everything before the last comma is already chosen
        parts = current.split(",")
        already_chosen = [p.strip().lower() for p in parts[:-1]]
        current_tag = parts[-1].strip().lower()

        # Suggest tags that match what's being typed and aren't already in the list
        suggestions = [
            t for t in GENRE_TAGS
            if t not in already_chosen and current_tag in t
        ]

        # Build choices that include the already-typed tags as a prefix
        prefix = ", ".join(already_chosen)
        return [
            app_commands.Choice(
                name=f"{prefix}, {t}".lstrip(", ") if prefix else t,
                value=f"{prefix}, {t}".lstrip(", ") if prefix else t,
            )
            for t in suggestions
        ][:25]

    # ── /add ─────────────────────────────────

    @app_commands.command(name="add", description="Add a show to the watchlist")
    @app_commands.describe(
        title="Name of the show",
        tags="Genre tags separated by commas (e.g. anime,live-action)",
        status="Starting status — defaults to planned",
    )
    @app_commands.choices(status=[
        
        app_commands.Choice(name="Suggestion", value="suggestion"),
        app_commands.Choice(name="Planned",  value="planned"),
        app_commands.Choice(name="On-Hold",  value="on-hold"),
        app_commands.Choice(name="Dropped",  value="dropped"),
        app_commands.Choice(name="Watching", value="watching"),
        app_commands.Choice(name="Finished", value="finished"),
    ])
    @app_commands.autocomplete(tags=_tag_autocomplete)
    async def add(self, interaction: discord.Interaction, title: str, tags: str, status: str = "planned"):
        await interaction.response.defer()

        if await db.get_show_by_title(interaction.guild_id, title):
            await interaction.followup.send(f"⚠️ **{title}** is already in the watchlist.")
            return

        parsed_tags = [t.strip().lower() for t in tags.split(",") if t.strip()] if tags else []
        bad = [t for t in parsed_tags if t not in GENRE_TAGS]
        if bad:
            valid = " ".join(f"`{t}`" for t in GENRE_TAGS)
            await interaction.followup.send(f"⚠️ Unknown tag(s): {_tag_display(bad)}\nAvailable tags: {valid}")
            return

        await db.add_show(
            guild_id=interaction.guild_id,
            title=title,
            status=status,
            tags=parsed_tags,
            added_by_id=interaction.user.id
        )

        await interaction.followup.send(
            f"{STATUS_EMOJI[status]} Added **{title}** to the watchlist!\n"
            f"**Status:** {status} · **Tags:** {_tag_display(parsed_tags)}"
        )

    # ── /suggest ─────────────────────────────────

    @app_commands.command(name="suggest", description="Quickly suggest a show")
    @app_commands.describe(
        title="Name of the show",
        tags="Genre tags separated by commas (e.g. anime,live-action)",
    )
    @app_commands.autocomplete(tags=_tag_autocomplete)
    async def suggest(self, interaction: discord.Interaction, title: str, tags: str):
        await interaction.response.defer()

        if await db.get_show_by_title(interaction.guild_id, title):
            await interaction.followup.send(f"⚠️ **{title}** is already in the watchlist.")
            return

        parsed_tags = [t.strip().lower() for t in tags.split(",") if t.strip()]
        bad = [t for t in parsed_tags if t not in GENRE_TAGS]
        if bad:
            valid = " ".join(f"`{t}`" for t in GENRE_TAGS)
            await interaction.followup.send(f"⚠️ Unknown tag(s): {_tag_display(bad)}\nAvailable tags: {valid}")
            return

        await db.add_show(
            guild_id=interaction.guild_id,
            title=title,
            status="suggestion",
            tags=parsed_tags,
            added_by_id=interaction.user.id,
        )

        await interaction.followup.send(
            f"💡 Suggested **{title}**! · **Tags:** {_tag_display(parsed_tags)}"
        )

    # ── /status ──────────────────────────────

    @app_commands.command(name="status", description="Update the watch status of a show")
    @app_commands.describe(title="Name of the show", new_status="New status")
    @app_commands.choices(new_status=[
        
        app_commands.Choice(name="Suggestion", value="suggestion"),
        app_commands.Choice(name="Planned",  value="planned"),
        app_commands.Choice(name="On-Hold",  value="on-hold"),
        app_commands.Choice(name="Dropped",  value="dropped"),
        app_commands.Choice(name="Watching", value="watching"),
        app_commands.Choice(name="Finished", value="finished"),
    ])
    @app_commands.autocomplete(title=_title_autocomplete)
    async def update_status(self, interaction: discord.Interaction, title: str, new_status: str):
        await interaction.response.defer()

        show = await db.get_show_by_title(interaction.guild_id, title)
        if not show:
            await interaction.followup.send(f"❌ Could not find **{title}** in the watchlist.")
            return

        if show["status"] == new_status:
            await interaction.followup.send(f"ℹ️ **{title}** is already marked as **{new_status}**.")
            return

        old = show["status"]
        await db.update_show_status(interaction.guild_id, show["id"], new_status)
        await interaction.followup.send(
            f"{STATUS_EMOJI[new_status]} Updated **{title}**: {STATUS_EMOJI[old]} {old} → {STATUS_EMOJI[new_status]} **{new_status}**"
        )

    # ── /tag ─────────────────────────────────

    @app_commands.command(name="tag", description="Update the tags on a show")
    @app_commands.describe(title="Name of the show", tags="New tags, comma-separated (replaces existing tags)")
    @app_commands.autocomplete(title=_title_autocomplete)
    @app_commands.autocomplete(tags=_tag_autocomplete)
    async def update_tags(self, interaction: discord.Interaction, title: str, tags: str):
        await interaction.response.defer()

        show = await db.get_show_by_title(interaction.guild_id, title)
        if not show:
            await interaction.followup.send(f"❌ Could not find **{title}** in the watchlist.")
            return

        parsed_tags = [t.strip().lower() for t in tags.split(",") if t.strip()]
        bad = [t for t in parsed_tags if t not in GENRE_TAGS]
        if bad:
            valid = " ".join(f"`{t}`" for t in GENRE_TAGS)
            await interaction.followup.send(f"⚠️ Unknown tag(s): {_tag_display(bad)}\nAvailable tags: {valid}")
            return

        await db.update_show_tags(interaction.guild_id, show["id"], parsed_tags)
        await interaction.followup.send(f"🏷️ Updated tags for **{title}**: {_tag_display(parsed_tags)}")

    # ── /list ────────────────────────────────

    @app_commands.command(name="list", description="Browse the watchlist")
    @app_commands.describe(
        status="Filter by status (leave empty for all)",
        tag="Filter by tag (leave empty for all)",
    )
    @app_commands.choices(status=[
        
        app_commands.Choice(name="Suggestion", value="suggestion"),
        app_commands.Choice(name="Planned",  value="planned"),
        app_commands.Choice(name="On-Hold",  value="on-hold"),
        app_commands.Choice(name="Dropped",  value="dropped"),
        app_commands.Choice(name="Watching", value="watching"),
        app_commands.Choice(name="Finished", value="finished"),
    ])
    async def list_shows(self, interaction: discord.Interaction, status: str = None, tag: str = None):
        await interaction.response.defer()

        shows = await db.get_shows(interaction.guild_id, status=status, tag=tag)
        if not shows:
            qualifier = ""
            if status: qualifier += f" with status **{status}**"
            if tag:    qualifier += f" tagged **{tag}**"
            await interaction.followup.send(f"No shows found{qualifier}.")
            return

        grouped: dict[str, list] = {s: [] for s in STATUS_OPTIONS}
        for show in shows:
            grouped[show["status"]].append(show)

        embed = discord.Embed(title="📺 Watchlist", color=0x5865F2)

        for s in ([status] if status else STATUS_OPTIONS):
            bucket = grouped.get(s, [])
            if not bucket:
                continue
            lines = []
            for show in bucket:
                t_list = tags_str_to_list(show["tags"])
                tag_part = f" {_tag_display(t_list)}" if t_list else ""
                lines.append(f"- **{show['title']}**{tag_part}")
            embed.add_field(
                name=f"{STATUS_EMOJI[s]} {s.capitalize()} ({len(bucket)})",
                value="\n".join(lines),
                inline=False,
            )

        embed.set_footer(text=f"{len(shows)} show(s) total")
        await interaction.followup.send(embed=embed)


    # ── /rename ────────────────────────────────
    @app_commands.command(name="rename", description="Rename a show in the watchlist")
    @app_commands.describe(title="Current name of the show", new_title="New name")
    @app_commands.autocomplete(title=_title_autocomplete)
    async def rename(self, interaction: discord.Interaction, title: str, new_title: str):
        await interaction.response.defer()

        show = await db.get_show_by_title(interaction.guild_id, title)
        if not show:
            await interaction.followup.send(f"❌ Could not find **{title}** in the watchlist.")
            return

        if await db.get_show_by_title(interaction.guild_id, new_title):
            await interaction.followup.send(f"⚠️ **{new_title}** already exists in the watchlist.")
            return

        await db.update_show_title(interaction.guild_id, show["id"], new_title)
        await interaction.followup.send(f"✏️ Renamed **{title}** to **{new_title}**.")

    # ── /pick ────────────────────────────────

    @app_commands.command(name="pick", description="Let the bot pick a random show for you")
    @app_commands.describe(
        from_status="Pick from planned (new) or watching (continue). Defaults to planned.",
        tag="Only pick from shows with this specific tag",
    )
    @app_commands.choices(from_status=[
        app_commands.Choice(name="Planned",  value="planned"),
        app_commands.Choice(name="Watching", value="watching"),
        app_commands.Choice(name="Suggestion", value="suggestion"),
    ])
    async def pick(self, interaction: discord.Interaction, from_status: str = "planned", tag: str = None):
        await interaction.response.defer()

        pool = await db.get_shows(interaction.guild_id, status=from_status, tag=tag)
        if not pool:
            qualifier = f" tagged **{tag}**" if tag else ""
            await interaction.followup.send(f"No {from_status} shows{qualifier} to pick from!")
            return

        chosen = random.choice(pool)
        t_list = tags_str_to_list(chosen["tags"])

        embed = discord.Embed(
            title="🎲 The bot has spoken...",
            description=f"## {chosen['title']}",
            color=STATUS_COLORS[from_status],
        )
        embed.add_field(name="Tags",     value=_tag_display(t_list),    inline=True)
        user = interaction.guild.get_member(chosen["added_by_id"])
        added_by = user.display_name if user else "Unknown"
        embed.add_field(name="Added by", value=added_by, inline=True)
        embed.set_footer(text=f"Randomly chosen from {len(pool)} {from_status} show(s)")
        await interaction.followup.send(embed=embed)

    # ── /info ────────────────────────────────

    @app_commands.command(name="info", description="Show details about a specific show")
    @app_commands.autocomplete(title=_title_autocomplete)
    async def info(self, interaction: discord.Interaction, title: str):
        await interaction.response.defer()

        show = await db.get_show_by_title(interaction.guild_id, title)
        if not show:
            await interaction.followup.send(f"❌ Could not find **{title}** in the watchlist.")
            return

        t_list = tags_str_to_list(show["tags"])
        user = interaction.guild.get_member(show["added_by_id"])
        added_by = user.display_name if user else "Unknown"
        embed = self._build_embed(show["title"], show["status"], t_list, added_by, notes=show["notes"])
        embed.set_footer(text=f"Added on {show['added_at'][:10]}")
        await interaction.followup.send(embed=embed)

    # ── /remove ──────────────────────────────

    @app_commands.command(name="remove", description="Remove a show from the watchlist")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.autocomplete(title=_title_autocomplete)
    async def remove(self, interaction: discord.Interaction, title: str):
        show = await db.get_show_by_title(interaction.guild_id, title)
        if not show:
            await interaction.response.send_message(f"❌ Could not find **{title}** in the watchlist.")
            return

        view = ConfirmView(interaction.user)
        await interaction.response.send_message(
            f"⚠️ Are you sure you want to remove **{title}** from the watchlist?",
            view=view,
            ephemeral=True,
        )
        await view.wait()

        if view.confirmed:
            await db.delete_show(interaction.guild_id, show["id"])
            await interaction.edit_original_response(content=f"🗑️ Removed **{title}**.", view=None)
        else:
            await interaction.edit_original_response(content="Cancelled.", view=None)

    # ── /tags ────────────────────────────────

    @app_commands.command(name="tags", description="List all available genre tags")
    async def list_tags(self, interaction: discord.Interaction):
        embed = discord.Embed(title="🏷️ Available Tags", color=0x5865F2)
        embed.description = "\n".join(f"• `{t}`" for t in GENRE_TAGS)
        embed.set_footer(text="To add more tags, edit GENRE_TAGS in config.py and restart the bot.")
        await interaction.response.send_message(embed=embed)

    # ── /Clearlist ────────────────────────────────

    @app_commands.command(name="clearlist", description="Remove all shows from the watchlist")
    @app_commands.checks.has_permissions(administrator=True)
    async def clearlist(self, interaction: discord.Interaction):
        view = ConfirmView(interaction.user)
        await interaction.response.send_message(
            "⚠️ Are you sure you want to **clear the entire watchlist**? This cannot be undone.",
            view=view,
            ephemeral=True,
        )
        await view.wait()

        if view.confirmed:
            await db.clear_all_shows(interaction.guild_id)
            await interaction.edit_original_response(content="🗑️ Watchlist cleared.", view=None)
        else:
            await interaction.edit_original_response(content="Cancelled.", view=None)

    # ── /note ────────────────────────────────

    @app_commands.command(name="note", description="Add or update a note on a show")
    @app_commands.describe(title="Name of the show", note="Your note (leave empty to clear it)")
    @app_commands.autocomplete(title=_title_autocomplete)
    async def note(self, interaction: discord.Interaction, title: str, note: str = ""):
        await interaction.response.defer()

        show = await db.get_show_by_title(interaction.guild_id, title)
        if not show:
            await interaction.followup.send(f"❌ Could not find **{title}** in the watchlist.")
            return

        await db.update_note(interaction.guild_id, show["id"], note)

        if note:
            await interaction.followup.send(f"📝 Added note to **{title}**: *{note}*")
        else:
            await interaction.followup.send(f"🗑️ Cleared note on **{title}**.")

    # ── /help ────────────────────────────────

    @app_commands.command(name="help", description="Show all watchlist commands")
    async def help(self, interaction: discord.Interaction):
        embed = discord.Embed(title="📺 Commands", color=0x5865F2)
        embed.add_field(name="`/add <title> <tags> [status]`",
            value="Add a show.\nExample: `/add Pokemon tags:animation`", inline=False)
        embed.add_field(name="`/suggest <title> <tags>`",
            value="Suggest a show.\nExample: `/suggest Pokemon tags:animation`", inline=False)
        embed.add_field(name="`/status <title> <new_status>`",
            value="Update a show's status: `planned` → `watching` → `finished`", inline=False)
        embed.add_field(name="`/tag <title> <tags>`",
            value="Replace the genre tags on a show.", inline=False)
        embed.add_field(name="`/rename <title> <new_title>`",
            value="Rename a show in the watchlist.", inline=False)
        embed.add_field(name="`/note <title> [note]`",
            value="Add or update a note on a show.", inline=False)
        embed.add_field(name="`/pick [from_status] [tag]`",
            value="Pick a random show. Defaults to `planned`.", inline=False)
        embed.add_field(name="`/list [status] [tag]`",
            value="Browse the full list, optionally filtered.", inline=False)
        embed.add_field(name="`/info <title>`", value="See full details about one show.", inline=False)
        embed.add_field(name="`/tags`",           value="List all available tags.", inline=False)
        embed.add_field(name="`/remove <title>`", value="Remove a show (administrator only).", inline=False)
        embed.add_field(name="`/clearlist`",      value="Clear the entire watchlist (administrator only).", inline=False)
        embed.set_footer(text="Title fields have autocomplete — just start typing!")
        await interaction.response.send_message(embed=embed)

    # ── error handling ────────────────────────

    @add.error
    @remove.error
    @clearlist.error
    @update_status.error
    async def on_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("❌ You don't have permission to do that.", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ Something went wrong: {error}", ephemeral=True)
            raise error
        
@app_commands.command(name="export", description="Export the watchlist to a JSON file")
@app_commands.checks.has_permissions(administrator=True)
async def export(self, interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    data = await db.export_shows(interaction.guild_id)
    file = discord.File(
        fp=__import__("io").BytesIO(data.encode()),
        filename="watchlist_export.json"
    )
    await interaction.followup.send("📦 Here's your watchlist export:", file=file, ephemeral=True)

@app_commands.command(name="import", description="Import a watchlist from a JSON file")
@app_commands.checks.has_permissions(administrator=True)
async def import_shows(self, interaction: discord.Interaction, file: discord.Attachment):
    await interaction.response.defer(ephemeral=True)

    if not file.filename.endswith(".json"):
        await interaction.followup.send("❌ Please upload a `.json` file.", ephemeral=True)
        return

    try:
        data = await file.read()
        count = await db.import_shows(data.decode())
        await interaction.followup.send(f"✅ Imported {count} show(s) successfully.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Import failed: {e}", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Watchlist(bot))
