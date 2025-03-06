# cogs/validators.py

import asyncio
import os
import discord
import logging
from dotenv import load_dotenv
from discord.ext import commands
from discord.ui import View, Button
from buttons.validator_information import get_validator_information
from buttons.validator_list import handle_validator_list
from discord import app_commands
from utils.cache import selected_validators
from buttons.blockchain_params import (
    fetch_staking_params,
    fetch_slashing_params,
    fetch_inflation,
    fetch_mint_params,
    fetch_genesis
)
from buttons.validator_services import (
    get_snapshot_info,
    get_state_sync_info,
    get_fresh_addrbook_info,
    get_live_peers_info,
    get_useful_links,
    get_useful_commands
)
from buttons.validator_information import get_validator_information

load_dotenv()
GUILD_ID = int(os.getenv('GUILD_ID'))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ValidatorsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    @app_commands.command(name="start", description="Starts the bot menu.")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def start(self, interaction: discord.Interaction):
        """Starts the bot menu."""
        embed = discord.Embed(
        title="Main Menu",
        description="Choose one of the options below to interact with the validator.",
        color=discord.Color.orange()
        )
        embed.add_field(name="Validators Menu", value="Menu for working with validators", inline=False)
        embed.add_field(name="Blockchain Params", value="View blockchain parameters", inline=False)
        embed.add_field(name="Validator Services", value="Tools for managing validator services", inline=False)
        embed.add_field(name="Info", value="General information about the bot and its features", inline=False)
        embed.set_thumbnail(url="https://logowik.com/content/uploads/images/story-protocol8889.logowik.com.webp")  # Используем миниатюру
        embed.set_footer(text="Built by Stake-Take")

        view = MainMenu()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type == discord.InteractionType.component:
            custom_id = interaction.data['custom_id']
            if custom_id == "validators_menu":
                await self.show_validators_menu(interaction)
            elif custom_id == "info":
                await self.show_info(interaction)
            elif custom_id == "validator_list":
                await handle_validator_list(interaction)
            elif custom_id == "validator_information":
                await self.show_validator_info_modal(interaction)
            elif custom_id == "select_validator":
                await self.show_select_validator_modal(interaction)
            elif custom_id == "check_selected_validator":
                await self.check_selected_validator(interaction)
            elif custom_id == "validator_services":
                await self.show_validator_services_menu(interaction)
            elif custom_id == "snapshot":
                await self.show_snapshot_info(interaction)
            elif custom_id == "state_sync":
                await self.show_state_sync_info(interaction)
            elif custom_id == "fresh_addrbook":
                await self.show_addrbook_info(interaction)
            elif custom_id == "live_peers":
                await self.show_live_peers_info(interaction)
            elif custom_id == "useful_links":
                await self.show_useful_links(interaction)
            elif custom_id == "useful_commands":
                await self.show_useful_commands(interaction)
            elif custom_id == "blockchain_params":
                await self.show_blockchain_params_menu(interaction)
            elif custom_id == "staking_params":
                await self.send_staking_params(interaction)
            elif custom_id == "slashing_params":
                await self.send_slashing_params(interaction)
            elif custom_id == "inflation":
                await self.send_inflation(interaction)
            elif custom_id == "genesis":
                await self.send_genesis(interaction)
            elif custom_id == "mint_params":
                await self.send_mint_params(interaction)
            elif custom_id == "back":
                await self.show_main_menu(interaction)
            elif custom_id == "exit":
                try:
                    await interaction.message.delete()
                except discord.errors.NotFound:
                    pass
                await interaction.response.send_message("Menu closed.", ephemeral=True)

    async def show_main_menu(self, interaction):
        embed = discord.Embed(
        title="Main Menu",
        description="Choose one of the options below to interact with the validator.",
        color=discord.Color.orange()
        )
        embed.add_field(name="Validators Menu", value="Menu for working with validators", inline=False)
        embed.add_field(name="Blockchain Params", value="View blockchain parameters", inline=False)
        embed.add_field(name="Validator Services", value="Tools for managing validator services", inline=False)
        embed.add_field(name="Info", value="General information about the bot and its features", inline=False)
        embed.set_footer(text="Built by Stake-Take")

        view = MainMenu()
        await interaction.response.edit_message(embed=embed, view=view)
    
    async def show_validator_services_menu(self, interaction):
        embed = discord.Embed(
            title="Validator Services",
            description="Choose an option to manage validator services",
            color=discord.Color.orange()
        )
        embed.add_field(name="Snapshot", value="View and restore from a snapshot", inline=False)
        embed.add_field(name="State Sync", value="Synchronize with the network using state sync", inline=False)
        embed.add_field(name="Fresh Addrbook", value="Access the fresh address book", inline=False)
        embed.add_field(name="Live Peers", value="Check current live peers", inline=False)
        embed.add_field(name="Useful Links", value="Access useful blockchain-related links", inline=False)  # Новое поле для Useful Links
        embed.add_field(name="Useful Commands", value="View useful commands for managing validators", inline=False)  # Новое поле для Useful Commands
        embed.set_footer(text="Powered by Stake-Take")

        view = ValidatorServicesMenu()
        await interaction.response.edit_message(embed=embed, view=view)
    
    async def show_info(self, interaction):
        embed = discord.Embed(
            title="ℹ️ Bot Information",
            description=(
                "This bot provides various tools and information for the **Story Protocol** network.\n\n"
                "**Features include:**\n"
                "- 📜 Viewing validator information and uptime\n"
                "- 🚨 Monitoring validators and receiving alerts\n"
                "- 🔧 Accessing blockchain parameters\n"
                "- 🛠️ Getting instructions for validator services\n"
                "- 💡 And more!\n\n"
            ),
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url="https://pbs.twimg.com/profile_images/1820303986349805569/MKfPfLtz_400x400.jpg")  # Логотип Story Protocol
        embed.set_footer(text="Built by Stake-Take")

        # Передаём экземпляр MainMenu() вместо self
        view = MainMenu()
        await interaction.response.edit_message(embed=embed, view=view)

    async def show_validators_menu(self, interaction):
        embed = discord.Embed(
            title="Validators Menu",
            description="Choose an option to interact with validators",
            color=discord.Color.orange()
        )
        embed.add_field(name="Validator List", value="View the list of validators and their status", inline=False)
        embed.add_field(name="Validator Information", value="Get detailed information about a specific validator", inline=False)
        embed.add_field(name="Select Validator", value="Select a validator to follow", inline=False)
        embed.add_field(name="Check Selected Validator", value="View information on the validator you're following", inline=False)
        embed.set_footer(text="Powered by Stake-Take")
    
        view = ValidatorsMenu()
        await interaction.response.edit_message(embed=embed, view=view)

    
    async def show_blockchain_params_menu(self, interaction):
        embed = discord.Embed(
            title="Blockchain Params",
            description="Choose an option to view blockchain parameters",
            color=discord.Color.orange()
        )
        embed.add_field(name="Staking Params", value="View current staking parameters", inline=False)
        embed.add_field(name="Slashing Params", value="View slashing parameters", inline=False)
        embed.add_field(name="Inflation", value="View inflation parameters", inline=False)
        embed.add_field(name="Mint Params", value="View minting parameters", inline=False)
        embed.add_field(name="Genesis", value="View the genesis block information", inline=False)
        embed.set_footer(text="Powered by Stake-Take")

        view = BlockchainParamsMenu()
        await interaction.response.edit_message(embed=embed, view=view)

    async def send_staking_params(self, interaction):
        embed = await fetch_staking_params()
        if embed:
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message("Failed to fetch staking params.", ephemeral=True)

    async def send_slashing_params(self, interaction):
        embed = await fetch_slashing_params()
        if embed:
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message("Failed to fetch slashing params.", ephemeral=True)

    async def send_inflation(self, interaction):
        embed = await fetch_inflation()
        if embed:
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message("Failed to fetch inflation data.", ephemeral=True)

    async def send_mint_params(self, interaction):
        embed = await fetch_mint_params()
        if embed:
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message("Failed to fetch mint params.", ephemeral=True)

    async def send_genesis(self, interaction):
        embed = await fetch_genesis()
        if embed:
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message("Failed to fetch genesis data.", ephemeral=True)

    async def show_validator_info_modal(self, interaction):
        modal = ValidatorInfoModal()
        await interaction.response.send_modal(modal)

    async def show_select_validator_modal(self, interaction):
        modal = SelectValidatorModal()
        await interaction.response.send_modal(modal)
    
    async def show_snapshot_info(self, interaction):
        embed = await get_snapshot_info()
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def show_state_sync_info(self, interaction):
        embed = await get_state_sync_info()
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def show_addrbook_info(self, interaction):
        embed = await get_fresh_addrbook_info()
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def show_live_peers_info(self, interaction):
        embed = await get_live_peers_info()
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def show_useful_links(self, interaction):
        embed = await get_useful_links()
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def show_useful_commands(self, interaction):
        embed = await get_useful_commands()
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def check_selected_validator(self, interaction):
        user_id = interaction.user.id
        if user_id in selected_validators:
            validator_address = selected_validators[user_id]
            embed = await get_validator_information(validator_address)
            if embed:
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(f"Validator {validator_address} not found.", ephemeral=True)
        else:
            await interaction.response.send_message("You have not selected a validator. Use the select_validator command first.", ephemeral=True)

class MainMenu(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(Button(label="Validators Menu", style=discord.ButtonStyle.blurple, custom_id="validators_menu", emoji="📋"))
        self.add_item(Button(label="Blockchain Params", style=discord.ButtonStyle.green, custom_id="blockchain_params", emoji="🔧"))
        self.add_item(Button(label="Validator Services", style=discord.ButtonStyle.grey, custom_id="validator_services", emoji="🛠️"))
        self.add_item(Button(label="Info", style=discord.ButtonStyle.secondary, custom_id="info", emoji="ℹ️"))
        self.add_item(Button(label="Exit", style=discord.ButtonStyle.red, custom_id="exit", emoji="❌"))

class ValidatorsMenu(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(Button(label="Validator List", style=discord.ButtonStyle.primary, custom_id="validator_list", emoji="📜"))
        self.add_item(Button(label="Validator Information", style=discord.ButtonStyle.primary, custom_id="validator_information", emoji="ℹ️"))
        self.add_item(Button(label="Select Validator", style=discord.ButtonStyle.primary, custom_id="select_validator", emoji="✅"))
        self.add_item(Button(label="Check Selected Validator", style=discord.ButtonStyle.primary, custom_id="check_selected_validator", emoji="🔍"))
        self.add_item(Button(label="Back", style=discord.ButtonStyle.secondary, custom_id="back", emoji="⬅️"))
        self.add_item(Button(label="Exit", style=discord.ButtonStyle.danger, custom_id="exit", emoji="❌"))

class ValidatorServicesMenu(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(Button(label="Snapshot", style=discord.ButtonStyle.primary, custom_id="snapshot", emoji="📸"))
        self.add_item(Button(label="State Sync", style=discord.ButtonStyle.primary, custom_id="state_sync", emoji="🔄"))
        self.add_item(Button(label="Fresh Addrbook", style=discord.ButtonStyle.primary, custom_id="fresh_addrbook", emoji="📖"))
        self.add_item(Button(label="Live Peers", style=discord.ButtonStyle.primary, custom_id="live_peers", emoji="🌐"))
        self.add_item(Button(label="Useful Links", style=discord.ButtonStyle.primary, custom_id="useful_links", emoji="🔗"))
        self.add_item(Button(label="Useful Commands", style=discord.ButtonStyle.primary, custom_id="useful_commands", emoji="💡"))
        self.add_item(Button(label="Back", style=discord.ButtonStyle.secondary, custom_id="back", emoji="⬅️"))
        self.add_item(Button(label="Exit", style=discord.ButtonStyle.danger, custom_id="exit", emoji="❌"))
    
class BlockchainParamsMenu(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(Button(label="Staking Params", style=discord.ButtonStyle.primary, custom_id="staking_params", emoji="📈"))
        self.add_item(Button(label="Slashing Params", style=discord.ButtonStyle.primary, custom_id="slashing_params", emoji="⚔️"))
        self.add_item(Button(label="Inflation", style=discord.ButtonStyle.primary, custom_id="inflation", emoji="📊"))
        self.add_item(Button(label="Mint Params", style=discord.ButtonStyle.primary, custom_id="mint_params", emoji="💰"))
        self.add_item(Button(label="Genesis", style=discord.ButtonStyle.primary, custom_id="genesis", emoji="🌟"))
        self.add_item(Button(label="Back", style=discord.ButtonStyle.secondary, custom_id="back", emoji="⬅️"))
        self.add_item(Button(label="Exit", style=discord.ButtonStyle.danger, custom_id="exit", emoji="❌"))

class ValidatorInfoModal(discord.ui.Modal, title="Enter Validator Address"):
    validator_address = discord.ui.TextInput(label="Validator Address", placeholder="storyvaloper1...")

    async def on_submit(self, interaction: discord.Interaction):
        embed = await get_validator_information(self.validator_address.value)
        if embed:
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message("Validator not found.", ephemeral=True)

class SelectValidatorModal(discord.ui.Modal, title="Select Validator"):
    validator_address = discord.ui.TextInput(label="Validator Address", placeholder="storyvaloper1...")

    async def on_submit(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        operator_address = self.validator_address.value.strip().lower()
        selected_validators[user_id] = operator_address
        logger.info(f"User {user_id} selected validator {operator_address}")
        await interaction.response.send_message(f"You are now following validator {operator_address}.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ValidatorsCog(bot))
