from pyexplorer_api.services.mappers import (
    coerce_satoshis,
    extract_address,
    normalise_transaction,
)


def test_coerce_satoshis_from_btc_string() -> None:
    assert coerce_satoshis("0.50000000") == 50_000_000


def test_extract_address_from_prev_out() -> None:
    assert extract_address({"prev_out": {"addr": "bc1example"}}) == "bc1example"


def test_normalise_transaction() -> None:
    tx = {
        "txid": "a" * 64,
        "time": 1,
        "confirmations": 2,
        "size": 200,
        "vin": [{"addresses": ["input"], "value": 1000}],
        "vout": [{"addresses": ["output"], "value": 900}],
    }
    normalised = normalise_transaction(tx)
    assert normalised["hash"] == "a" * 64
    assert normalised["fee_btc"] == 0.000001
