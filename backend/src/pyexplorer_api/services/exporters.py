"""Data export helpers."""

import csv
import json
from io import StringIO
from typing import Any

from pydantic import BaseModel


def to_json(data: BaseModel | dict[str, Any]) -> str:
    payload = data.model_dump(mode="json") if isinstance(data, BaseModel) else data
    return json.dumps(payload, indent=2, ensure_ascii=False)


def transaction_to_csv(data: BaseModel | dict[str, Any]) -> str:
    payload = data.model_dump(mode="json") if isinstance(data, BaseModel) else data
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "Hash",
            "Time",
            "Block Height",
            "Confirmations",
            "Size",
            "Value (BTC)",
            "Fee (BTC)",
        ]
    )
    writer.writerow(
        [
            payload.get("hash", ""),
            payload.get("time", ""),
            payload.get("block_height", 0),
            payload.get("confirmations", 0),
            payload.get("size", 0),
            payload.get("value_btc", 0),
            payload.get("fee_btc", 0),
        ]
    )
    return output.getvalue()


def address_to_csv(data: BaseModel | dict[str, Any]) -> str:
    payload = data.model_dump(mode="json") if isinstance(data, BaseModel) else data
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "Address",
            "Final Balance (BTC)",
            "Total Received (BTC)",
            "Total Sent (BTC)",
            "Number of Transactions",
        ]
    )
    writer.writerow(
        [
            payload.get("address", ""),
            payload.get("final_balance_btc", 0),
            payload.get("total_received_btc", 0),
            payload.get("total_sent_btc", 0),
            payload.get("tx_count", 0),
        ]
    )
    return output.getvalue()
