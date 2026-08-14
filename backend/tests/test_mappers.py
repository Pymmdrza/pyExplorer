from pyexplorer_api.services.mappers import (
    coerce_satoshis,
    extract_address,
    normalise_transaction,
    to_float,
    to_int,
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


def test_numeric_normalizers_reject_negative_and_non_finite_values() -> None:
    assert to_int(-1) == 0
    assert to_int("-42") == 0
    assert to_int(float("inf")) == 0
    assert to_float(-0.1) == 0.0
    assert to_float(float("nan")) == 0.0
    assert coerce_satoshis(float("inf")) == 0
    assert coerce_satoshis("nan") == 0


def test_normalise_unconfirmed_transaction_clamps_negative_chain_metadata() -> None:
    tx = {
        "txid": "b" * 64,
        "time": 1_710_000_000,
        "blockHeight": -1,
        "confirmations": -1,
        "size": -1,
        "vin": [{"addresses": ["input"], "value": 1000}],
        "vout": [{"addresses": ["output"], "value": 900}],
    }

    normalised = normalise_transaction(tx)

    assert normalised["block_height"] == 0
    assert normalised["confirmations"] == 0
    assert normalised["size"] == 0
