import os
import io

import aiosqlite
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TOKEN")
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

async def init_db():
    db = await aiosqlite.connect('bot_data.db')
    await db.execute('''
        CREATE TABLE IF NOT EXISTS flights (
            user_id TEXT NOT NULL,
            departure TEXT NOT NULL,
            arrival TEXT NOT NULL,
            time FLOAT NOT NULL,
            date DATE NOT NULL,
            id BIGINT NOT NULL PRIMARY KEY
        )
    ''')
    await db.commit()
    return db

@bot.tree.command(name="ping", description="the hello world of bots")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong!")

@bot.tree.command(name="log", description="log a new flight")
@app_commands.describe(
    departure="ICAO of where you departed from",
    arrival="ICAO of where you flew to",
    hours="Hours spent off-blocks",
    minutes="Minutes spent off-blocks (0-59)",
    image="Screenshot of the flight"
)
async def log(interaction: discord.Interaction, 
            departure: str, 
            arrival: str, 
            hours: int, 
            minutes: int,
            image: discord.Attachment):
    invalid = False
    await interaction.response.defer()
    # Data verifying goes brr
    if len(departure) != 4 or len(arrival) != 4:
        invalid = True
    elif not (departure.isalpha() and arrival.isalpha()):
        invalid = True
    if invalid:
        await interaction.followup.send("Invalid airport code(s) used", ephemeral=True)
        return
    
    if minutes > 59:
        await interaction.followup.send("Minutes is over 59", ephemeral=True)
        return
    
    image_data = await image.read()
    file = discord.File(fp=io.BytesIO(image_data), filename="image.png")

    await interaction.followup.send(
        content=f"You flew from {departure} to {arrival} in {hours}:{minutes}", file=file)

@bot.event
async def on_ready():
    await init_db()
    try:
        synced = await bot.tree.sync()
        print("synced these commands:")
        for cmd in synced:
            print(f"   - /{cmd.name}")
    except discord.HTTPException as e:
        print(f"HTTP Error: {e.status} - {e.text}")
    except Exception as e:
        print(f"idfk what error: {e}")

bot.run(TOKEN)