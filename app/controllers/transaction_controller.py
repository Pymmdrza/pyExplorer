import logging
from datetime import datetime
from typing import Optional, Dict, Any, Iterable, List

from app.config.config_manager import config
from app.utils.api_client import make_request


logger = logging.getLogger(__name__)

SATOSHI = 100_000_000
PAGE_SUFFIX = '?page=1'


def get_transaction_details(tx_hash: str) -> Optional[Dict[str, Any]]:
    """Return normalized transaction information for the given hash."""
    try:
        transaction = _fetch_transaction(tx_hash)
        if not transaction:
            logger.warning("Transaction %s not found", tx_hash)
            return None

        inputs = _normalise_inputs(transaction)
        outputs = _normalise_outputs(transaction)

        total_input_sat = sum(_extract_satoshis(vin, ('valueSat', 'value')) for vin in transaction.get('vin', []))
        total_output_sat = sum(_extract_satoshis(vout, ('valueSat', 'value')) for vout in transaction.get('vout', []))

        fee_sat = _extract_satoshis(transaction, ('fees', 'fee'))
        if fee_sat == 0 and total_input_sat and total_output_sat:
            fee_sat = max(total_input_sat - total_output_sat, 0)

        value_sat = _extract_satoshis(transaction, ('valueSat', 'value'))
        if value_sat == 0:
            value_sat = total_output_sat

        return {
            'hash': transaction.get('txid') or transaction.get('hash', ''),
            'time': _parse_transaction_time(transaction),
            'block_height': _to_int(transaction.get('blockHeight') or transaction.get('blockheight')),
            'confirmations': _to_int(transaction.get('confirmations')),
            'size': _to_int(transaction.get('size') or transaction.get('vsize')),
            'value': value_sat / SATOSHI,
            'fee': fee_sat / SATOSHI,
            'inputs': inputs,
            'out': outputs
        }
    except Exception as exc:
        logger.error("Error fetching transaction details: %s", exc)
        return None


def _fetch_transaction(tx_hash: str) -> Optional[Dict[str, Any]]:
    transaction: Optional[Dict[str, Any]] = None
    attempts = max(_available_node_count(), 1)

    for _ in range(attempts):
        url = _build_transaction_url(tx_hash)
        if not url:
            return None

        transaction = make_request(url, max_retries=1)
        if transaction:
            break

    return transaction


def _build_transaction_url(tx_hash: str) -> Optional[str]:
    try:
        base_url = config.get_node_url('tx')
    except Exception as exc:
        logger.error("Unable to determine transaction endpoint: %s", exc)
        return None

    return f"{base_url}{tx_hash}{PAGE_SUFFIX}"


def _available_node_count() -> int:
    api_nodes = getattr(config, 'api_nodes', None)
    if isinstance(api_nodes, dict):
        return len(api_nodes)
    return 1


def _normalise_inputs(transaction: Dict[str, Any]) -> List[Dict[str, Any]]:
    inputs = []
    for vin in transaction.get('vin', []) or []:
        inputs.append({
            'prev_out': {
                'addr': _extract_address(vin),
                'value': _extract_satoshis(vin, ('valueSat', 'value')) / SATOSHI
            }
        })
    return inputs


def _normalise_outputs(transaction: Dict[str, Any]) -> List[Dict[str, Any]]:
    outputs = []
    for vout in transaction.get('vout', []) or []:
        outputs.append({
            'addr': _extract_address(vout),
            'value': _extract_satoshis(vout, ('valueSat', 'value')) / SATOSHI
        })
    return outputs


def _parse_transaction_time(transaction: Dict[str, Any]) -> datetime:
    for field in ('blockTime', 'time', 'blocktime', 'receivedTime', 'timestamp'):
        value = transaction.get(field)
        if value is None:
            continue
        try:
            return datetime.utcfromtimestamp(int(float(value)))
        except (TypeError, ValueError, OverflowError):
            continue
    return datetime.utcfromtimestamp(0)


def _extract_satoshis(source: Dict[str, Any], keys: Iterable[str]) -> int:
    for key in keys:
        if key not in source:
            continue
        satoshis = _coerce_satoshis(source.get(key))
        if satoshis:
            return satoshis
    return 0


def _coerce_satoshis(value: Any) -> int:
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
        if '.' in stripped:
            return int(numeric * SATOSHI)
        return int(numeric)

    if isinstance(value, (int, float)):
        numeric = float(value)
        if numeric < 0:
            return 0
        if 0 < numeric < 1:
            return int(numeric * SATOSHI)
        return int(numeric)

    return 0


def _extract_address(entry: Dict[str, Any]) -> str:
    addresses = entry.get('addresses')
    if isinstance(addresses, list) and addresses:
        return addresses[0]
    if isinstance(addresses, str) and addresses:
        return addresses

    prev_out = entry.get('prevOut') or entry.get('prev_out')
    if isinstance(prev_out, dict):
        prev_addresses = prev_out.get('addresses')
        if isinstance(prev_addresses, list) and prev_addresses:
            return prev_addresses[0]
        if isinstance(prev_addresses, str) and prev_addresses:
            return prev_addresses
        for key in ('address', 'addr'):
            candidate = prev_out.get(key)
            if isinstance(candidate, str) and candidate:
                return candidate

    for key in ('address', 'addr'):
        candidate = entry.get(key)
        if isinstance(candidate, str) and candidate:
            return candidate

    if entry.get('coinbase') is not None:
        return 'Coinbase'

    return 'Unknown'


def _to_int(value: Any) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0
