import os
import asyncio
import discord
from discord.ext import commands
from discord import app_commands

TOKEN = os.getenv("TOKEN")
OWNER_ID = 1407548826247761961  # Hier deine Discord-ID eintragen

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

class BundeswehrBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        print("✅ Slash Commands synchronisiert")

bot = BundeswehrBot()

@bot.event
async def on_ready():
    print(f"🟢 Online als {bot.user}")

# ======================
# Utility
# ======================

@bot.tree.command(name="ping", description="Zeigt die Latenz an")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"🏓 Pong! {round(bot.latency * 1000)} ms"
    )

@bot.tree.command(name="hilfe", description="Zeigt alle Befehle")
async def hilfe(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📚 Bundeswehr Hauptbot Hilfe",
        color=discord.Color.blue()
    )
    embed.add_field(
        name="🎖️ RP",
        value="/dienstbeginn\n/dienstende\n/meldung\n/einsatz",
        inline=False
    )
    embed.add_field(
        name="👮 Moderation",
        value="/kick\n/ban",
        inline=False
    )
    embed.add_field(
        name="🛡️ Sicherheit",
        value="/notfall",
        inline=False
    )

    await interaction.response.send_message(embed=embed)

# ======================
# Bundeswehr RP
# ======================

@bot.tree.command(name="dienstbeginn", description="Dienstbeginn melden")
async def dienstbeginn(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"🎖️ {interaction.user.mention} hat den Dienst begonnen."
    )

@bot.tree.command(name="dienstende", description="Dienstende melden")
async def dienstende(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"🏠 {interaction.user.mention} hat den Dienst beendet."
    )

@bot.tree.command(name="meldung", description="Meldung abgeben")
@app_commands.describe(text="Deine Meldung")
async def meldung(interaction: discord.Interaction, text: str):
    await interaction.response.send_message(
        f"📢 Meldung von {interaction.user.mention}:\n{text}"
    )

@bot.tree.command(name="einsatz", description="Einsatz ausrufen")
@app_commands.describe(name="Name des Einsatzes")
async def einsatz(interaction: discord.Interaction, name: str):
    embed = discord.Embed(
        title="🚁 Neuer Einsatz",
        description=f"**{name}**",
        color=discord.Color.green()
    )
    embed.set_footer(text=f"Gemeldet von {interaction.user}")
    await interaction.response.send_message(embed=embed)

# ======================
# Moderation
# ======================

@bot.tree.command(name="kick", description="Mitglied kicken")
@app_commands.describe(mitglied="Mitglied", grund="Grund")
async def kick(
    interaction: discord.Interaction,
    mitglied: discord.Member,
    grund: str = "Kein Grund angegeben"
):
    if not interaction.user.guild_permissions.kick_members:
        await interaction.response.send_message(
            "❌ Keine Berechtigung.",
            ephemeral=True
        )
        return

    await mitglied.kick(reason=grund)

    await interaction.response.send_message(
        f"👢 {mitglied.mention} wurde gekickt.\nGrund: {grund}"
    )

@bot.tree.command(name="ban", description="Mitglied bannen")
@app_commands.describe(mitglied="Mitglied", grund="Grund")
async def ban(
    interaction: discord.Interaction,
    mitglied: discord.Member,
    grund: str = "Kein Grund angegeben"
):
    if not interaction.user.guild_permissions.ban_members:
        await interaction.response.send_message(
            "❌ Keine Berechtigung.",
            ephemeral=True
        )
        return

    await mitglied.ban(reason=grund)

    await interaction.response.send_message(
        f"🔨 {mitglied.mention} wurde gebannt.\nGrund: {grund}"
    )

# ======================
# Notfallmodus
# ======================

@bot.tree.command(
    name="notfall",
    description="Startet den Notfallmodus"
)
async def notfall(interaction: discord.Interaction):

    if interaction.user.id != OWNER_ID:
        await interaction.response.send_message(
            "❌ Nur der Besitzer darf diesen Befehl nutzen.",
            ephemeral=True
        )
        return

    await interaction.response.send_message(
        "@everyone 🚨 NOTFALLMODUS EINGELEITET 🚨"
    )

    kanal = interaction.channel

    for i in range(10, 0, -1):
        await kanal.send(f"⏳ Shutdown in {i} Sekunden...")
        await asyncio.sleep(1)

    await kanal.send(
        "🛑 Bot wird kontrolliert heruntergefahren."
    )

    await bot.close()

bot.run(TOKEN)
