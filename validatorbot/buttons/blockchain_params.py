# buttons/blockchain_params.py

import aiohttp
import discord
import os
import logging
from dotenv import load_dotenv
from utils.cache import selected_validators
import datetime

load_dotenv()
logger = logging.getLogger(__name__)

COSMOS_API_URL = os.getenv("COSMOS_API_URL")
COSMOS_RPC_URL = os.getenv("COSMOS_RPC_URL")

def parse_iso_format(date_string):
    try:
        # Split date and time
        date_part, time_part = date_string.split('T')
        
        # Further split date
        year, month, day = map(int, date_part.split('-'))
        
        # Split time and handle microseconds if present
        if '.' in time_part:
            time_part, microseconds_part = time_part.split('.')
            hour, minute, second = map(int, time_part.split(':'))
            # Обрезаем микросекунды до 6 знаков
            microsecond = int(microseconds_part.rstrip('Z')[:6])
        else:
            hour, minute, second = map(int, time_part.rstrip('Z').split(':'))
            microsecond = 0
        
        # Construct datetime object
        return datetime.datetime(year, month, day, hour, minute, second, microsecond, tzinfo=datetime.timezone.utc)
    except Exception as e:
        logger.error(f"Error parsing ISO date format: {e}")
        return None

async def fetch_staking_params():
    url = f"{COSMOS_API_URL}/cosmos/staking/v1beta1/params"
    return await fetch_params(url, "Staking Params")

async def fetch_slashing_params():
    url = f"{COSMOS_API_URL}/cosmos/slashing/v1beta1/params"
    return await fetch_params(url, "Slashing Params")

async def fetch_inflation():
    url = f"{COSMOS_API_URL}/cosmos/mint/v1beta1/inflation"
    return await fetch_params(url, "Inflation")

async def fetch_mint_params():
    url = f"{COSMOS_API_URL}/cosmos/mint/v1beta1/params"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    params = data.get('params', {})
                    embed = discord.Embed(title="Mint Params", color=discord.Color.green())
                    for key, value in params.items():
                        # Форматируем числа с плавающей точкой
                        try:
                            if '.' in value:
                                value = float(value)
                                value_str = f"{value:.2f}"
                            else:
                                value_str = value
                        except (ValueError, TypeError):
                            value_str = str(value)
                        if len(value_str) > 1024:
                            value_str = value_str[:1021] + '...'
                        embed.add_field(name=key, value=str(value), inline=False)
                    return embed
                else:
                    logger.error(f"Failed to fetch Mint Params: {response.status}")
                    return None
    except Exception as e:
        logger.error(f"Error fetching Mint Params: {e}")
        return None

async def fetch_genesis():
    url = f"{COSMOS_RPC_URL}/genesis"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    genesis = data.get('result', {}).get('genesis', {})
                    genesis_time_iso = genesis.get('genesis_time', 'N/A')
                    
                    try:
                        # Корректируем строку даты, обрезая микросекунды до 6 знаков
                        if 'Z' in genesis_time_iso:
                            genesis_time_iso = genesis_time_iso.replace('Z', '+00:00')
                        
                        if '.' in genesis_time_iso:
                            # Разделяем на дату и микросекунды
                            date_part, fractional_part = genesis_time_iso.split('.')
                            
                            # Разделяем микросекунды и временную зону
                            if '+' in fractional_part:
                                fractional_seconds, timezone = fractional_part.split('+')
                                timezone = '+' + timezone
                            elif '-' in fractional_part:
                                fractional_seconds, timezone = fractional_part.split('-')
                                timezone = '-' + timezone
                            else:
                                fractional_seconds = fractional_part
                                timezone = ''
                            
                            # Обрезаем микросекунды до 6 знаков
                            fractional_seconds = fractional_seconds[:6]
                            
                            # Собираем корректную строку даты
                            genesis_time_iso = f"{date_part}.{fractional_seconds}{timezone}"
                        
                        # Теперь можно безопасно использовать fromisoformat
                        genesis_time = datetime.datetime.fromisoformat(genesis_time_iso)
                        formatted_time = genesis_time.strftime('%Y-%m-%d %H:%M:%S UTC')
                    except Exception as e:
                        formatted_time = genesis_time_iso  # Если не удалось преобразовать, оставляем как есть
                        logger.warning(f"Unable to parse genesis_time: {genesis_time_iso} - {e}")
                    
                    # Инициализируем embed перед добавлением полей
                    embed = discord.Embed(title="Genesis Information", color=discord.Color.green())
                    embed.add_field(name="Genesis Time", value=formatted_time, inline=False)
                    
                    chain_id = genesis.get('chain_id', 'N/A')
                    initial_height = genesis.get('initial_height', 'N/A')
                    app_hash = genesis.get('app_hash', 'N/A')
                    
                    embed.add_field(name="Chain ID", value=chain_id, inline=False)
                    embed.add_field(name="Initial Height", value=initial_height, inline=False)
                    embed.add_field(name="App Hash", value=app_hash, inline=False)
                    
                    return embed
                else:
                    logger.error(f"Failed to fetch Genesis: HTTP {response.status}")
                    return None
    except Exception as e:
        logger.error(f"Error fetching Genesis: {e}")
        return None

async def fetch_params(url, title):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    embed = discord.Embed(title=title, color=discord.Color.green())
                    params = data.get('params', data)
                    for key, value in params.items():
                        # Форматируем числа с плавающей точкой
                        try:
                            if '.' in value:
                                value = float(value)
                                value_str = f"{value:.2f}"
                            else:
                                value_str = value
                        except (ValueError, TypeError):
                            value_str = str(value)
                        if len(value_str) > 1024:
                            value_str = value_str[:1021] + '...'
                        embed.add_field(name=key, value=value_str, inline=False)
                    return embed
                else:
                    logger.error(f"Failed to fetch {title}: {response.status}")
                    return None
    except Exception as e:
        logger.error(f"Error fetching {title}: {e}")
        return None
