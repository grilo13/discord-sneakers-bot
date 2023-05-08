import datetime
import os
import json
import sys

from discord.ext import tasks, commands
from discord import app_commands
import discord

from bot import NotificationBot

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN', 'MTEwNDA4NTkyNDUwMzExMzc1OA.GKb-3p.q-d9S0U-U8daoPwZuj6rJM4nQsgJAgGuLSd6is')
TEST_SIZES = ["36", "37", "37.5", "38", "38.5", "39", "39.5", "40", "41", "41.5", "42", "42.5", "43", "44"]

users_info = {}

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


def save_user_schedules():
    with open("user_info.json", "w") as f:
        json.dump(users_info, f)


async def user_schedules() -> list or bool:
    print(bot.user.id)
    user = users_info.get(bot.user.id)

    print("user", user)

    if user:
        return users_info.get(user).get('schedules')
    else:
        return False


async def check_sizes(brand: str, reference: str, model: str, size: int):
    notification_bot = NotificationBot(brand, reference, model, size)
    is_available = notification_bot.execute_bot()
    guild = await bot.fetch_channel(858708270977646616)
    timestamp = datetime.datetime.now().__str__()
    if is_available:
        await guild.send('@everyone\n'
                         'Your size {} is available. Go get them shoes boy! 🎉 -> {}'.format(size, timestamp))
    else:
        await guild.send('@everyone\n'
                         'Your size {} isn\'t available yet... but don\'t give up boy! ❌ -> {}'.format(size,
                                                                                                       timestamp))


@bot.tree.command(name='start_schedules', description='Starts the Schedules')
async def start_schedules(interaction: discord.Interaction):
    global users_info
    user = interaction.user
    users = users_info.get('users')
    user_prev_schedules = users.get(str(user.id))

    if user_prev_schedules is None:
        await interaction.response.send_message('User {} doesn\'t have any schedule to be started'.format(user.name))
    else:
        schedules = user_prev_schedules.get('schedules')
        await interaction.response.send_message(
            'User {} has {} schedules to be started.'.format(user.name, len(schedules)))

        for schd in schedules:
            minutes = schd.get('minutes')
            brand = schd.get('brand')
            model = schd.get('model')
            size = schd.get('size')
            reference = schd.get('reference')
            new_task = tasks.loop(minutes=minutes)(check_sizes)
            new_task.start(brand, reference, model, size)


@bot.tree.command(name='add_schedule', description="Creates a new Schedule for a product")
@app_commands.choices(brand=[app_commands.Choice(name='nb', value='New Balance'),
                             app_commands.Choice(name='nike', value='Nike')])
async def add_schedule(interaction: discord.Interaction, brand: str, reference: str, size: str, model: str,
                       minutes: int):
    global users_info
    user_schedules = users_info.get('users').get(str(interaction.user.id))

    task_body = {'minutes': minutes, 'brand': brand, 'reference': reference, 'model': model, 'size': size}

    if user_schedules:
        print("here")
        user_schedules.get('schedules').append(task_body)
    else:
        print("here2")
        users_info.get('users').update(
            {interaction.user.id: {"schedules": [task_body]}})

    save_user_schedules()

    new_task = tasks.loop(minutes=minutes)(check_sizes)
    new_task.start(brand, reference, model, size)

    print(users_info)
    await interaction.response.send_message(
        'Creating new schedule.. user already has {}'.format(
            len(users_info.get('users').get(str(interaction.user.id)).get('schedules'))))


@bot.event
async def on_ready():
    global users_info
    with open("user_info.json") as f:
        users_info = json.load(f)

    synced_commands = await bot.tree.sync()  # sync all bot commands into the "tree"
    print("Slash commands synced + {}".format(len(synced_commands)))


bot.run(DISCORD_TOKEN)
