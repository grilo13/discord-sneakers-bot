import datetime
import os
import random

from discord.ext import tasks, commands
import discord

from bot import NotificationBot

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN', 'MTEwNDA4NTkyNDUwMzExMzc1OA.GKb-3p.q-d9S0U-U8daoPwZuj6rJM4nQsgJAgGuLSd6is')
TEST_SIZES = ["36", "37", "37.5", "38", "38.5", "39", "39.5", "40", "41", "41.5", "42", "42.5", "43", "44"]

intents = discord.Intents.default()
intents.message_content = True


@tasks.loop(minutes=5)
async def check_sizes():
    shoe_number = '39.5'
    notification_bot = NotificationBot('New Balance', 'BB480LV1-36569', '480', shoe_number)
    is_available = notification_bot.execute_bot()
    guild = await bot.fetch_channel(858708270977646616)
    timestamp = datetime.datetime.now().__str__()
    if is_available:
        await guild.send('@everyone\n'
                         'Your size {} is available. Go get them shoes boy! 🎉 -> {}'.format(shoe_number, timestamp))
    else:
        await guild.send('@everyone\n'
                         'Your size {} isn\'t available yet... but don\'t give up boy! ❌ -> {}'.format(shoe_number,
                                                                                                       timestamp))


intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    check_sizes.start()


bot.run(DISCORD_TOKEN)
