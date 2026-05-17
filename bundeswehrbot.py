import discord
from discord.ext import commands
import os

TOKEN = os.getenv("TOKEN") or "MTUwNTYzNDE0NjE5Njc4MzIxNA.GIJy5W.UudCgbreD7KwInTy2I0_clhu9J9MO9rkTXMv_Q"
GUILD_ID = 1504190915235811360
BOT_ZENTRALE = "bot-zentrale"

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

def kanal(guild, name):
    return discord.utils.get(guild.text_channels, name=name)

@bot.event
async def on_ready():
    print(f"{bot.user} Hauptbot online!")
    guild = discord.Object(id=GUILD_ID)
    bot.tree.copy_global_to(guild=guild)
    synced = await bot.tree.sync(guild=guild)
    print(f"{len(synced)} Commands geladen.")

@bot.tree.command(name="ki_scan", description="Scannt Server und sendet Aufgaben an KI-Bot")
async def ki_scan(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ Keine Rechte.", ephemeral=True)

    await interaction.response.defer(ephemeral=True)

    zentrale = kanal(interaction.guild, BOT_ZENTRALE)
    if not zentrale:
        zentrale = await interaction.guild.create_text_channel(BOT_ZENTRALE)

    wichtige_channels = [
        "einsaetze",
        "waffenlogs",
        "bundeswehr-funk",
        "dienstmeldungen",
        "personalakten",
        "beförderungen",
        "ausbildung",
        "logs",
        "bot-commands"
    ]

    vorhandene = [c.name for c in interaction.guild.text_channels]
    aufgaben = 0

    for ch in wichtige_channels:
        if ch not in vorhandene:
            await zentrale.send(f"AUFGABE:create_channel:{ch}")
            aufgaben += 1

    await interaction.followup.send(
        f"🧠 KI-Scan fertig. {aufgaben} Aufgaben gesendet.",
        ephemeral=True
    )

@bot.tree.command(name="alarm", description="Sendet Alarm an KI-Bot")
async def alarm(
    interaction: discord.Interaction,
    stufe: str,
    ort: str,
    bedrohung: str,
    ausruestung: str
):
    await interaction.response.defer(ephemeral=True)

    zentrale = kanal(interaction.guild, BOT_ZENTRALE)
    if not zentrale:
        zentrale = await interaction.guild.create_text_channel(BOT_ZENTRALE)

    await zentrale.send(
        f"ALARM:{stufe}|{ort}|{bedrohung}|{ausruestung}|{interaction.user.mention}"
    )

    await interaction.followup.send("🚨 Alarm an KI-Bot gesendet.", ephemeral=True)

@bot.tree.command(name="ki_status", description="Fragt KI-Bot Status")
async def ki_status(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    zentrale = kanal(interaction.guild, BOT_ZENTRALE)
    if not zentrale:
        zentrale = await interaction.guild.create_text_channel(BOT_ZENTRALE)

    await zentrale.send("AUFGABE:status")
    await interaction.followup.send("✅ Status-Anfrage gesendet.", ephemeral=True)

@bot.tree.command(name="hilfe", description="Zeigt Befehle")
async def hilfe(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🧠 Bundeswehr Hauptbot",
        description="/ki_scan\n/alarm\n/ki_status",
        color=0x2E8B57
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

bot.run(TOKEN)
