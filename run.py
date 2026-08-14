from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND_SRC = ROOT / "backend" / "src"
FRONTEND_DIST = ROOT / "frontend" / "dist"

sys.path.insert(0, str(BACKEND_SRC))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run pyExplorer with Uvicorn.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--log-level", default="info")
    args = parser.parse_args()

    if not FRONTEND_DIST.joinpath("index.html").is_file():
        raise SystemExit(
            "Frontend build not found. Run the setup script or run `npm install && npm run build` "
            "inside the frontend directory first."
        )

    try:
        import uvicorn
    except ImportError as exc:
        raise SystemExit(
            "Backend dependencies are not installed. Run the setup script first."
        ) from exc

    uvicorn.run(
        "pyexplorer_api.asgi:app",
        host=args.host,
        port=args.port,
        log_level=args.log_level,
        server_header=False,
        timeout_keep_alive=5,
    )


if __name__ == "__main__":
    main()
