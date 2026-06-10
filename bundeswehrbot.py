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
