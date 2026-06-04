"""Provider response normalization helpers."""

from collections.abc import Iterable
from datetime import UTC, datetime
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
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def to_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def coerce_satoshis(value: Any) -> int:
    if value is None:
        return 0
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return 0
        try:
            numeric = float(stripped)
        except ValueError:
            return 0
        if "." in stripped:
            return int(numeric * SATOSHI)
        return int(numeric)
    if isinstance(value, int | float):
        numeric = float(value)
        if numeric < 0:
            return 0
        if 0 < numeric < 1:
            return int(numeric * SATOSHI)
        return int(numeric)
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


def normalise_transaction(raw: dict[str, Any]) -> dict[str, Any]:
    inputs = [
        {
            "address": extract_address(vin),
            "value_btc": extract_satoshis(vin, ("valueSat", "value")) / SATOSHI,
        }
        for vin in raw.get("vin", []) or []
    ]
    outputs = [
        {
            "address": extract_address(vout),
            "value_btc": extract_satoshis(vout, ("valueSat", "value")) / SATOSHI,
        }
        for vout in raw.get("vout", []) or []
    ]

    total_input_sat = sum(
        extract_satoshis(vin, ("valueSat", "value")) for vin in raw.get("vin", []) or []
    )
    total_output_sat = sum(
        extract_satoshis(vout, ("valueSat", "value"))
        for vout in raw.get("vout", []) or []
    )
    fee_sat = extract_satoshis(raw, ("fees", "fee"))
    if fee_sat == 0 and total_input_sat and total_output_sat:
        fee_sat = max(total_input_sat - total_output_sat, 0)
    value_sat = extract_satoshis(raw, ("valueSat", "value")) or total_output_sat

    return {
        "hash": raw.get("txid") or raw.get("hash", ""),
        "time": parse_timestamp(
            raw, ("blockTime", "time", "blocktime", "receivedTime", "timestamp")
        )
        or datetime.fromtimestamp(0, tz=UTC),
        "block_height": to_int(raw.get("blockHeight") or raw.get("blockheight")),
        "confirmations": to_int(raw.get("confirmations")),
        "size": to_int(raw.get("size") or raw.get("vsize")),
        "value_btc": value_sat / SATOSHI,
        "fee_btc": fee_sat / SATOSHI,
        "inputs": inputs,
        "outputs": outputs,
    }
