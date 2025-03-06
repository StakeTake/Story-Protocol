# utils/validator_monitor.py

import asyncio
import aiohttp
import json
import base64
import logging
import discord
from hashlib import sha256
from bech32 import bech32_encode, convertbits
from discord import Embed, Client
from dotenv import load_dotenv
import os
from utils.cache import validator_cache, selected_validators
from utils.validator_data import get_validator_uptimes
from utils.validator_data import check_api_availability

load_dotenv()

COSMOS_API_URL = os.getenv("COSMOS_API_URL")
COSMOS_RESERVE_API_URL = os.getenv("COSMOS_RESERVE_API_URL")

previous_states = {}

alert_priority = {
    'jailed': 5,
    'inactive_jailed': 7,
    'unjailed_active': 8,
    'unjailed_inactive': 9,
    'active': 4,
    'inactive_insufficient': 6,
    'commission': 2,
    'uptime': 3,
    'new_validator': 1
}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def monitor_validators(bot: Client, channel_id: int):
    logger.info("Starting monitor_validators function.")
    while True:
        try:
            logger.info("Checking validators and updating cache...")
            await update_validator_cache(bot, channel_id)
        except Exception as e:
            logger.error(f"Error during monitoring: {e}")
        await asyncio.sleep(4 * 60)  # Интервал обновления - 4 минут

async def update_validator_cache(bot, channel_id):
    """Фоновая задача для обновления кэша валидаторов и мониторинга."""
    try:
        await get_validator_uptimes()
        validator_data = validator_cache["data"]
        summary = validator_cache["summary"]
        validator_cache["last_updated"] = discord.utils.utcnow()

        logger.info("Validator cache updated. Now checking for alerts...")

        # Выполнение проверки на изменения и отправка алертов
        await check_validators(bot, channel_id, validator_data)

    except Exception as e:
        logger.error(f"Error updating validator cache: {e}")

async def check_validators(bot: Client, channel_id: int, validator_data):
    alerts = []
    global previous_states

    if not previous_states:
        previous_states = {v: data for v, data in validator_data.items()}
        logger.info("Initialized previous_states with current validators.")
        return

    for operator_address, validator in validator_data.items():
        moniker = validator['moniker']
        status = validator['status']
        jailed = validator['jailed']
        commission = validator.get('commission', 0)
        uptime = validator['uptime']
        previous_state = previous_states.get(operator_address)

        validator_alerts = []

        if previous_state:
            prev_status = previous_state.get('status')
            prev_jailed = previous_state.get('jailed')
            prev_commission = previous_state.get('commission')
            prev_uptime = previous_state.get('uptime')

            #logger.debug(f"Previous state for {moniker}: status={prev_status}, jailed={prev_jailed}, commission={prev_commission}, uptime={prev_uptime}")
            #logger.debug(f"Current state for {moniker}: status={status}, jailed={jailed}, commission={commission}, uptime={uptime}")

            # Проверяем изменения и добавляем возможные алерты
            if commission != prev_commission:
                alert = generate_alert("commission", moniker, prev_commission, commission, operator_address)
                validator_alerts.append(('commission', alert))
            if not prev_jailed and jailed:
                alert = generate_alert("jailed", moniker, None, None, operator_address)
                validator_alerts.append(('jailed', alert))
            elif prev_jailed and not jailed:
                if status == "BOND_STATUS_BONDED":
                    alert = generate_alert("unjailed_active", moniker, None, None, operator_address)
                    validator_alerts.append(('unjailed_active', alert))
                else:
                    alert = generate_alert("unjailed_inactive", moniker, None, None, operator_address)
                    validator_alerts.append(('unjailed_inactive', alert))
            if prev_status != status:
                if prev_status == "BOND_STATUS_BONDED" and status != "BOND_STATUS_BONDED":
                    if jailed:
                        alert = generate_alert("inactive_jailed", moniker, None, None, operator_address)
                        validator_alerts.append(('inactive_jailed', alert))
                    else:
                        alert = generate_alert("inactive_insufficient", moniker, None, None, operator_address)
                        validator_alerts.append(('inactive_insufficient', alert))
                elif prev_status != "BOND_STATUS_BONDED" and status == "BOND_STATUS_BONDED":
                    alert = generate_alert("active", moniker, None, None, operator_address)
                    validator_alerts.append(('active', alert))
            if status == "BOND_STATUS_BONDED" and not jailed:
                uptime_alert = check_uptime_alert(moniker, prev_uptime, uptime, operator_address)
                if uptime_alert:
                    validator_alerts.append(('uptime', uptime_alert))
        else:
            # Если предыдущего состояния нет, пропускаем этот валидатор
            # Это предотвратит отправку алертов для валидаторов без предыдущего состояния
            logger.debug(f"No previous state for validator {moniker} ({operator_address}), skipping alerts.")
            pass

        # Выбираем алерт с наивысшим приоритетом
        if validator_alerts:
            highest_priority_alert = min(validator_alerts, key=lambda x: alert_priority.get(x[0], 99))
            alerts.append(highest_priority_alert[1])

        # Обновляем состояние валидатора
        previous_states[operator_address] = validator

    # Отправляем алерты
    if alerts:
        channel = await bot.fetch_channel(channel_id)
        for alert in alerts:
            try:
                embed = Embed(title="Validator Alert", description=alert, color=discord.Color.red() if "⚠️" in alert or "🔴" in alert else discord.Color.green())
                await channel.send(embed=embed, allowed_mentions=discord.AllowedMentions(users=True))
                logger.info(f"Sent alert: {alert}")
            except Exception as e:
                logger.error(f"Failed to send alert: {e}")


def generate_alert(alert_type, moniker, old_value, new_value, operator_address):
    """Генерация текста алертов."""
    operator_address = operator_address.lower()
    logger.debug(f"Generating alert: {alert_type} for {moniker} ({operator_address})")
    logger.debug(f"Selected validators: {selected_validators}")
    user_list = [user_id for user_id, val_addr in selected_validators.items() if val_addr == operator_address]
    logger.debug(f"Users to mention: {user_list}")
    user_mentions = " ".join(f"<@{user_id}>" for user_id in user_list)

    if alert_type == "commission":
        return f"⚠️ **{moniker}** has changed commission from **{old_value * 100:.2f}%** to **{new_value * 100:.2f}%**. {user_mentions}"
    elif alert_type == "inactive_jailed":
        return f"🔴 **{moniker}** is now **inactive and jailed**. {user_mentions}"
    elif alert_type == "inactive_insufficient":
        return f"🔴 **{moniker}** is now **inactive due to insufficient tokens**. {user_mentions}"
    elif alert_type == "active":
        return f"🟢 **{moniker}** is now **active**. {user_mentions}"
    elif alert_type == "unjailed_active":
        return f"🟢 **{moniker}** has been **unjailed and is now active**. {user_mentions}"
    elif alert_type == "unjailed_inactive":
        return f"⚠️ **{moniker}** has been **unjailed but is still inactive**. {user_mentions}"
    elif alert_type == "jailed":
        return f"🔴 **{moniker}** has been **jailed**. {user_mentions}"
    elif alert_type == "new_validator":
        return f"🆕 **New validator {moniker}** has joined the network. {user_mentions}"
    return None

def check_uptime_alert(moniker, prev_uptime, current_uptime, operator_address):
    """Проверка пороговых значений аптайма и генерация одного алерта."""
    thresholds = [95, 90, 80, 70, 60, 50]
    for threshold in thresholds:
        if prev_uptime < threshold <= current_uptime:
            return f"🟢 **{moniker}** uptime has risen above {threshold}%: now at {current_uptime}%."
        elif prev_uptime >= threshold > current_uptime:
            return f"⚠️ **{moniker}** uptime has dropped below {threshold}%: now at {current_uptime}%."
    return None