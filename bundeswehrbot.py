import discord
from discord.ext import commands
import os
import sqlite3
from datetime import datetime

TOKEN = os.getenv("TOKEN")
DB = "montana.db"

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)


def db():
    return sqlite3.connect(DB)


def setup_db():
    con = db()
    cur = con.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        guild_id INTEGER,
        key TEXT,
        value TEXT,
        PRIMARY KEY (guild_id, key)
    )
    """)
    con.commit()
    con.close()


def kanal(guild, name):
    return discord.utils.get(guild.text_channels, name=name)


def rolle(guild, name):
    return discord.utils.get(guild.roles, name=name)


async def log(guild, name, text):
    ch = kanal(guild, name)
    if ch:
        await ch.send(text)


@bot.event
async def on_ready():
    setup_db()
    print(f"{bot.user} Montana Hauptbot online!")

    try:
        synced = await bot.tree.sync()
        print(f"{len(synced)} Commands geladen.")
    except Exception as e:
        print(f"SYNC FEHLER: {e}")


@bot.event
async def on_member_join(member):
    ch = kanal(member.guild, "willkommen")
    r = rolle(member.guild, "Anwärter")

    if r:
        await member.add_roles(r)

    if ch:
        embed = discord.Embed(
            title="🤠 Willkommen bei der Montana Gang",
            description=(
                f"Willkommen {member.mention}!\n\n"
                "Lies dir bitte die Regeln durch und hab viel Spaß."
            ),
            color=0x8B4513
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        await ch.send(embed=embed)

    await log(member.guild, "member-logs", f"✅ {member.mention} ist dem Server beigetreten.")


@bot.event
async def on_member_remove(member):
    await log(member.guild, "member-logs", f"❌ {member} hat den Server verlassen.")


@bot.tree.command(name="setup", description="Erstellt Montana Gang System")
async def setup(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ Keine Rechte.", ephemeral=True)

    await interaction.response.defer(ephemeral=True)

    channels = [
        "willkommen",
        "ankuendigungen",
        "regeln",
        "bot-info",
        "gang-chat",
        "montana-funk",
        "boss-buero",
        "waffenkammer",
        "einsaetze",
        "bewerbungen",
        "bewerbungs-check",
        "annahmen",
        "ablehnungen",
        "bot-commands",
        "member-logs",
        "moderation-logs",
        "rollen-logs",
        "system-logs"
    ]

    roles = [
        "Boss",
        "Co-Boss",
        "Underboss",
        "Manager",
        "OG Member",
        "Member",
        "Anwärter",
        "Büro Schlüssel",
        "Waffenkammer Schlüssel",
        "Boss Zugang"
    ]

    for name in channels:
        if not kanal(interaction.guild, name):
            await interaction.guild.create_text_channel(name)

    for name in roles:
        if not rolle(interaction.guild, name):
            await interaction.guild.create_role(name=name)

    await log(interaction.guild, "system-logs", f"⚙️ Setup wurde von {interaction.user.mention} ausgeführt.")

    await interaction.followup.send("✅ Montana Gang Setup abgeschlossen.", ephemeral=True)


@bot.tree.command(name="setup_permissions", description="Setzt Büro/Waffenkammer Rechte")
async def setup_permissions(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ Keine Rechte.", ephemeral=True)

    await interaction.response.defer(ephemeral=True)

    buero = kanal(interaction.guild, "boss-buero")
    waffen = kanal(interaction.guild, "waffenkammer")

    buero_key = rolle(interaction.guild, "Büro Schlüssel")
    waffen_key = rolle(interaction.guild, "Waffenkammer Schlüssel")

    everyone = interaction.guild.default_role

    if buero and buero_key:
        await buero.set_permissions(everyone, view_channel=False)
        await buero.set_permissions(
            buero_key,
            view_channel=True,
            send_messages=True,
            read_message_history=True
        )

    if waffen and waffen_key:
        await waffen.set_permissions(everyone, view_channel=False)
        await waffen.set_permissions(
            waffen_key,
            view_channel=True,
            send_messages=True,
            read_message_history=True
        )

    await log(interaction.guild, "system-logs", "🔐 Rechte wurden eingerichtet.")
    await interaction.followup.send("✅ Rechte gesetzt.", ephemeral=True)


@bot.tree.command(name="rolle_erstellen", description="Erstellt eine Rolle")
async def rolle_erstellen(interaction: discord.Interaction, name: str):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ Keine Rechte.", ephemeral=True)

    if rolle(interaction.guild, name):
        return await interaction.response.send_message("⚠️ Rolle existiert bereits.", ephemeral=True)

    r = await interaction.guild.create_role(name=name)
    await log(interaction.guild, "rollen-logs", f"🎭 Rolle erstellt: **{r.name}** von {interaction.user.mention}")
    await interaction.response.send_message(f"✅ Rolle `{name}` erstellt.", ephemeral=True)


@bot.tree.command(name="schluessel_geben", description="Gibt einem User eine Schlüsselrolle")
async def schluessel_geben(interaction: discord.Interaction, user: discord.Member, schluessel: str):
    if not interaction.user.guild_permissions.manage_roles:
        return await interaction.response.send_message("❌ Keine Rechte.", ephemeral=True)

    r = rolle(interaction.guild, schluessel)

    if not r:
        return await interaction.response.send_message("❌ Rolle nicht gefunden.", ephemeral=True)

    await user.add_roles(r)

    await log(
        interaction.guild,
        "rollen-logs",
        f"🔑 {user.mention} hat **{schluessel}** erhalten von {interaction.user.mention}"
    )

    await interaction.response.send_message(f"✅ {user.mention} hat `{schluessel}` erhalten.", ephemeral=True)


@bot.tree.command(name="schluessel_entfernen", description="Entfernt eine Schlüsselrolle")
async def schluessel_entfernen(interaction: discord.Interaction, user: discord.Member, schluessel: str):
    if not interaction.user.guild_permissions.manage_roles:
        return await interaction.response.send_message("❌ Keine Rechte.", ephemeral=True)

    r = rolle(interaction.guild, schluessel)

    if not r:
        return await interaction.response.send_message("❌ Rolle nicht gefunden.", ephemeral=True)

    await user.remove_roles(r)

    await log(
        interaction.guild,
        "rollen-logs",
        f"🔒 {user.mention} hat **{schluessel}** verloren. Entfernt von {interaction.user.mention}"
    )

    await interaction.response.send_message(f"✅ `{schluessel}` entfernt.", ephemeral=True)


@bot.tree.command(name="uprank", description="Sendet Uprank Nachricht")
async def uprank(
    interaction: discord.Interaction,
    channel: discord.TextChannel,
    user: discord.Member,
    von: str,
    auf: str,
    grund: str
):
    if not interaction.user.guild_permissions.manage_roles:
        return await interaction.response.send_message("❌ Keine Rechte.", ephemeral=True)

    embed = discord.Embed(
        title="🚨 | Montana Gang Uprank",
        color=0x8B4513
    )

    embed.add_field(name="Wer:", value=user.mention, inline=False)
    embed.add_field(name="Von:", value=von, inline=True)
    embed.add_field(name="Auf:", value=auf, inline=True)
    embed.add_field(name="Grund:", value=grund, inline=False)
    embed.set_footer(text="Montana Gang Rangsystem")
    embed.timestamp = datetime.now()

    await channel.send(embed=embed)
    await log(interaction.guild, "rollen-logs", f"⬆️ Uprank: {user.mention} von {von} auf {auf}")

    await interaction.response.send_message("✅ Uprank gesendet.", ephemeral=True)


@bot.tree.command(name="schreiben", description="Bot schreibt eine Nachricht")
async def schreiben(interaction: discord.Interaction, channel: discord.TextChannel, text: str):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ Keine Rechte.", ephemeral=True)

    await channel.send(text)
    await log(interaction.guild, "system-logs", f"✍️ Nachricht gesendet von {interaction.user.mention} in {channel.mention}")
    await interaction.response.send_message("✅ Nachricht gesendet.", ephemeral=True)


@bot.tree.command(name="status", description="Zeigt Bot Status")
async def status(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🤠 Montana Hauptbot Status",
        color=0x8B4513
    )

    embed.add_field(name="Setup", value="✅ Aktiv")
    embed.add_field(name="Rollen", value="✅ Aktiv")
    embed.add_field(name="Rechte", value="✅ Aktiv")
    embed.add_field(name="Logs", value="✅ Aktiv")
    embed.add_field(name="Willkommen", value="✅ Aktiv")

    await interaction.response.send_message(embed=embed, ephemeral=True)
import discord
from discord.ext import commands
import asyncio

TOKEN = "DEIN_TOKEN"

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot online: {bot.user}")


@bot.command()
@commands.has_permissions(administrator=True)
async def notfall(ctx):

    embed = discord.Embed(
        title="🚨 NOTFALLMODUS EINGELEITET 🚨",
        description="""
⚠️ Kritischer Vorfall erkannt

🔒 Systeme werden gesichert
📁 Logs werden gespeichert
🛑 Bot wird heruntergefahren

Status: KRITISCH
        """,
        color=discord.Color.red()
    )

    await ctx.send("@everyone", embed=embed)

    for i in range(10, 0, -1):
        await ctx.send(f"⏳ Shutdown in {i} Sekunden...")
        await asyncio.sleep(1)

    await ctx.send("🛑 Notfallmodus abgeschlossen.")
    await bot.close()


bot.run(TOKEN)

bot.run(TOKEN)
