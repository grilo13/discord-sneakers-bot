import datetime
import os
import json
import asyncio

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
            schd['task'] = new_task.get_task().get_name()
            print(schd['task'])
            save_user_schedules()


@bot.tree.command(name='add_schedule', description="Creates a new Schedule for a product")
@app_commands.choices(brand=[app_commands.Choice(name='nb', value='New Balance'),
                             app_commands.Choice(name='nike', value='Nike')])
async def add_schedule(interaction: discord.Interaction, brand: str, reference: str, size: str, model: str,
                       minutes: int):
    global users_info
    user_schedules = users_info.get('users').get(str(interaction.user.id))

    if len(user_schedules.get('schedules')) == user_schedules.get('max_number_of_schedules'):
        await interaction.response.send_message('You already have the maximum Schedules for your subscription...')
    else:
        task_body = {'minutes': minutes, 'brand': brand, 'reference': reference, 'model': model, 'size': size}

        if user_schedules:
            new_task = tasks.loop(minutes=minutes)(check_sizes)
            new_task.start(brand, reference, model, size)
            task_body['task'] = new_task.get_task().get_name()
            user_schedules.get('schedules').append(task_body)
        else:
            new_task = tasks.loop(minutes=minutes)(check_sizes)
            new_task.start(brand, reference, model, size)
            task_body['task'] = new_task.get_task().get_name()
            users_info.get('users').update({interaction.user.id: {"schedules": [task_body]}})

        save_user_schedules()

        print(users_info)
        await interaction.response.send_message(
            'Creating new schedule.. user already has {}'.format(
                len(users_info.get('users').get(str(interaction.user.id)).get('schedules'))))


@bot.tree.command(name='check_schedules', description='Check user schedules')
async def check_schedules(interaction: discord.Interaction):
    global users_info
    list_embededs = []
    user_info = users_info.get('users').get(str(interaction.user.id))

    if user_info is None:
        await interaction.response.send_message('User {} doesn\'t have any schedules'.format(interaction.user.name))
    else:
        user_schedules = user_info.get('schedules')
        user_max_number = user_info.get('max_number_of_schedules')
        counter = 1
        for schedules in user_schedules:
            embed = discord.Embed(title='User Schedule {}'.format(counter),
                                  description='Here is the User {} Schedules'.format(interaction.user.name),
                                  color=discord.Color.blue(), timestamp=interaction.created_at)
            embed.set_thumbnail(url=interaction.user.avatar)
            embed.add_field(name="ID", value=interaction.user.id)
            embed.add_field(name="Name", value="{}#{}".format(interaction.user.name, interaction.user.discriminator))
            embed.add_field(name='Brand', value=schedules.get('brand'))
            embed.add_field(name='Reference', value=schedules.get('reference'))
            embed.add_field(name='Model', value=schedules.get('model'))
            embed.add_field(name='Size', value=schedules.get('size'))

            if schedules.get('image') is not None:
                embed.set_image(url=schedules.get('image'))

            list_embededs.append(embed)

            counter += 1

        await interaction.response.send_message(embeds=list_embededs,
                                                view=DeleteScheduleButton(task_id=schedules.get("task")))


@bot.tree.command(name='stop_bot', description='Stops the bot from Listening')
async def shutdown(interaction: discord.Interaction):
    await interaction.response.send_message('Shutting down the Bot {}...'.format(bot.user))

    await bot.close()


class DeleteScheduleButton(discord.ui.View):
    def __init__(self, task_id: str):
        self.task_id = task_id
        super().__init__(timeout=None)

    @discord.ui.button(label='Delete Schedule', style=discord.ButtonStyle.red)
    async def delete_schedule(self, interaction: discord.Interaction, button: discord.ui.Button):
        global users_info
        await interaction.response.send_message(
            'Button has just been pressed... user trying to delete Schedule {}'.format(self.task_id))

        for tasks in asyncio.all_tasks():
            if tasks.get_name() == self.task_id:
                tasks.cancel('SchedulerTask has just been canceled')
                print("Task is ready for being removed")

        user_schedules: list = users_info.get('users').get(str(interaction.user.id)).get('schedules')
        for index, schedule in enumerate(user_schedules):
            if schedule.get('task') == self.task_id:
                user_schedules.pop(index)
                print("Just removed schedule {}".format(schedule.get('task')))
                save_user_schedules()

    @discord.ui.button(label='Add Schedule', style=discord.ButtonStyle.success)
    async def add_schedule(self, interaction: discord.Interaction, button: discord.ui.Button):
        global users_info
        user_schedules = users_info.get('users').get(str(interaction.user.id))

        if len(user_schedules.get('schedules')) == user_schedules.get('max_number_of_schedules'):
            await interaction.response.send_message('You already have the maximum Schedules for your subscription...')
        await interaction.response.send_message('Button has just been pressed... adding new Schedule')


@bot.event
async def on_ready():
    print("Bot {} has just arrived in the Server!".format(bot.user))
    global users_info
    with open("user_info.json") as f:
        users_info = json.load(f)

    synced_commands = await bot.tree.sync()  # sync all bot commands into the "tree"
    print("Slash commands synced + {}".format(len(synced_commands)))


bot.run(DISCORD_TOKEN)
