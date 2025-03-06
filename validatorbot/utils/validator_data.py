import asyncio
import aiohttp
import base64
import hashlib
import logging
import os
from Crypto.Hash import RIPEMD160
import bech32
from dotenv import load_dotenv
from utils.cache import validator_cache
from utils.cache import selected_validators

load_dotenv()
logger = logging.getLogger(__name__)

COSMOS_API_URL = os.getenv("COSMOS_API_URL")
COSMOS_RESERVE_API_URL = os.getenv("COSMOS_RESERVE_API_URL")

async def fetch_validators(session, api_url):
    """Получение списка валидаторов."""
    validators = []
    next_key = None
    while True:
        params = {'pagination.limit': '20000'}
        if next_key:
            params['pagination.key'] = next_key
        url = f"{api_url}/cosmos/staking/v1beta1/validators"
        async with session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                validators.extend(data.get('validators', []))
                next_key = data.get('pagination', {}).get('next_key')
                if not next_key:
                    break
            else:
                logger.error(f"Ошибка при получении валидаторов: {response.status}")
                return []
    return validators

async def fetch_all_signing_infos(session, api_url):
    """Получение всех signing_infos с учётом пагинации."""
    signing_infos = []
    next_key = None
    while True:
        params = {'pagination.limit': '2000'}
        if next_key:
            params['pagination.key'] = next_key
        url = f"{api_url}/cosmos/slashing/v1beta1/signing_infos"
        async with session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                signing_infos.extend(data.get('info', []))
                next_key = data.get('pagination', {}).get('next_key')
                if not next_key:
                    break
            else:
                logger.error(f"Ошибка при получении signing_infos: {response.status}")
                return []
    return signing_infos

def convert_pubkey_to_address(pubkey_base64):
    try:
        pubkey_bytes = base64.b64decode(pubkey_base64)
        sha256_digest = hashlib.sha256(pubkey_bytes).digest()
        ripemd160 = RIPEMD160.new()
        ripemd160.update(sha256_digest)
        ripemd160_digest = ripemd160.digest()
        # Префикс меняется в зависимости от вашей сети (например, "cosmosvalcons")
        bech32_address = bech32.bech32_encode("storyvalcons", bech32.convertbits(ripemd160_digest, 8, 5))
        return bech32_address
    except Exception as e:
        logger.error(f"Ошибка при конвертации публичного ключа в адрес: {e}")
        return None

async def get_window_size(session, api_url):
    url = f"{api_url}/cosmos/slashing/v1beta1/params"
    async with session.get(url) as response:
        if response.status == 200:
            data = await response.json()
            window_size = int(data['params']['signed_blocks_window'])
            return window_size
        else:
            logger.error(f"Failed to fetch slashing params: {response.status}")
            return None

async def get_validator_uptimes():
    """Функция для обновления данных валидаторов и аптайма."""
    try:
        current_api_url = COSMOS_API_URL
        main_api_available = await check_api_availability(COSMOS_API_URL)

        if not main_api_available:
            logger.info(f"Switching to reserve API URL: {COSMOS_RESERVE_API_URL}")
            current_api_url = COSMOS_RESERVE_API_URL

        async with aiohttp.ClientSession() as session:
            validators = await fetch_validators(session, current_api_url)
            if not validators:
                return

            # Инициализируем словарь для данных валидаторов
            validator_data = {}
            summary = {
                "total": len(validators),
                "active": 0,
                "inactive": 0,
                "jailed": 0
            }

            # Получаем signing_infos только для активных валидаторов
            active_validators = [v for v in validators if v.get("status") == "BOND_STATUS_BONDED" and not v.get("jailed", False)]
            summary["active"] = len(active_validators)
            summary["inactive"] = len(validators) - len(active_validators)

            signing_infos = await fetch_all_signing_infos(session, current_api_url)
            if not signing_infos:
                return

            signing_info_dict = {info['address']: info for info in signing_infos}
            window_size = await get_window_size(session, current_api_url)

            for validator in validators:
                operator_address = validator.get("operator_address")
                moniker = validator.get("description", {}).get("moniker", "Unknown")
                status = validator.get("status")
                jailed = validator.get("jailed", False)
                commission = float(validator.get("commission", {}).get("commission_rates", {}).get("rate", 0))
                consensus_pubkey = validator.get("consensus_pubkey", {}).get("key")

                if jailed:
                    summary["jailed"] += 1

                uptime_percent = 0.0  # По умолчанию аптайм 0%

                # Если валидатор активен, вычисляем аптайм
                if status == "BOND_STATUS_BONDED" and not jailed:
                    consensus_address = convert_pubkey_to_address(consensus_pubkey)
                    if not consensus_address:
                        logger.error(f"Не удалось конвертировать публичный ключ валидатора {moniker}")
                        continue

                    signing_info = signing_info_dict.get(consensus_address)
                    if not signing_info:
                        logger.error(f"Не найден signing_info для валидатора {moniker} с адресом {consensus_address}")
                        continue

                    missed_blocks = int(signing_info.get("missed_blocks_counter", 0))
                    uptime_percent = round((1 - missed_blocks / window_size) * 100, 2)

                validator_data[operator_address] = {
                    'moniker': moniker,
                    'uptime': uptime_percent,
                    'status': status,
                    'jailed': jailed,
                    'commission': commission
                }

            validator_cache["data"] = validator_data
            validator_cache["summary"] = summary
            validator_cache["last_updated"] = asyncio.get_event_loop().time()
            logger.info("Validator cache updated successfully.")
    except Exception as e:
        logger.error(f"Error updating validator data: {e}")

async def check_api_availability(api_url):
    """Проверка доступности API."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as response:
                return response.status == 200
    except Exception:
        return False