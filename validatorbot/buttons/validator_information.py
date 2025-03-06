# buttons/validator_information.py

import discord
import logging
from utils.api import fetch_validator_info
from utils.embeds import create_validator_embed
from utils.cache import validator_cache
from utils.cache import selected_validators

logger = logging.getLogger(__name__)

async def get_validator_information(validator_address: str):
    try:
        data = await fetch_validator_info(validator_address)
        if data:
            embed = create_validator_embed(data)
            return embed
        else:
            return None
    except Exception as e:
        logger.error(f"Error fetching validator information: {e}")
        return None
