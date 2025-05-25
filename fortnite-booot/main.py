import os
import discord
from discord.ext import commands
from flask import Flask
from threading import Thread

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="/", intents=intents)

queue = []
MAX_PLAYERS = 100
ROLE_NAME = "Кастомки"
queue_message = None

# Панель с кнопками
class QueueView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(JoinButton())
        self.add_item(ClearButton())

class JoinButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="✋ Встать в очередь", style=discord.ButtonStyle.primary)

    async def callback(self, interaction: discord.Interaction):
        user = interaction.user
        if ROLE_NAME not in [role.name for role in user.roles]:
            await interaction.response.send_message(f"{user.mention}, у тебя нет роли **{ROLE_NAME}**.", ephemeral=True)
            return

        if user.id in [u.id for u in queue]:
            await interaction.response.send_message("Ты уже в очереди.", ephemeral=True)
            return

        if len(queue) >= MAX_PLAYERS:
            await interaction.response.send_message("⚠️ Очередь заполнена!", ephemeral=True)
            return

        queue.append(user)
        await interaction.response.send_message(f"{user.mention} добавлен в очередь!", ephemeral=True)
        await update_queue_display()

class ClearButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="🧹 Очистить очередь", style=discord.ButtonStyle.danger)

    async def callback(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("⛔ У тебя нет прав для очистки.", ephemeral=True)
            return

        queue.clear()
        await interaction.response.send_message("Очередь очищена.")
        await update_queue_display()

async def update_queue_display():
    global queue_message
    if queue_message:
        await queue_message.edit(content=f"🎮 Очередь на кастомку: {len(queue)} / {MAX_PLAYERS}")

from discord.ext import commands  # ← уже есть вверху файла

@bot.command()
@commands.has_permissions(administrator=True)
async def panel(ctx):
    global queue_message
    queue_message = await ctx.send(f"🎮 Очередь на кастомку: {len(queue)} / {MAX_PLAYERS}", view=QueueView())
    await ctx.message.delete(delay=5)

@panel.error
async def panel_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("⛔ У тебя нет прав использовать эту команду.", delete_after=5)
@panel.error

async def panel_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        try:
            await ctx.message.delete()
        except:
            pass  # если нет прав удалить
        await ctx.send("⛔ У тебя нет прав использовать эту команду.", delete_after=5)


@bot.command()
async def sendcode(ctx, code: str):
    if not queue:
        await ctx.send("⚠️ Очередь пуста!")
        return

    await ctx.send(f"📨 Рассылаю код ({code}) {len(queue)} игрокам...", delete_after=10)

    for user in queue:
        try:
            await user.send(f"🎮 Код кастомки Fortnite: **{code}**\nЗайди в игру, выбери режим и введи код. https://www.twitch.tv/vp_mistic https://www.twitch.tv/paupau322")
        except discord.Forbidden:
            await ctx.send(f"❌ Не удалось отправить ЛС {user.mention}", delete_after=10)

    queue.clear()
    await update_queue_display()
    await ctx.send("✅ Рассылка завершена и очередь сброшена.", delete_after=10)

REACTION_MESSAGE_ID = 1376146619388530758  # Заменить на настоящий ID

@bot.event
async def on_raw_reaction_add(payload):
    if payload.message_id != REACTION_MESSAGE_ID:
        return
    guild = bot.get_guild(payload.guild_id)
    if not guild:
        return
    role = discord.utils.get(guild.roles, name=ROLE_NAME)
    member = guild.get_member(payload.user_id)
    if member and role:
        await member.add_roles(role)
        print(f"✅ Добавлена роль {role.name} пользователю {member.name}")

@bot.event
async def on_raw_reaction_remove(payload):
    if payload.message_id != REACTION_MESSAGE_ID:
        return
    guild = bot.get_guild(payload.guild_id)
    if not guild:
        return
    role = discord.utils.get(guild.roles, name=ROLE_NAME)
    member = guild.get_member(payload.user_id)
    if member and role:
        await member.remove_roles(role)
        print(f"🚫 Удалена роль {role.name} у пользователя {member.name}")

# Flask для 24/7 Replit
app = Flask(__name__)
@app.route('/')
def home():
    return "Я жив!"
def run():
    app.run(host='0.0.0.0', port=8080)
Thread(target=run).start()

token = ""

try:
    bot.run(token)
except Exception as e:
    print("Ошибка запуска бота:", e)