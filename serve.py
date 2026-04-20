"""
CdE Dashboard — Authenticated Server Launcher

Starts the Shiny dashboard wrapped with HTTP Basic Auth.
Designed to work with any tunnel (ngrok, Cloudflare Tunnel, or direct).

Usage:
    python serve.py                     # default: port 8000, with auth
    python serve.py --port 8080         # custom port
    python serve.py --no-auth           # disable auth (local dev only)
    python serve.py --host 0.0.0.0      # listen on all interfaces
"""

import argparse
import sys
import os
from pathlib import Path

# Ensure the app directory is importable
APP_DIR = Path(__file__).parent / "src" / "app"
sys.path.insert(0, str(APP_DIR))


def create_app(use_auth: bool = True):
    """Create the ASGI application, optionally wrapped with auth."""
    # Import the Shiny app
    from app import app as shiny_app

    if use_auth:
        from auth_middleware import BasicAuthMiddleware
        return BasicAuthMiddleware(shiny_app)
    return shiny_app


def main():
    parser = argparse.ArgumentParser(description="CdE Dashboard Server")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on (default: 8000)")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to (default: 127.0.0.1)")
    parser.add_argument("--no-auth", action="store_true", help="Disable basic auth (local dev only)")
    parser.add_argument("--reload", action="store_true", help="Auto-reload on code changes")
    args = parser.parse_args()

    # Set working directory to app folder so relative imports work
    os.chdir(APP_DIR)

    try:
        import uvicorn
    except ImportError:
        print("Error: uvicorn is required. Install it with: pip install uvicorn")
        sys.exit(1)

    print("=" * 55)
    print("  CdE Macroeconomic Dashboard")
    print("=" * 55)
    print(f"  Local:  http://{args.host}:{args.port}")
    print(f"  Auth:   {'ENABLED' if not args.no_auth else 'DISABLED'}")
    if not args.no_auth:
        print(f"  User:   {os.environ.get('DASHBOARD_USER', '(from .env)')}")
    print("=" * 55)
    print()
    print("  To share externally, run one of:")
    print(f"    ngrok http {args.port}")
    print(f"    cloudflared tunnel --url http://localhost:{args.port}")
    print()

    app = create_app(use_auth=not args.no_auth)

    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
