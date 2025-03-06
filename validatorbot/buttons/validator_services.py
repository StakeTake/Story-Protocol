# buttons/validator_services.py

import discord
import aiohttp
import random
from utils.cache import selected_validators

async def get_state_sync_info():
    """Returns an embed with State Sync instructions."""
    embed = discord.Embed(
        title="State Sync",
        description=(
            "State Sync enables a new node to quickly join the network by downloading a recent snapshot of the application's state, "
            "instead of fetching and replaying all historical blocks. This significantly reduces the synchronization time from days to minutes."
        ),
        color=discord.Color.green()
    )

    # Step 1: Stop the service and reset the data
    embed.add_field(
        name="1. Stop the service and reset the data",
        value=(
            "```bash\n"
            "sudo systemctl stop story\n"
            "cp $HOME/.story/story/data/priv_validator_state.json $HOME/.story/story/priv_validator_state.json.backup\n"
            "rm -rf $HOME/.story/story/data\n"
            "mkdir -p $HOME/.story/story/data\n"
            "```"
        ),
        inline=False
    )

    # Step 2: Get and configure the state sync information
    embed.add_field(
        name="2. Get and configure the state sync information",
        value=(
            "```bash\n"
            "STATE_SYNC_RPC=https://story-testnet-rpc.stake-take.com:443\n"
            "LATEST_HEIGHT=$(curl -s $STATE_SYNC_RPC/block | jq -r .result.block.header.height)\n"
            "SYNC_BLOCK_HEIGHT=$(echo \"$LATEST_HEIGHT\" | awk '{printf \"%d000\\n\", $0 / 1000}')\n"
            "SYNC_BLOCK_HASH=$(curl -s \"$STATE_SYNC_RPC/block?height=$SYNC_BLOCK_HEIGHT\" | jq -r .result.block_id.hash)\n"
            "\n"
            "echo $LATEST_HEIGHT $SYNC_BLOCK_HEIGHT $SYNC_BLOCK_HASH && sleep 1\n"
            "\n"
            "sed -i \\\n"
            "  -e \"s|^enable *=.*|enable = true|\" \\\n"
            "  -e \"s|^rpc_servers *=.*|rpc_servers = \\\"$STATE_SYNC_RPC,$STATE_SYNC_RPC\\\"|\" \\\n"
            "  -e \"s|^trust_height *=.*|trust_height = $SYNC_BLOCK_HEIGHT|\" \\\n"
            "  -e \"s|^trust_hash *=.*|trust_hash = \\\"$SYNC_BLOCK_HASH\\\"|\" \\\n"
            "  -e \"s|^persistent_peers *=.*|persistent_peers = \\\"$STATE_SYNC_PEER\\\"|\" \\\n"
            "  $HOME/.story/story/config/config.toml\n"
            "\n"
            "mv $HOME/.story/story/priv_validator_state.json.backup $HOME/.story/story/data/priv_validator_state.json\n"
            "```"
        ),
        inline=False
    )

    # Step 3: Restart the service and check the log
    embed.add_field(
        name="3. Restart the service and check the log",
        value=(
            "```bash\n"
            "sudo systemctl start story && sudo journalctl -fu story -o cat\n"
            "```"
        ),
        inline=False
    )

    return embed

async def get_snapshot_info():
    """Returns an embed with Snapshot instructions."""
    embed = discord.Embed(
        title="Snapshots",
        description="Instructions to update your node using snapshots.",
        color=discord.Color.green()
    )

    # Добавляем установку необходимых инструментов
    embed.add_field(
        name="Prerequisites",
        value=(
            "Ensure you have the following tools installed:\n"
            "- **curl**\n"
            "- **tar**\n"
            "- **lz4**\n\n"
            "If not, install them with:\n"
            "```bash\n"
            "sudo apt update\n"
            "sudo apt install curl tar lz4 -y\n"
            "```"
        ),
        inline=False
    )

    # Шаг 1: Остановите сервисы узла
    embed.add_field(
        name="1. Stop the Node Services",
        value=(
            "```bash\n"
            "sudo systemctl stop story story-geth\n"
            "```"
        ),
        inline=False
    )

    # Шаг 2: Сделайте резервную копию состояния валидатора
    embed.add_field(
        name="2. Backup Validator State",
        value=(
            "```bash\n"
            "cp $HOME/.story/story/data/priv_validator_state.json $HOME/.story/story/priv_validator_state.json.backup\n"
            "```"
        ),
        inline=False
    )

    # Шаг 3: Удалите старые данные
    embed.add_field(
        name="3. Remove Old Data",
        value=(
            "```bash\n"
            "rm -rf $HOME/.story/story/data\n"
            "rm -rf $HOME/.story/geth/iliad/geth/chaindata\n"
            "```"
        ),
        inline=False
    )

    # Шаг 4: Скачайте новые снимки с вашего сервера
    embed.add_field(
        name="4. Download New Snapshots from Your Server",
        value=(
            "```bash\n"
            "# Download and extract geth snapshot\n"
            "curl -L https://story.snapshot.stake-take.com/snapshot_geth.tar.lz4 | tar -Ilz4 -xf - -C $HOME/.story/geth\n"
            "\n"
            "# Download and extract consensus snapshot\n"
            "curl -L https://story.snapshot.stake-take.com/snapshot_consensus.tar.lz4 | tar -Ilz4 -xf - -C $HOME/.story/story\n"
            "```"
        ),
        inline=False
    )

    # Шаг 5: Восстановите состояние валидатора
    embed.add_field(
        name="5. Restore Validator State",
        value=(
            "```bash\n"
            "mv $HOME/.story/story/priv_validator_state.json.backup $HOME/.story/story/data/priv_validator_state.json\n"
            "```"
        ),
        inline=False
    )

    # Шаг 6: Перезапустите сервисы узла
    embed.add_field(
        name="6. Restart Node Services",
        value=(
            "```bash\n"
            "sudo systemctl start story story-geth\n"
            "```"
        ),
        inline=False
    )

    # Шаг 7: Проверьте логи для подтверждения успешного запуска
    embed.add_field(
        name="7. Check Logs",
        value=(
            "```bash\n"
            "sudo journalctl -fu story-geth -o cat\n"
            "sudo journalctl -fu story -o cat\n"
            "```"
        ),
        inline=False
    )

    return embed

async def get_fresh_addrbook_info():
    """Returns an embed with information on obtaining a fresh addrbook."""
    embed = discord.Embed(
        title="Fresh Addrbook",
        description="Instructions on obtaining a fresh addrbook.",
        color=discord.Color.green()
    )

    embed.add_field(
        name="Instructions",
        value=(
            "1. **Stop the node**:\n"
            "```bash\n"
            "sudo systemctl stop story\n"
            "```\n"
            "2. **Download the latest `addrbook.json`**:\n"
            "```bash\n"
            "curl -Ls https://story.snapshot.stake-take.com/addrbook.json > $HOME/.story/story/config/addrbook.json\n"
            "```\n"
            "3. **Start the node**:\n"
            "```bash\n"
            "sudo systemctl start story\n"
            "```\n"
        ),
        inline=False
    )

    return embed

async def get_live_peers_info():
    """Returns an embed with live peers information and instructions to update persistent_peers."""
    embed = discord.Embed(
        title="🌐 Live Peers",
        description="Below is a list of random live peers. Follow the instructions to update your `persistent_peers`.",
        color=discord.Color.green()
    )

    # Fetch live peers data
    try:
        peers_list = []
        async with aiohttp.ClientSession() as session:
            async with session.get('https://story-testnet-rpc.stake-take.com/net_info') as response:
                data = await response.json()
                peers = data.get('result', {}).get('peers', [])
                if not peers:
                    embed.add_field(name="No Peers Found", value="No live peers could be found at this time.", inline=False)
                else:
                    for peer in peers:
                        node_id = peer.get('node_info', {}).get('id', '')
                        remote_ip = peer.get('remote_ip', '')
                        if node_id and remote_ip:
                            peers_list.append(f"{node_id}@{remote_ip}:26656")

        if peers_list:
            # Select random 10 peers
            random_peers = random.sample(peers_list, min(10, len(peers_list)))
            peers_str = ",".join(random_peers)

            instructions = (
                f"Set the `PEERS` variable:\n"
                "```bash\n"
                f'PEERS="{peers_str}"\n'
                "```\n"
                "Then update your `config.toml` file:\n"
                "```bash\n"
                'sed -i -e "/^\\[p2p\\]/,/^\\[/{s/^[[:space:]]*persistent_peers *=.*/persistent_peers = \\"$PEERS\\"/}" $HOME/.story/story/config/config.toml\n'
                "```\n"
                "You can verify the change with:\n"
                "```bash\n"
                "sed -n '217p' $HOME/.story/story/config/config.toml\n"
                "```"
            )
            embed.add_field(name="Instructions", value=instructions, inline=False)
        else:
            embed.add_field(name="No Peers Available", value="Could not find any live peers at this time.", inline=False)

    except Exception as e:
        embed.add_field(name="Error", value="Unable to fetch live peers.", inline=False)
        print(f"Error fetching live peers: {e}")

    embed.set_footer(text="Built by Stake-Take")
    return embed

async def get_useful_links():
    """Returns an embed with useful links."""
    embed = discord.Embed(
        title="🔗 Useful Links",
        description="Here are some useful links for the Story Protocol network:",
        color=discord.Color.green()
    )

    # Добавляем новые ссылки
    embed.add_field(
        name="🌐 Story Website",
        value="[Visit the official Story Protocol website](https://www.story.foundation/)",
        inline=False
    )
    embed.add_field(
        name="🚰 Faucet",
        value="[Get testnet tokens from the Faucet](https://faucet.story.foundation/)",
        inline=False
    )
    embed.add_field(
        name="🔎 Block Explorer",
        value="[Explore blocks and transactions](https://testnet.storyscan.xyz/)",
        inline=False
    )
    embed.add_field(
        name="💰 Staking",
        value="[Stake your tokens](https://staking.story.foundation/)",
        inline=False
    )
    embed.add_field(
        name="📖 Protocol Explorer",
        value="[View protocol details](https://explorer.story.foundation/)",
        inline=False
    )
    embed.add_field(
        name="📊 Grafana Dashboard",
        value="[Monitor network metrics](https://story.stake-take.com/grafana)",
        inline=False
    )
    embed.add_field(
        name="🌍 Community Explorer",
        value="[Community Explorer on NodesGuru](https://testnet.story.explorers.guru/validators)",
        inline=False
    )

    embed.set_footer(text="Built by Stake-Take")
    return embed

async def get_useful_commands():
    """Returns an embed with validator management commands."""
    embed = discord.Embed(
        title="Useful Commands",
        description="This section will guide you through how you can run and manage your own validator.",
        color=discord.Color.green()
    )

    # Validator key export
    embed.add_field(
        name="Validator Key Export",
        value=(
            "**View your validator keys:**\n"
            "```bash\n"
            "story validator export\n"
            "```\n"
            "**Export the derived EVM private key into a .env file:**\n"
            "```bash\n"
            "story validator export --export-evm-key --evm-key-path .env\n"
            "```\n"
            "*Note: The EVM private key is highly sensitive. Store this file in a secure location.*"
        ),
        inline=False
    )

    # Validator creation
    embed.add_field(
        name="Validator Creation",
        value=(
            "Before setting up a validator, ensure your wallet is funded with testnet tokens from a faucet. "
            "Currently, you need to stake 1024 IP to create a validator.\n\n"
            "**Create a new validator:**\n"
            "```bash\n"
            "story validator create --stake ${AMOUNT_TO_STAKE_IN_WEI}\n"
            "```\n"
            "*Note: To participate in consensus, at least 1 IP must be staked (equivalent to 1,000,000,000,000,000,000 wei).*"
        ),
        inline=False
    )

    # Validator staking
    embed.add_field(
        name="Validator Staking",
        value=(
            "**Stake to an existing validator:**\n"
            "```bash\n"
            "story validator stake --validator-pubkey ${VALIDATOR_PUB_KEY_IN_BASE64} --stake ${AMOUNT_TO_STAKE_IN_WEI}\n"
            "```\n"
            "*You must stake at least 1 ETH worth (1,000,000,000,000,000,000 wei) for the transaction to be valid.*"
        ),
        inline=False
    )

    # Validator unstaking
    embed.add_field(
        name="Validator Unstaking",
        value=(
            "**Unstake from the selected validator:**\n"
            "```bash\n"
            "story validator unstake --validator-pubkey ${VALIDATOR_PUB_KEY_IN_BASE64} --unstake ${AMOUNT_TO_UNSTAKE_IN_WEI}\n"
            "```"
        ),
        inline=False
    )

    # Validator stake-on-behalf
    embed.add_field(
        name="Validator Stake-on-Behalf",
        value=(
            "**Stake on behalf of another delegator:**\n"
            "```bash\n"
            "story validator stake-on-behalf --delegator-pubkey ${DELEGATOR_PUB_KEY_IN_BASE64} "
            "--validator-pubkey ${VALIDATOR_PUB_KEY_IN_BASE64} --stake ${AMOUNT_TO_STAKE_IN_WEI}\n"
            "```"
        ),
        inline=False
    )

    # Validator unstake-on-behalf
    embed.add_field(
        name="Validator Unstake-on-Behalf",
        value=(
            "**Unstake on behalf of another delegator as an operator:**\n"
            "```bash\n"
            "story validator unstake-on-behalf --delegator-pubkey ${DELEGATOR_PUB_KEY_IN_BASE64} "
            "--validator-pubkey ${VALIDATOR_PUB_KEY_IN_BASE64} --unstake ${AMOUNT_TO_UNSTAKE_IN_WEI}\n"
            "```\n"
            "*To unstake on behalf of delegators, you must be registered as an authorized operator for that delegator.*"
        ),
        inline=False
    )

    return embed

