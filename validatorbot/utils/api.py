# utils/api.py

import aiohttp
import logging
from dotenv import load_dotenv
from utils.cache import selected_validators
import os

load_dotenv()

API_URL = os.getenv("COSMOS_API_URL")
RESERVE_API_URL = os.getenv("COSMOS_RESERVE_API_URL")

logger = logging.getLogger(__name__)

async def fetch_validator_info(validator_address):
    url = f"{API_URL}/cosmos/staking/v1beta1/validators/{validator_address}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Fetched validator info: {data}")
                    return data
                else:
                    raise Exception(f"Failed to fetch validator info: {response.status}")
    except Exception as e:
        logger.error(e)
        url = f"{RESERVE_API_URL}/cosmos/staking/v1beta1/validators/{validator_address}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Fetched validator info from reserve API: {data}")
                    return data
                else:
                    logger.error(f"Failed to fetch validator info from reserve API: {response.status}")
                    return None
