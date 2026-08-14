from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from pyexplorer_api.web import SPAStaticFiles


def create_web_client(directory: Path) -> TestClient:
    app = FastAPI()
    app.mount("/", SPAStaticFiles(directory=directory, html=True), name="frontend")
    return TestClient(app)


def test_static_frontend_serves_index_and_assets(tmp_path: Path) -> None:
    (tmp_path / "index.html").write_text("<html>app</html>", encoding="utf-8")
    assets = tmp_path / "assets"
    assets.mkdir()
    (assets / "app.js").write_text("console.log('app')", encoding="utf-8")

    client = create_web_client(tmp_path)

    assert client.get("/").status_code == 200
    assert client.get("/assets/app.js").status_code == 200


def test_spa_fallback_is_limited_to_browser_navigation(tmp_path: Path) -> None:
    (tmp_path / "index.html").write_text("<html>app</html>", encoding="utf-8")
    client = create_web_client(tmp_path)

    navigation = client.get("/transactions/example", headers={"Accept": "text/html"})
    missing_asset = client.get("/assets/missing.js", headers={"Accept": "*/*"})

    assert navigation.status_code == 200
    assert navigation.text == "<html>app</html>"
    assert missing_asset.status_code == 404
