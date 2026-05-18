import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import os
from datetime import datetime

TOKEN = os.getenv("TOKEN")
GUILD_ID = 1504190915235811360  # Server-ID eintragen

DB = "notruf_hamburg_bw.db"
BOT_ZENTRALE = "bot-zentrale"

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


def db():
    return sqlite3.connect(DB)


def setup_db():
    con = db()
    cur = con.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS dienst (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name TEXT,
        start TEXT,
        ende TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS einsaetze (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titel TEXT,
        ort TEXT,
        status TEXT,
        leitung TEXT,
        zeit TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS inventar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        item TEXT,
        typ TEXT,
        von TEXT,
        zeit TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS personalakten (
        user_id INTEGER PRIMARY KEY,
        rang TEXT,
        notiz TEXT,
        status TEXT
    )
    """)

    con.commit()
    con.close()


def kanal(guild, name):
    return discord.utils.get(guild.text_channels, name=name)


async def zentrale(guild):
    ch = kanal(guild, BOT_ZENTRALE)
    if not ch:
        ch = await guild.create_text_channel(BOT_ZENTRALE)
    return ch


@bot.event
async def on_ready():
    setup_db()
    print(f"{bot.user} Hauptbot online!")

    guild = discord.Object(id=GUILD_ID)
    bot.tree.copy_global_to(guild=guild)
    synced = await bot.tree.sync(guild=guild)

    print(f"{len(synced)} Commands geladen.")


@bot.tree.command(name="setup", description="Erstellt alle Notruf Hamburg Bundeswehr Channels")
async def setup(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ Keine Rechte.", ephemeral=True)

    await interaction.response.defer(ephemeral=True)

    channels = [
        "ankundigungen",
        "regeln",
        "einsaetze",
        "alarmierungen",
        "bw-funk",
        "dienstmeldungen",
        "waffenlogs",
        "personalakten",
        "befoerderungen",
        "ausbildung",
        "militarpolizei",
        "bot-zentrale",
        "logs",
        "bot-commands"
    ]

    erstellt = 0

    for ch in channels:
        if not kanal(interaction.guild, ch):
            await interaction.guild.create_text_channel(ch)
            erstellt += 1

    ank = kanal(interaction.guild, "ankundigungen")

    if ank:
        embed = discord.Embed(
            title="🪖 Notruf Hamburg Bundeswehr System",
            description="✅ System aktiviert\n✅ Channels erstellt\n✅ KI-Leitstelle bereit\n\nNutze `/hilfe`.",
            color=0x2E8B57
        )
        await ank.send("@everyone", embed=embed)

    await interaction.followup.send(f"✅ Setup abgeschlossen. Erstellt: {erstellt} Channels", ephemeral=True)


@bot.tree.command(name="ki_scan", description="KI prüft Server und lässt fehlende Channels erstellen")
async def ki_scan(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ Keine Rechte.", ephemeral=True)

    await interaction.response.defer(ephemeral=True)

    z = await zentrale(interaction.guild)

    wichtige = [
        "einsaetze",
        "alarmierungen",
        "bw-funk",
        "dienstmeldungen",
        "waffenlogs",
        "personalakten",
        "befoerderungen",
        "ausbildung",
        "militarpolizei",
        "logs",
        "bot-commands"
    ]

    vorhanden = [c.name for c in interaction.guild.text_channels]
    aufgaben = 0

    for ch in wichtige:
        if ch not in vorhanden:
            await z.send(f"AUFGABE:create_channel:{ch}")
            aufgaben += 1

    await z.send("AUFGABE:status")

    await interaction.followup.send(f"🧠 KI-Scan fertig. {aufgaben} Aufgaben gesendet.", ephemeral=True)


@bot.tree.command(name="alarm", description="Löst Bundeswehr Alarm aus")
async def alarm(interaction: discord.Interaction, stufe: str, ort: str, bedrohung: str, ausruestung: str = "Standardausrüstung"):
    await interaction.response.defer(ephemeral=True)

    embed = discord.Embed(title=f"🚨 ALARMSTUFE {stufe.upper()}", color=0xFF0000)
    embed.add_field(name="📍 Ort", value=ort, inline=True)
    embed.add_field(name="⚠️ Bedrohung", value=bedrohung, inline=False)
    embed.add_field(name="🪖 Ausrüstung", value=ausruestung, inline=False)
    embed.add_field(name="👮 Ausgelöst von", value=interaction.user.mention, inline=True)

    ch = kanal(interaction.guild, "alarmierungen")
    if ch:
        await ch.send(
            "@everyone 🚨 **BUNDESWEHR ALARM**",
            embed=embed,
            allowed_mentions=discord.AllowedMentions(everyone=True)
        )

    z = await zentrale(interaction.guild)
    await z.send(f"ALARM:{stufe}|{ort}|{bedrohung}|{ausruestung}|{interaction.user.mention}")

    await interaction.followup.send("🚨 Alarm ausgelöst und an KI-Leitstelle gesendet.", ephemeral=True)


@bot.tree.command(name="dienst", description="In Dienst gehen")
async def dienst(interaction: discord.Interaction):
    con = db()
    cur = con.cursor()

    cur.execute("SELECT id FROM dienst WHERE user_id=? AND ende IS NULL", (interaction.user.id,))

    if cur.fetchone():
        con.close()
        return await interaction.response.send_message("⚠️ Du bist bereits im Dienst.", ephemeral=True)

    cur.execute(
        "INSERT INTO dienst (user_id, name, start, ende) VALUES (?, ?, ?, NULL)",
        (interaction.user.id, str(interaction.user), datetime.now().strftime("%d.%m.%Y %H:%M"))
    )

    con.commit()
    con.close()

    ch = kanal(interaction.guild, "dienstmeldungen")
    if ch:
        await ch.send(f"🟢 {interaction.user.mention} ist jetzt im Dienst.")

    await interaction.response.send_message("✅ Du bist jetzt im Dienst.", ephemeral=True)


@bot.tree.command(name="undienst", description="Außer Dienst gehen")
async def undienst(interaction: discord.Interaction):
    con = db()
    cur = con.cursor()

    cur.execute("SELECT id FROM dienst WHERE user_id=? AND ende IS NULL", (interaction.user.id,))
    row = cur.fetchone()

    if not row:
        con.close()
        return await interaction.response.send_message("⚠️ Du bist nicht im Dienst.", ephemeral=True)

    cur.execute("UPDATE dienst SET ende=? WHERE id=?", (datetime.now().strftime("%d.%m.%Y %H:%M"), row[0]))

    con.commit()
    con.close()

    await interaction.response.send_message("🔴 Du bist jetzt außer Dienst.", ephemeral=True)


@bot.tree.command(name="dienstliste", description="Zeigt aktive Soldaten")
async def dienstliste(interaction: discord.Interaction):
    con = db()
    cur = con.cursor()

    cur.execute("SELECT name, start FROM dienst WHERE ende IS NULL")
    daten = cur.fetchall()

    con.close()

    text = "\n".join([f"🟢 **{n}** seit {s}" for n, s in daten]) or "Niemand im Dienst."

    await interaction.response.send_message(
        embed=discord.Embed(title="🕒 Dienstliste", description=text, color=0x00FF00),
        ephemeral=True
    )


@bot.tree.command(name="einsatz", description="Erstellt Einsatz")
async def einsatz(interaction: discord.Interaction, titel: str, ort: str, leitung: discord.Member):
    con = db()
    cur = con.cursor()

    cur.execute(
        "INSERT INTO einsaetze (titel, ort, status, leitung, zeit) VALUES (?, ?, ?, ?, ?)",
        (titel, ort, "Aktiv", str(leitung), datetime.now().strftime("%d.%m.%Y %H:%M"))
    )

    eid = cur.lastrowid

    con.commit()
    con.close()

    embed = discord.Embed(title=f"🪖 Einsatz #{eid}", color=0x2E8B57)
    embed.add_field(name="Titel", value=titel, inline=False)
    embed.add_field(name="Ort", value=ort)
    embed.add_field(name="Leitung", value=leitung.mention)
    embed.add_field(name="Status", value="Aktiv")

    ch = kanal(interaction.guild, "einsaetze")
    if ch:
        await ch.send(embed=embed)

    await interaction.response.send_message(f"✅ Einsatz #{eid} erstellt.", ephemeral=True)


@bot.tree.command(name="einsatz_beenden", description="Beendet Einsatz")
async def einsatz_beenden(interaction: discord.Interaction, einsatz_id: int, ergebnis: str):
    con = db()
    cur = con.cursor()

    cur.execute("UPDATE einsaetze SET status=? WHERE id=?", (f"Beendet: {ergebnis}", einsatz_id))

    con.commit()
    con.close()

    await interaction.response.send_message(f"✅ Einsatz #{einsatz_id} beendet.", ephemeral=True)


@bot.tree.command(name="funk", description="Sendet Funkmeldung")
async def funk(interaction: discord.Interaction, nachricht: str):
    ch = kanal(interaction.guild, "bw-funk")

    embed = discord.Embed(title="📻 BW-Funk", description=nachricht, color=0x2F3136)
    embed.add_field(name="Von", value=interaction.user.mention)

    if ch:
        await ch.send(embed=embed)

    await interaction.response.send_message("✅ Funk gesendet.", ephemeral=True)


@bot.tree.command(name="waffe_geben", description="Gibt Waffe aus")
async def waffe_geben(interaction: discord.Interaction, person: discord.Member, waffe: str):
    con = db()
    cur = con.cursor()

    cur.execute(
        "INSERT INTO inventar (user_id, item, typ, von, zeit) VALUES (?, ?, ?, ?, ?)",
        (person.id, waffe, "Waffe", str(interaction.user), datetime.now().strftime("%d.%m.%Y %H:%M"))
    )

    con.commit()
    con.close()

    ch = kanal(interaction.guild, "waffenlogs")
    if ch:
        await ch.send(f"🔫 {waffe} an {person.mention} ausgegeben von {interaction.user.mention}.")

    await interaction.response.send_message("✅ Waffe ausgegeben.", ephemeral=True)


@bot.tree.command(name="ausruestung", description="Gibt Ausrüstung aus")
async def ausruestung(interaction: discord.Interaction, person: discord.Member, item: str):
    con = db()
    cur = con.cursor()

    cur.execute(
        "INSERT INTO inventar (user_id, item, typ, von, zeit) VALUES (?, ?, ?, ?, ?)",
        (person.id, item, "Ausrüstung", str(interaction.user), datetime.now().strftime("%d.%m.%Y %H:%M"))
    )

    con.commit()
    con.close()

    await interaction.response.send_message(f"✅ {item} an {person.mention} ausgegeben.", ephemeral=True)


@bot.tree.command(name="inventar", description="Zeigt Inventar")
async def inventar(interaction: discord.Interaction, person: discord.Member):
    con = db()
    cur = con.cursor()

    cur.execute("SELECT item, typ, von, zeit FROM inventar WHERE user_id=?", (person.id,))
    daten = cur.fetchall()

    con.close()

    text = "\n".join([f"**{typ}:** {item} | von {von} | {zeit}" for item, typ, von, zeit in daten]) or "Kein Inventar."

    await interaction.response.send_message(
        embed=discord.Embed(title=f"🎒 Inventar {person}", description=text[:4000], color=0x2E8B57),
        ephemeral=True
    )


@bot.tree.command(name="personalakte", description="Erstellt Personalakte")
async def personalakte(interaction: discord.Interaction, person: discord.Member, rang: str, status: str, notiz: str = "Keine Notiz"):
    con = db()
    cur = con.cursor()

    cur.execute(
        "INSERT OR REPLACE INTO personalakten (user_id, rang, notiz, status) VALUES (?, ?, ?, ?)",
        (person.id, rang, notiz, status)
    )

    con.commit()
    con.close()

    ch = kanal(interaction.guild, "personalakten")
    if ch:
        embed = discord.Embed(title="📁 Personalakte", color=0x2E8B57)
        embed.add_field(name="Soldat", value=person.mention)
        embed.add_field(name="Rang", value=rang)
        embed.add_field(name="Status", value=status)
        embed.add_field(name="Notiz", value=notiz, inline=False)
        await ch.send(embed=embed)

    await interaction.response.send_message(f"📁 Personalakte für {person.mention} gespeichert.", ephemeral=True)


@bot.tree.command(name="befoerderung", description="Trägt Beförderung ein")
async def befoerderung(interaction: discord.Interaction, person: discord.Member, neuer_rang: str, grund: str):
    con = db()
    cur = con.cursor()

    cur.execute(
        "INSERT OR REPLACE INTO personalakten (user_id, rang, notiz, status) VALUES (?, ?, ?, ?)",
        (person.id, neuer_rang, f"Beförderung: {grund}", "Aktiv")
    )

    con.commit()
    con.close()

    ch = kanal(interaction.guild, "befoerderungen")
    if ch:
        await ch.send(f"🎖️ {person.mention} wurde zu **{neuer_rang}** befördert. Grund: {grund}")

    await interaction.response.send_message("✅ Beförderung gespeichert.", ephemeral=True)


@bot.tree.command(name="stats", description="Zeigt Statistik")
async def stats(interaction: discord.Interaction):
    con = db()
    cur = con.cursor()

    cur.execute("SELECT COUNT(*) FROM dienst WHERE ende IS NULL")
    dienst_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM einsaetze")
    einsatz_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM inventar")
    inventar_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM personalakten")
    personal_count = cur.fetchone()[0]

    con.close()

    embed = discord.Embed(title="📊 Bundeswehr Statistik", color=0x2E8B57)
    embed.add_field(name="Im Dienst", value=str(dienst_count))
    embed.add_field(name="Einsätze", value=str(einsatz_count))
    embed.add_field(name="Inventar", value=str(inventar_count))
    embed.add_field(name="Personalakten", value=str(personal_count))

    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="hilfe", description="Zeigt alle Commands")
async def hilfe(interaction: discord.Interaction):
    embed = discord.Embed(title="🪖 Notruf Hamburg Bundeswehr", color=0x2E8B57)
    embed.add_field(
        name="Commands",
        value=(
            "/setup\n/ki_scan\n/alarm\n/dienst\n/undienst\n/dienstliste\n"
            "/einsatz\n/einsatz_beenden\n/funk\n/waffe_geben\n/ausruestung\n"
            "/inventar\n/personalakte\n/befoerderung\n/stats"
        ),
        inline=False
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


bot.run(TOKEN)
