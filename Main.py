from datetime import datetime
import os
import io
import json
from typing import Optional

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

with open("lookup.json") as f:
    lookup = json.load(f)

async def init_db():
    db = await aiosqlite.connect('data.db')
    await db.execute("""
        CREATE TABLE IF NOT EXISTS flights (
            user_id TEXT NOT NULL,
            departure TEXT NOT NULL,
            arrival TEXT NOT NULL,
            time FLOAT NOT NULL,
            date DATE NOT NULL,
            server BIGINT NOT NULL,
            id BIGINT NOT NULL PRIMARY KEY
        )
    """)
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
    now = datetime.now()

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

    db = await aiosqlite.connect("data.db")

    time = hours + (minutes / 60)

    await db.execute("""
        INSERT INTO flights (user_id, departure, arrival, time, date, server, id)
        VALUES (?, ?, ?, ?, ?, ?, ?)""", (interaction.user.id, departure.upper(), arrival.upper(), time, now.strftime("%Y-%m-%d"), interaction.guild_id, int(now.timestamp())))
    await db.commit()
    await db.close()

    await interaction.followup.send(
        content=
f"""Flight logged!
From: {departure.upper()}
To: {arrival.upper()}
Time: {hours} hours {minutes} minutes
id: {int(now.timestamp())}"""
, file=file)

@bot.tree.command(name="json", description="Produces a dump of all JSON data from this server")
async def get_json(interaction: discord.Interaction):
    
    async with aiosqlite.connect('data.db') as db:
        db.row_factory = aiosqlite.Row

        async with db.execute("SELECT * FROM flights WHERE server = ?", (interaction.guild_id,)) as cursor:
            rows = await cursor.fetchall()
            result = [dict(row) for row in rows]
            string = json.dumps(result, default=str, indent=4)
    file = io.StringIO(string)
    file = discord.File(file, filename="data.json")

    await interaction.response.send_message(file=file, content=f"JSON dump for server {interaction.guild.name} ({interaction.guild_id})", ephemeral=True)

@bot.tree.command(name="stats", description="Get flight hours and flight counts")
@app_commands.describe(
    user= "The person's stats you want to check (leave blank for everyone)",
    start= "Start of the time period (YYYY-MM-DD) (leave blank for no limit)",
    end= "End of the time period (YYYY-MM-DD) (leave blank for no limit)"
)
async def stats(
    interaction: discord.Interaction,
    user: Optional[discord.Member] = None,
    start: Optional[str] = None,
    end: Optional[str] = None):
    start_times = []
    end_times = []

    if start is None:
        start = "0000-01-01"
    if end is None:
        end = "9999-12-31"

    for time in start.split("-"):
        start_times.append(int(time))
    for time in end.split("-"):
        end_times.append(int(time))
    
    if end_times[0] - start_times[0] == 0:
        same_year = True
    elif end_times[0] - start_times[0] < 0:
        await interaction.response.send_message(f"Invalid years: {end_times[0]} is before {start_times[0]}", ephemeral=True)
        return
    year = (start_times[0], end_times[0])

    if end_times[1] > 12 or end_times[1] < 1 or type(end_times[1]) != int:
        await interaction.response.send_message(f"Invalid month: there isn't a {end_times[1]}th month", ephemeral=True)
        return
    if start_times[1] > 12 or end_times[1] < 1 or type(end_times[1]) != int:
        await interaction.response.send_message(f"Invalid month: there isn't a {start_times[1]}th month", ephemeral=True)
        return
    
    if start_times[2] < 1:
        await interaction.response.send_message(f"Invalid day: {start_times[2]} isn't a valid date", ephemeral=True)
    if end_times[2] < 1:
        await interaction.response.send_message(f"Invalid day: {end_times[2]} isn't a valid date", ephemeral=True) 

    for month in lookup["Months"]:
        if month["int"] == start_times[1] and month["days"] < start_times[2]:
            await interaction.response.send_message(f"Invalid day: {start_times[2]} is greater than the amount of days in {month["word"]} ({month["days"]})", ephemeral=True)
            return
        if month["int"] == end_times[1] and month["days"] < end_times[2]:
            await interaction.response.send_message(f"Invalid day: {end_times[2]} is greater than the amount of days in {month["word"]} ({month["days"]})", ephemeral= True)
            return
        
    if user is None:
        async with aiosqlite.connect("data.db") as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM flights WHERE server = ? AND date BETWEEN ? AND ?", (interaction.guild_id, start, end)) as cursor:
                rows = await cursor.fetchall()
                flights = [dict(row) for row in rows]
    else:
        async with aiosqlite.connect("data.db") as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM flights WHERE server = ? AND user_id = ? AND date BETWEEN ? AND ?", (interaction.guild_id, user.id, start, end)) as cursor:
                rows = await cursor.fetchall()
                flights = [dict(row) for row in rows]
    
    total_time = 0
    departures = []
    arrivals = []
    users = []

    if not flights:
        if user is None:
            await interaction.response.send_message(f"There's no flights logged for {interaction.guild.name} currently", ephemeral=True)
            return
        
        await interaction.response.send_message(f"There's no flights logged for {user}", ephemeral=True)

    for log in flights:
        total_time += log["time"]
        departures.append(log["departure"])
        arrivals.append(log["departure"])
        
        if user is None:
            found = False
            for pilot in users:
                found = True
                if pilot["user_id"] == log["user_id"]:
                    pilot["time"] = pilot["time"] + log["time"]
                    pilot["flights"] = pilot["flights"] + 1
                    pilot["departures"].append(log["departure"])
                    pilot["arrivals"].append(log["arrival"])
            if not found:
                users.append({
                    "user_id": log["user_id"],
                    "time": log["time"],
                    "flights": 1,
                    "departures": [log["departure"]],
                    "arrivals": [log["arrival"]]
                })
    
    time_components = str(total_time).split(".")
    hours = time_components[0]
    minutes = int(round(float("0." + time_components[1]) * 60, 0))
    if user is None:
        msg = f"""Server statistics for {interaction.guild.name}:
From {start} - {end}

Total flights: {len(flights)}
Total hours: {total_time}h ({hours}h {minutes}m)"""
    else:
        msg = f"""Flight statistics for {user.mention}:
From {start} - {end}

Total flights: {len(flights)}
Total hours: {total_time}h ({hours}h {minutes}m)"""
    
    await interaction.response.send_message(msg, allowed_mentions=discord.AllowedMentions(users=False))

@bot.event
async def on_ready():
    await init_db()
    try:
        synced = await bot.tree.sync()
    except discord.HTTPException as e:
        print(f"HTTP Error: {e.status} - {e.text}")
    except Exception as e:
        print(f"idfk what error: {e}")

bot.run(TOKEN) 