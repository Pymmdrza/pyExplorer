"""Production web application serving helpers."""

from __future__ import annotations

from pathlib import Path

from starlette.datastructures import Headers
from starlette.exceptions import HTTPException
from starlette.responses import FileResponse, Response
from starlette.staticfiles import StaticFiles
from starlette.types import Scope


class SPAStaticFiles(StaticFiles):
    """Serve a compiled single-page application with browser-navigation fallback."""

    async def get_response(self, path: str, scope: Scope) -> Response:
        try:
            response = await super().get_response(path, scope)
        except HTTPException as exc:
            if exc.status_code != 404:
                raise
            response = Response(status_code=404)

        if response.status_code != 404 or scope.get("method") not in {"GET", "HEAD"}:
            return response

        accepted = Headers(scope=scope).get("accept", "")
        if "text/html" not in accepted and "application/xhtml+xml" not in accepted:
            return response

        index_path = Path(self.directory) / "index.html"
        if index_path.is_file():
            return FileResponse(index_path)
        return response


def find_frontend_dist() -> Path | None:
    """Find the compiled frontend for source-tree and packaged deployments."""
    package_dir = Path(__file__).resolve().parent
    candidates = (
        package_dir / "static",
        package_dir.parents[2] / "frontend" / "dist",
        Path.cwd() / "frontend" / "dist",
    )

    for candidate in candidates:
        if (candidate / "index.html").is_file():
            return candidate
    return None
