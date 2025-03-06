# buttons/validator_list.py

import discord
import asyncio
import aiohttp
import json
import base64
import hashlib
import bech32
import logging
from dotenv import load_dotenv
import os
from Crypto.Hash import RIPEMD160
from utils.cache import validator_cache
from utils.cache import selected_validators

# Загрузка переменных окружения
load_dotenv()

COSMOS_RPC_URL = os.getenv("COSMOS_RPC_URL")
COSMOS_RESERVE_RPC_URL = os.getenv("COSMOS_RESERVE_RPC_URL")
COSMOS_API_URL = os.getenv("COSMOS_API_URL")
COSMOS_RESERVE_API_URL = os.getenv("COSMOS_RESERVE_API_URL")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Проверка, что все переменные окружения установлены
required_env_vars = ["COSMOS_RPC_URL", "COSMOS_RESERVE_RPC_URL", "COSMOS_API_URL", "COSMOS_RESERVE_API_URL"]
missing_env_vars = [var for var in required_env_vars if os.getenv(var) is None]

if missing_env_vars:
    logger.error(f"One or more required environment variables are not set: {', '.join(missing_env_vars)}")
    exit(1)
else:
    for var in required_env_vars:
        logger.info(f"{var} is set to {os.getenv(var)}")

async def handle_validator_list(interaction: discord.Interaction):
    """Возвращаем данные о валидаторах из кэша."""
    validator_data = validator_cache.get("data", {})
    summary = validator_cache.get("summary", {})
    
    if not validator_data or not summary:
        await interaction.response.send_message("Validator data is not available at the moment.", ephemeral=True)
        return

    await send_embed(interaction, validator_data, summary)


async def send_embed(interaction, validator_data, summary):
    try:
        await interaction.response.defer(ephemeral=True)  # Отложить ответ

        lines = []
        for operator_address, data in validator_data.items():
            status = data.get('status')
            jailed = data.get('jailed', False)
            moniker = data.get('moniker', 'Unknown')
            uptime = data.get('uptime', 0)

            if status == "BOND_STATUS_BONDED" and not jailed:
                if uptime >= 95:
                    color = "🟢"
                elif uptime >= 90:
                    color = "🟩"
                elif uptime >= 80:
                    color = "🟨"
                elif uptime >= 70:
                    color = "🟧"
                elif uptime >= 60:
                    color = "🟥"
                else:
                    color = "⚫"

                lines.append(f"{color} **{moniker}**: {uptime}%")

        footer_text = (
            "\n\n**Legend:**\n"
            "🟢 Uptime >= 95%\n"
            "🟩 90% <= Uptime < 95%\n"
            "🟨 80% <= Uptime < 90%\n"
            "🟧 70% <= Uptime < 80%\n"
            "🟥 60% <= Uptime < 70%\n"
            "⚫ Uptime < 60%\n"
            f"\nTotal validators: {summary['total']}"
            f"\nActive validators: {summary['active']}"
            f"\nInactive validators: {summary['inactive']}"
            f"\nJailed validators: {summary['jailed']}"
        )

        # Разбиваем список lines на части так, чтобы каждая часть не превышала 4000 символов
        parts = []
        current_part = ""
        for line in lines:
            if len(current_part) + len(line) + len(footer_text) < 4000:
                current_part += line + "\n"
            else:
                parts.append(current_part + footer_text)
                current_part = line + "\n"
        if current_part:
            parts.append(current_part + footer_text)

        # Отправляем каждую часть в отдельном сообщении
        for part in parts:
            embed = discord.Embed(
                title="Validator Uptime",
                description=part,
                color=discord.Color.blue()
            )
            embed.set_footer(text="Built by Stake-Take")
            try:
                await interaction.followup.send(embed=embed, ephemeral=True)
            except discord.errors.HTTPException as e:
                logger.error(f"Failed to send embed: {e}")

    except discord.errors.NotFound:
        logger.error("Interaction not found or already timed out.")

async def update_validator_cache():
    """Фоновая задача для обновления кэша списка валидаторов и аптайма."""
    try:
        logger.info("Updating validator cache...")

        # Запрос списка валидаторов и аптайма
        validator_data, summary = await get_validator_uptimes(COSMOS_API_URL)

        validator_cache["data"] = validator_data
        validator_cache["summary"] = summary
        validator_cache["last_updated"] = discord.utils.utcnow()

        logger.info("Validator cache updated successfully.")
    except Exception as e:
        logger.error(f"Error updating validator cache: {e}")
