import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.tree.command(name="ping", description="the hello world of bots")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong!")


@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print("synced these commands:")
        for cmd in synced:
            print(f"   - /{cmd.name}")
    except discord.HTTPException as e:
        print(f"HTTP Error: {e.status} - {e.text}")
    except Exception as e:
        print(f"idfk what error: {e}")

bot.run('<sry github no token 4 u>')