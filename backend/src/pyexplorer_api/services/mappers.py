"""Network response normalization helpers."""

from collections.abc import Iterable
from datetime import UTC, datetime
from math import isfinite
from typing import Any

from pyexplorer_api.core.constants import SATOSHI


def parse_timestamp(source: dict[str, Any], fields: Iterable[str]) -> datetime | None:
    for field in fields:
        value = source.get(field)
        if value is None:
            continue
        try:
            return datetime.fromtimestamp(int(float(value)), tz=UTC)
        except (TypeError, ValueError, OverflowError):
            continue
    return None


def to_int(value: Any) -> int:
    """Normalize an upstream integer into the non-negative API domain."""
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return 0
    if not isfinite(numeric) or numeric <= 0:
        return 0
    try:
        return int(numeric)
    except (OverflowError, ValueError):
        return 0


def to_float(value: Any) -> float:
    """Normalize an upstream float into the non-negative API domain."""
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return 0.0
    if not isfinite(numeric) or numeric <= 0:
        return 0.0
    return numeric


def coerce_satoshis(value: Any) -> int:
    if value is None:
        return 0

    is_btc_string = False
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return 0
        try:
            numeric = float(stripped)
        except ValueError:
            return 0
        is_btc_string = "." in stripped
    elif isinstance(value, int | float):
        numeric = float(value)
    else:
        return 0

    if not isfinite(numeric) or numeric <= 0:
        return 0

    try:
        if is_btc_string or numeric < 1:
            return int(numeric * SATOSHI)
        return int(numeric)
    except (OverflowError, ValueError):
        return 0


def extract_satoshis(source: dict[str, Any], keys: Iterable[str]) -> int:
    for key in keys:
        if key not in source:
            continue
        satoshis = coerce_satoshis(source.get(key))
        if satoshis:
            return satoshis
    return 0


def extract_address(entry: dict[str, Any]) -> str:
    addresses = entry.get("addresses")
    if isinstance(addresses, list) and addresses:
        return str(addresses[0])
    if isinstance(addresses, str) and addresses:
        return addresses

    prev_out = entry.get("prevOut") or entry.get("prev_out")
    if isinstance(prev_out, dict):
        prev_addresses = prev_out.get("addresses")
        if isinstance(prev_addresses, list) and prev_addresses:
            return str(prev_addresses[0])
        if isinstance(prev_addresses, str) and prev_addresses:
            return prev_addresses
        for key in ("address", "addr"):
            candidate = prev_out.get(key)
            if isinstance(candidate, str) and candidate:
                return candidate

    for key in ("address", "addr"):
        candidate = entry.get(key)
        if isinstance(candidate, str) and candidate:
            return candidate

    if entry.get("coinbase") is not None:
        return "Coinbase"
    return "Unknown"


def _transaction_inputs(raw: dict[str, Any]) -> list[dict[str, Any]]:
    items = raw.get("vin") or raw.get("inputs") or []
    return items if isinstance(items, list) else []


def _transaction_outputs(raw: dict[str, Any]) -> list[dict[str, Any]]:
    items = raw.get("vout") or raw.get("out") or []
    return items if isinstance(items, list) else []


def _entry_satoshis(entry: dict[str, Any]) -> int:
    nested = entry.get("prev_out") or entry.get("prevOut")
    if isinstance(nested, dict):
        value = extract_satoshis(nested, ("valueSat", "value"))
        if value:
            return value
    return extract_satoshis(entry, ("valueSat", "value"))


def normalise_transaction(raw: dict[str, Any]) -> dict[str, Any]:
    raw_inputs = _transaction_inputs(raw)
    raw_outputs = _transaction_outputs(raw)

    inputs = [
        {"address": extract_address(item), "value_btc": _entry_satoshis(item) / SATOSHI}
        for item in raw_inputs
        if isinstance(item, dict)
    ]
    outputs = [
        {
            "address": extract_address(item),
            "value_btc": extract_satoshis(item, ("valueSat", "value")) / SATOSHI,
        }
        for item in raw_outputs
        if isinstance(item, dict)
    ]

    total_input_sat = sum(_entry_satoshis(item) for item in raw_inputs if isinstance(item, dict))
    total_output_sat = sum(
        extract_satoshis(item, ("valueSat", "value"))
        for item in raw_outputs
        if isinstance(item, dict)
    )
    fee_sat = extract_satoshis(raw, ("fees", "fee"))
    if fee_sat == 0 and total_input_sat and total_output_sat:
        fee_sat = max(total_input_sat - total_output_sat, 0)
    value_sat = extract_satoshis(raw, ("valueSat", "value")) or total_output_sat

    return {
        "hash": raw.get("txid") or raw.get("hash", ""),
        "time": parse_timestamp(
            raw, ("blockTime", "time", "blocktime", "receivedTime", "timestamp")
        ) or datetime.fromtimestamp(0, tz=UTC),
        "block_height": to_int(raw.get("blockHeight") or raw.get("blockheight") or raw.get("block_height")),
        "confirmations": to_int(raw.get("confirmations")),
        "size": to_int(raw.get("size") or raw.get("vsize")),
        "value_btc": value_sat / SATOSHI,
        "fee_btc": fee_sat / SATOSHI,
        "inputs": inputs,
        "outputs": outputs,
    }
