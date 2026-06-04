from conftest import TEST_ADDRESS, TEST_BLOCK_HEIGHT, TEST_TX_HASH, FakeBlockchainClient
from fastapi.testclient import TestClient


def test_health_and_ready(api_client: TestClient) -> None:
    health = api_client.get("/api/v1/health")
    assert health.status_code == 200
    assert health.json()["status"] == "healthy"

    ready = api_client.get("/api/v1/ready")
    assert ready.status_code == 200
    assert ready.json() == {
        "ready": True,
        "providers": 3,
        "realtime_enabled": False,
    }


def test_search_returns_api_and_frontend_paths(api_client: TestClient) -> None:
    tx_response = api_client.get("/api/v1/search", params={"q": TEST_TX_HASH.upper()})
    assert tx_response.status_code == 200
    assert tx_response.json()["type"] == "transaction"
    assert tx_response.json()["api_path"] == f"/transactions/{TEST_TX_HASH}"
    assert tx_response.json()["frontend_path"] == f"/transactions/{TEST_TX_HASH}"

    address_response = api_client.get("/api/v1/search", params={"q": TEST_ADDRESS})
    assert address_response.status_code == 200
    assert address_response.json()["type"] == "address"
    assert address_response.json()["frontend_path"] == f"/addresses/{TEST_ADDRESS}"

    block_response = api_client.get(
        "/api/v1/search", params={"q": str(TEST_BLOCK_HEIGHT)}
    )
    assert block_response.status_code == 200
    assert block_response.json()["type"] == "block"
    assert block_response.json()["frontend_path"] == f"/blocks/{TEST_BLOCK_HEIGHT}"


def test_search_invalid_query_returns_400(api_client: TestClient) -> None:
    response = api_client.get("/api/v1/search", params={"q": "not-a-bitcoin-query"})

    assert response.status_code == 400
    assert response.json()["code"] == "BAD_REQUEST"


def test_transaction_detail_returns_normalized_payload(api_client: TestClient) -> None:
    response = api_client.get(f"/api/v1/transactions/{TEST_TX_HASH}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["hash"] == TEST_TX_HASH
    assert payload["block_height"] == TEST_BLOCK_HEIGHT
    assert payload["confirmations"] == 12
    assert payload["value_btc"] == 0.00099
    assert payload["fee_btc"] == 0.00001
    assert payload["inputs"][0]["address"] == "bc1qinputaddress"
    assert payload["outputs"][0]["address"] == TEST_ADDRESS


def test_transaction_not_found_returns_404(
    api_client: TestClient, fake_blockchain_client: FakeBlockchainClient
) -> None:
    fake_blockchain_client.transactions.clear()

    response = api_client.get(f"/api/v1/transactions/{TEST_TX_HASH}")

    assert response.status_code == 404
    assert response.json()["code"] == "NOT_FOUND"
    assert response.json()["details"] == {"tx_hash": TEST_TX_HASH}


def test_address_detail_paginates_transactions(api_client: TestClient) -> None:
    response = api_client.get(
        f"/api/v1/addresses/{TEST_ADDRESS}", params={"page": 1, "per_page": 1}
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["address"] == TEST_ADDRESS
    assert payload["final_balance_btc"] == 0.0005
    assert payload["total_received_btc"] == 0.0015
    assert payload["total_sent_btc"] == 0.001
    assert payload["tx_count"] == 2
    assert len(payload["transactions"]) == 1
    assert payload["pagination"] == {
        "current_page": 1,
        "per_page": 1,
        "total_items": 2,
        "total_pages": 2,
    }


def test_address_not_found_returns_404(
    api_client: TestClient, fake_blockchain_client: FakeBlockchainClient
) -> None:
    fake_blockchain_client.addresses.clear()

    response = api_client.get(f"/api/v1/addresses/{TEST_ADDRESS}")

    assert response.status_code == 404
    assert response.json()["code"] == "NOT_FOUND"


def test_block_detail_paginates_transactions(api_client: TestClient) -> None:
    response = api_client.get(
        f"/api/v1/blocks/{TEST_BLOCK_HEIGHT}", params={"page": 2, "per_page": 1}
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["hash"] == "f" * 64
    assert payload["height"] == TEST_BLOCK_HEIGHT
    assert payload["tx_count"] == 2
    assert len(payload["transactions"]) == 1
    assert payload["transactions"][0]["hash"] == "e" * 64
    assert payload["pagination"] == {
        "current_page": 2,
        "per_page": 1,
        "total_items": 2,
        "total_pages": 2,
    }


def test_block_not_found_returns_404(
    api_client: TestClient, fake_blockchain_client: FakeBlockchainClient
) -> None:
    fake_blockchain_client.blocks.clear()

    response = api_client.get(f"/api/v1/blocks/{TEST_BLOCK_HEIGHT}")

    assert response.status_code == 404
    assert response.json()["code"] == "NOT_FOUND"


def test_network_overview_uses_mocked_stats(api_client: TestClient) -> None:
    response = api_client.get("/api/v1/network/overview")

    assert response.status_code == 200
    payload = response.json()
    assert payload["market_price_usd"] == 65000
    assert payload["latest_block_height"] == TEST_BLOCK_HEIGHT
    assert payload["tx_count_24h"] == 412345
    assert payload["mempool_size"] == 12345
    assert [provider["name"] for provider in payload["providers"]] == [
        "atomic",
        "guarda",
        "trezor",
    ]


def test_transaction_export_json_and_csv(api_client: TestClient) -> None:
    json_response = api_client.get(f"/api/v1/exports/transactions/{TEST_TX_HASH}.json")
    assert json_response.status_code == 200
    assert json_response.headers["content-type"] == "application/json"
    assert "transaction-aaaaaaaa.json" in json_response.headers["content-disposition"]
    assert json_response.json()["hash"] == TEST_TX_HASH

    csv_response = api_client.get(f"/api/v1/exports/transactions/{TEST_TX_HASH}.csv")
    assert csv_response.status_code == 200
    assert csv_response.headers["content-type"].startswith("text/csv")
    assert "Hash,Time,Block Height" in csv_response.text
    assert TEST_TX_HASH in csv_response.text


def test_address_export_json_and_csv(api_client: TestClient) -> None:
    json_response = api_client.get(f"/api/v1/exports/addresses/{TEST_ADDRESS}.json")
    assert json_response.status_code == 200
    assert json_response.json()["address"] == TEST_ADDRESS

    csv_response = api_client.get(f"/api/v1/exports/addresses/{TEST_ADDRESS}.csv")
    assert csv_response.status_code == 200
    assert "Address,Final Balance" in csv_response.text
    assert TEST_ADDRESS in csv_response.text


def test_unsupported_export_format_returns_400(api_client: TestClient) -> None:
    response = api_client.get(f"/api/v1/exports/transactions/{TEST_TX_HASH}.xml")

    assert response.status_code == 400
    assert response.json()["code"] == "BAD_REQUEST"
    assert response.json()["details"] == {"format": "xml"}
