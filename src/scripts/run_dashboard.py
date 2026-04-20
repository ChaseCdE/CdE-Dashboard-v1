"""
Run the CdE Macroeconomic Dashboard.

Usage:
    python -m src.scripts.run_dashboard

Or directly:
    cd src/app && shiny run app.py
"""

import subprocess
import sys
from pathlib import Path


def main():
    # Get the app directory
    app_dir = Path(__file__).parent.parent / "app"
    app_file = app_dir / "app.py"

    if not app_file.exists():
        print(f"Error: App file not found at {app_file}")
        sys.exit(1)

    print("Starting CdE Macroeconomic Dashboard...")
    print(f"App location: {app_file}")
    print("-" * 50)

    # Run the shiny app
    subprocess.run(
        [sys.executable, "-m", "shiny", "run", str(app_file), "--reload"],
        cwd=str(app_dir),
    )


if __name__ == "__main__":
    main()
