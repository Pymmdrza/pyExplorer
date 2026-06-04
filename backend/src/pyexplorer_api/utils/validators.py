"""Validation and classification helpers for Bitcoin explorer inputs."""

import re

from pyexplorer_api.exceptions import BadRequestError
from pyexplorer_api.schemas.search import QueryType

LEGACY_OR_SCRIPT_ADDRESS_RE = re.compile(r"^(1|3)[A-HJ-NP-Za-km-z1-9]{25,39}$")
BECH32_ADDRESS_RE = re.compile(r"^bc1[ac-hj-np-z02-9]{11,71}$", re.IGNORECASE)
TX_HASH_RE = re.compile(r"^[a-fA-F0-9]{64}$")
BLOCK_HEIGHT_RE = re.compile(r"^\d+$")


def is_valid_tx_hash(value: str) -> bool:
    return bool(TX_HASH_RE.fullmatch(value.strip()))


def is_valid_address(value: str) -> bool:
    candidate = value.strip()
    return bool(
        LEGACY_OR_SCRIPT_ADDRESS_RE.fullmatch(candidate)
        or BECH32_ADDRESS_RE.fullmatch(candidate)
    )


def is_valid_block_height(value: str | int) -> bool:
    return bool(BLOCK_HEIGHT_RE.fullmatch(str(value).strip()))


def classify_query(query: str) -> QueryType:
    candidate = query.strip()
    if not candidate:
        raise BadRequestError("Search query is required.")
    if is_valid_tx_hash(candidate):
        return QueryType.TRANSACTION
    if is_valid_address(candidate):
        return QueryType.ADDRESS
    if is_valid_block_height(candidate):
        return QueryType.BLOCK
    raise BadRequestError(
        "Invalid search query. Enter a valid transaction hash, Bitcoin address, or block height.",
        {"query": query},
    )


def validate_tx_hash(tx_hash: str) -> str:
    if not is_valid_tx_hash(tx_hash):
        raise BadRequestError("Invalid transaction hash.", {"tx_hash": tx_hash})
    return tx_hash.lower()


def validate_address(address: str) -> str:
    if not is_valid_address(address):
        raise BadRequestError("Invalid Bitcoin address.", {"address": address})
    return address


def validate_block_height(height: int | str) -> int:
    if not is_valid_block_height(height):
        raise BadRequestError("Invalid block height.", {"height": height})
    return int(height)
