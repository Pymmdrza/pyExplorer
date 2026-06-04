import pytest
from pyexplorer_api.exceptions import BadRequestError
from pyexplorer_api.schemas.search import QueryType
from pyexplorer_api.utils.validators import (
    classify_query,
    validate_block_height,
    validate_tx_hash,
)


def test_classify_transaction_hash() -> None:
    assert classify_query("a" * 64) == QueryType.TRANSACTION


def test_classify_block_height() -> None:
    assert classify_query("840000") == QueryType.BLOCK
    assert validate_block_height("840000") == 840000


def test_invalid_query_raises() -> None:
    with pytest.raises(BadRequestError):
        classify_query("not-a-bitcoin-query")


def test_invalid_hash_raises() -> None:
    with pytest.raises(BadRequestError):
        validate_tx_hash("not-a-hash")
