import base64
import hashlib
import bech32
import logging
import binascii
from Crypto.Hash import RIPEMD160  # Из библиотеки pycryptodome

# Инициализация логирования
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Функция для конвертации в bech32
def bech32_encode(data, prefix):
    return bech32.bech32_encode(prefix, bech32.convertbits(data, 8, 5))

# Варианты хеширования
def sha256_hash(data):
    return hashlib.sha256(data).digest()

def ripemd160_hash(data):
    h = RIPEMD160.new()
    h.update(data)
    return h.digest()

def sha256_then_ripemd160(data):
    sha256_result = hashlib.sha256(data).digest()
    return ripemd160_hash(sha256_result)

# Пробуем различные комбинации хеширования
def generate_possible_addresses(pubkey_raw):
    possible_addresses = []

    # Пробуем разные хеши
    sha256_digest = sha256_hash(pubkey_raw)
    ripemd160_digest = ripemd160_hash(pubkey_raw)
    sha256_then_ripemd160_digest = sha256_then_ripemd160(pubkey_raw)

    # Используем первые 20 байт как часть адреса
    sha256_20 = sha256_digest[:20]
    ripemd160_20 = ripemd160_digest[:20]
    sha256_then_ripemd160_20 = sha256_then_ripemd160_digest[:20]

    # Пробуем разные префиксы bech32
    for prefix in ["storyvalcons", "cosmosvalcons", "cosmos", "story"]:
        possible_addresses.append(bech32_encode(sha256_20, prefix))
        possible_addresses.append(bech32_encode(ripemd160_20, prefix))
        possible_addresses.append(bech32_encode(sha256_then_ripemd160_20, prefix))

    return possible_addresses

def convert_pubkey_to_address(pubkey_base64):
    try:
        logger.info(f"Публичный ключ (Base64): {pubkey_base64}")
        pubkey_raw = base64.b64decode(pubkey_base64)
        logger.info(f"Декодированный публичный ключ (Raw): {pubkey_raw.hex()}")

        # Генерация всех возможных вариантов адресов
        possible_addresses = generate_possible_addresses(pubkey_raw)

        # Вывод всех сгенерированных адресов
        for address in possible_addresses:
            logger.info(f"Возможный адрес: {address}")

    except Exception as e:
        logger.error(f"Ошибка при конвертации публичного ключа в адрес: {e}")

# Тестируем с конкретным публичным ключом
pubkey = ""
convert_pubkey_to_address(pubkey)
