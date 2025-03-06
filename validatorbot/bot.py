# bot.py (main file)

import os
import discord
import asyncio
from discord.ext import commands
from dotenv import load_dotenv
from utils.cache import selected_validators
import logging

# Загрузка переменных окружения
load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))
GUILD_ID = int(os.getenv('GUILD_ID'))

intents = discord.Intents.default()
intents.message_content = True

logging.basicConfig(level=logging.DEBUG)
# Создаём объект Bot с префиксом для текстовых команд
bot = commands.Bot(command_prefix='/', intents=intents)

# Фоновая задача для обновления кэша валидаторов и мониторинга
async def background_validator_cache_updater():
    """Фоновая задача для обновления кэша валидаторов и мониторинга каждые 4 минуты."""
    from utils.validator_data import get_validator_uptimes
    while True:
        await get_validator_uptimes()
        await asyncio.sleep(240)  # 4 минуты

# Событие при готовности бота
@bot.event
async def on_ready():
    print(f'Bot has connected to Discord as {bot.user}')
    await load_cogs()

    # Синхронизация команд приложения
    try:
        synced = await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f"Synced {len(synced)} commands to the guild {GUILD_ID}")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

    # Запускаем фоновую задачу мониторинга
    bot.loop.create_task(background_validator_cache_updater())
    bot.loop.create_task(start_monitoring())

# Функция для загрузки когов
async def load_cogs():
    # Список ваших когов, которые вы хотите загрузить
    cogs = ['cogs.validators']
    for cog in cogs:
        try:
            await bot.load_extension(cog)
            print(f'Successfully loaded {cog}')
        except Exception as e:
            print(f'Failed to load {cog}: {e}')

# Задача для мониторинга валидаторов
async def start_monitoring():
    from utils.validator_monitor import monitor_validators
    channel_id = int(os.getenv("CHANNEL_ID"))
    bot.loop.create_task(monitor_validators(bot, channel_id))

# Запуск бота
if __name__ == "__main__":
    bot.run(TOKEN)