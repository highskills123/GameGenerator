"""Entry point: python -m game_generator.server"""

import uvicorn
from .app import app, DEFAULT_RUNS_DIR  # noqa: F401

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="GameGenerator FastAPI server")
    parser.add_argument("--host", default="0.0.0.0", help="Bind host (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8080, help="Bind port (default: 8080)")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload (dev mode)")
    args = parser.parse_args()

    uvicorn.run(
        "game_generator.server.app:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )
