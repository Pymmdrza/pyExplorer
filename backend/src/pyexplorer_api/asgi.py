"""ASGI entrypoint for production and local server runners."""

from pyexplorer_api.main import create_app

app = create_app()
