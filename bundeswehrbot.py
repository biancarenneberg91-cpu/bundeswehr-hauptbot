import discord
from discord.ext import commands
from discord import app_commands
import os
import json
import asyncio

# ======================
# Railway Variablen
# ======================

TOKEN = os.getenv("TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))

# ======================
# Dateien
# ======================

NOTFALL_DATEI = "notfall.json"


def lade_notfall():
    try:
        with open(NOTFALL_DATEI, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"notfall": False}


def speichere_notfall(status):
    with open(NOTFALL_DATEI, "w", encoding="utf-8") as f:
        json.dump({"notfall": status}, f, indent=4)


# ======================
# Bot
# ======================

intents = discord.Intents.default()
intents.members = True
intents.message_content = True


class BundeswehrBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents
        )

    async def setup_hook(self):
        await self.tree.sync()
        print("✅ Slash Commands synchronisiert")


bot = BundeswehrBot()

LOCKDOWN = False


# ======================
# Start
# ======================

@bot.event
async def on_ready():
    global LOCKDOWN

    print(f"🟢 Online als {bot.user}")

    daten = lade_notfall()

    if daten["notfall"]:
        LOCKDOWN = True
        print("🚨 LOCKDOWN AKTIV")


# ======================
# Lockdown Check
# ======================

async def lockdown_check(interaction: discord.Interaction):
    global LOCKDOWN

    if LOCKDOWN:
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message(
                "🚨 Der Bot befindet sich im Notfallmodus.",
                ephemeral=True
            )
            return False

    return True


# ======================
# Ping
# ======================

@bot.tree.command(
    name="ping",
    description="Zeigt die Latenz an"
)
async def ping(interaction: discord.Interaction):

    if not await lockdown_check(interaction):
        return

    await interaction.response.send_message(
        f"🏓 Pong! {round(bot.latency * 1000)} ms"
    )


# ======================
# Hilfe
# ======================

@bot.tree.command(
    name="hilfe",
    description="Zeigt die Befehle"
)
async def hilfe(interaction: discord.Interaction):

    if not await lockdown_check(interaction):
        return

    embed = discord.Embed(
        title="🎖️ Bundeswehr Hauptbot",
        description="Verfügbare Befehle",
        color=discord.Color.blue()
    )

    embed.add_field(
        name="⚙️ Allgemein",
        value="""
/ping
/hilfe
        """,
        inline=False
    )

    embed.add_field(
        name="🛡️ Sicherheit",
        value="""
/notfall
/notfall_aufheben
        """,
        inline=False
    )

    embed.set_footer(text="Teil 1")

    await interaction.response.send_message(
        embed=embed
    )


# ======================
# Notfall
# ======================

@bot.tree.command(
    name="notfall",
    description="Aktiviert den Notfallmodus"
)
async def notfall(interaction: discord.Interaction):

    global LOCKDOWN

    if interaction.user.id != OWNER_ID:
        await interaction.response.send_message(
            "❌ Nur der Besitzer darf das.",
            ephemeral=True
        )
        return

    LOCKDOWN = True
    speichere_notfall(True)

    await interaction.response.send_message(
        "@everyone 🚨 NOTFALLMODUS EINGELEITET 🚨"
    )

    kanal = interaction.channel

    for i in range(10, 0, -1):
        await kanal.send(
            f"⏳ Shutdown in {i} Sekunden..."
        )
        await asyncio.sleep(1)

    await kanal.send(
        "🛑 Lockdown aktiviert."
    )


# ======================
# Notfall aufheben
# ======================

@bot.tree.command(
    name="notfall_aufheben",
    description="Beendet den Notfallmodus"
)
async def notfall_aufheben(
    interaction: discord.Interaction
):

    global LOCKDOWN

    if interaction.user.id != OWNER_ID:
        await interaction.response.send_message(
            "❌ Nur der Besitzer darf das.",
            ephemeral=True
        )
        return

    LOCKDOWN = False
    speichere_notfall(False)

    await interaction.response.send_message(
        "✅ Notfallmodus aufgehoben."
    )


# ======================
# Start
# ======================

bot.run(TOKEN)
DATA_DATEI = "data.json"

def lade_daten():
    try:
        with open(DATA_DATEI, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {
            "warnings": {},
            "dienstgrade": {},
            "dienstzeiten": {}
        }

def speichere_daten(daten):
    with open(DATA_DATEI, "w", encoding="utf-8") as f:
        json.dump(daten, f, indent=4) 
@bot.tree.command(name="kick", description="Mitglied kicken")
@app_commands.describe(mitglied="Mitglied", grund="Grund")
async def kick(interaction: discord.Interaction,
               mitglied: discord.Member,
               grund: str = "Kein Grund"):

    if not await lockdown_check(interaction):
        return

    if not interaction.user.guild_permissions.kick_members:
        await interaction.response.send_message(
            "❌ Keine Berechtigung.",
            ephemeral=True
        )
        return

    await mitglied.kick(reason=grund)

    await interaction.response.send_message(
        f"👢 {mitglied.mention} wurde gekickt."
    )

    await interaction.channel.send(
        f"📋 MOD-LOG\nModerator: {interaction.user.mention}\n"
        f"Aktion: Kick\nBetroffener: {mitglied.mention}\n"
        f"Grund: {grund}"
    ) 
@bot.tree.command(name="ban", description="Mitglied bannen")
@app_commands.describe(mitglied="Mitglied", grund="Grund")
async def ban(interaction: discord.Interaction,
              mitglied: discord.Member,
              grund: str = "Kein Grund"):

    if not await lockdown_check(interaction):
        return

    if not interaction.user.guild_permissions.ban_members:
        await interaction.response.send_message(
            "❌ Keine Berechtigung.",
            ephemeral=True
        )
        return

    await mitglied.ban(reason=grund)

    await interaction.response.send_message(
        f"🔨 {mitglied.mention} wurde gebannt."
    )

    await interaction.channel.send(
        f"📋 MOD-LOG\nModerator: {interaction.user.mention}\n"
        f"Aktion: Ban\nBetroffener: {mitglied.mention}\n"
        f"Grund: {grund}"
    ) 
@bot.tree.command(name="purge", description="Nachrichten löschen")
@app_commands.describe(anzahl="Anzahl")
async def purge(interaction: discord.Interaction,
                anzahl: int):

    if not await lockdown_check(interaction):
        return

    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message(
            "❌ Keine Berechtigung.",
            ephemeral=True
        )
        return

    await interaction.response.defer(ephemeral=True)

    gelöscht = await interaction.channel.purge(limit=anzahl)

    await interaction.followup.send(
        f"🗑️ {len(gelöscht)} Nachrichten gelöscht.",
        ephemeral=True
    )

    await interaction.channel.send(
        f"📋 MOD-LOG\nModerator: {interaction.user.mention}\n"
        f"Aktion: Purge\nGelöscht: {len(gelöscht)} Nachrichten"
    ) 
@bot.tree.command(name="warn", description="Verwarnung vergeben")
@app_commands.describe(mitglied="Mitglied", grund="Grund")
async def warn(interaction: discord.Interaction,
               mitglied: discord.Member,
               grund: str):

    daten = lade_daten()

    uid = str(mitglied.id)

    daten["warnings"][uid] = daten["warnings"].get(uid, 0) + 1

    speichere_daten(daten)

    await interaction.response.send_message(
        f"⚠️ {mitglied.mention} wurde verwarnt.\n"
        f"Grund: {grund}\n"
        f"Verwarnungen: {daten['warnings'][uid]}"
    ) 
@bot.tree.command(name="warnings",
                  description="Verwarnungen anzeigen")
async def warnings(interaction: discord.Interaction,
                   mitglied: discord.Member):

    daten = lade_daten()

    anzahl = daten["warnings"].get(str(mitglied.id), 0)

    await interaction.response.send_message(
        f"⚠️ {mitglied.mention} hat {anzahl} Verwarnungen."
    ) 
@bot.tree.command(name="unwarn",
                  description="Verwarnung entfernen")
async def unwarn(interaction: discord.Interaction,
                 mitglied: discord.Member):

    daten = lade_daten()

    uid = str(mitglied.id)

    if uid in daten["warnings"] and daten["warnings"][uid] > 0:
        daten["warnings"][uid] -= 1

    speichere_daten(daten)

    await interaction.response.send_message(
        f"✅ Eine Verwarnung von {mitglied.mention} wurde entfernt."
    )
    @bot.tree.command(name="dienstbeginn", description="Dienst beginnen")
async def dienstbeginn(interaction: discord.Interaction):

    daten = lade_daten()
    uid = str(interaction.user.id)

    daten["dienstzeiten"][uid] = {
        "aktiv": True
    }

    speichere_daten(daten)

    await interaction.response.send_message(
        f"🟢 {interaction.user.mention} hat den Dienst begonnen."
    )
@bot.tree.command(name="dienstende", description="Dienst beenden")
async def dienstende(interaction: discord.Interaction):

    daten = lade_daten()
    uid = str(interaction.user.id)

    daten["dienstzeiten"][uid] = {
        "aktiv": False
    }

    speichere_daten(daten)

    await interaction.response.send_message(
        f"🔴 {interaction.user.mention} hat den Dienst beendet."
    ) 
@bot.tree.command(name="dienstgrad", description="Dienstgrad anzeigen")
async def dienstgrad(interaction: discord.Interaction,
                     mitglied: discord.Member = None):

    daten = lade_daten()

    if mitglied is None:
        mitglied = interaction.user

    grad = daten["dienstgrade"].get(
        str(mitglied.id),
        "Rekrut"
    )

    await interaction.response.send_message(
        f"🎖️ {mitglied.mention}\nDienstgrad: **{grad}**"
    )
                         @bot.tree.command(name="beförderung",
                  description="Mitglied befördern")
async def befoerderung(interaction: discord.Interaction,
                       mitglied: discord.Member,
                       neuer_grad: str):

    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ Keine Berechtigung.",
            ephemeral=True
        )
        return

    daten = lade_daten()

    daten["dienstgrade"][str(mitglied.id)] = neuer_grad

    speichere_daten(daten)

    await interaction.response.send_message(
        f"🏅 {mitglied.mention} wurde zu **{neuer_grad}** befördert."
    )v
@bot.tree.command(name="einsatz",
                  description="Einsatz ausrufen")
async def einsatz(interaction: discord.Interaction,
                  name: str):

    embed = discord.Embed(
        title="🚁 Neuer Einsatz",
        description=f"**{name}**",
        color=discord.Color.green()
    )

    embed.add_field(
        name="Leitung",
        value=interaction.user.mention,
        inline=False
    )

    await interaction.response.send_message(
        content="@everyone",
        embed=embed
    )
@bot.tree.command(name="lagebericht",
                  description="Lagebericht senden")
async def lagebericht(interaction: discord.Interaction,
                      text: str):

    embed = discord.Embed(
        title="📋 Lagebericht",
        description=text,
        color=discord.Color.blue()
    )

    embed.set_footer(
        text=f"Von {interaction.user}"
    )

    await interaction.response.send_message(
        embed=embed
    )
@bot.tree.command(name="alarm",
                  description="Alarm auslösen")
async def alarm(interaction: discord.Interaction,
                grund: str):

    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ Keine Berechtigung.",
            ephemeral=True
        )
        return

    embed = discord.Embed(
        title="🚨 ALARM",
        description=grund,
        color=discord.Color.red()
    )

    await interaction.response.send_message(
        content="@everyone",
        embed=embed
    )
