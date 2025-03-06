# utils/embeds.py

import discord
import logging
from utils.cache import validator_cache
from utils.cache import selected_validators

logger = logging.getLogger(__name__)

def create_validator_embed(validator):
    try:
        validator_data = validator.get('validator', {})
        if not validator_data:
            raise KeyError("Validator data is empty")

        description = validator_data.get('description', {})
        commission = validator_data.get('commission', {}).get('commission_rates', {})

        jailed = "Yes" if validator_data.get('jailed', False) else "No"

        tokens = int(validator_data.get('tokens', '0'))
        delegator_shares = float(validator_data.get('delegator_shares', '0'))
        commission_rate = float(commission.get('rate', '0'))
        max_commission_rate = float(commission.get('max_rate', '0'))
        max_change_rate = float(commission.get('max_change_rate', '0'))

        embed = discord.Embed(
            title=f"Validator {description.get('moniker', 'Unknown')}",
            color=discord.Color.orange()
        )
        embed.add_field(name="Address", value=validator_data.get('operator_address', 'N/A'), inline=False)
        embed.add_field(name="Status", value=validator_data.get('status', 'N/A'), inline=False)
        embed.add_field(name="Jailed", value=jailed, inline=False)
        embed.add_field(name="Tokens", value=f"{tokens}", inline=False)
        embed.add_field(name="Delegator Shares", value=f"{delegator_shares:.2f}", inline=False)
        embed.add_field(name="Commission Rate", value=f"{commission_rate * 100:.2f}%", inline=False)
        embed.add_field(name="Max Commission Rate", value=f"{max_commission_rate * 100:.2f}%", inline=False)
        embed.add_field(name="Max Change Rate", value=f"{max_change_rate * 100:.2f}%", inline=False)
        embed.add_field(name="Website", value=description.get('website', 'N/A'), inline=False)
        embed.add_field(name="Details", value=description.get('details', 'N/A'), inline=False)

        # Добавляем аптайм
        operator_address = validator_data.get('operator_address')
        cached_validator = validator_cache["data"].get(operator_address)
        if cached_validator:
            uptime = cached_validator.get('uptime', 0.0)
            embed.add_field(name="Uptime", value=f"{uptime:.2f}%", inline=False)
        else:
            embed.add_field(name="Uptime", value="N/A", inline=False)

        embed.set_footer(text="Powered by Stake-Take")
        return embed
    except KeyError as e:
        logger.error(f"KeyError: {e}, data: {validator}")
        return None

def create_validator_list_embed(validators):
    embed = discord.Embed(title="Validator List", color=discord.Color.orange())
    for validator in validators:
        address = validator['operator_address']
        embed.add_field(name="Validator Address", value=f"{address}", inline=False)
    embed.set_footer(text="Powered by Stake-Take")
    return embed
