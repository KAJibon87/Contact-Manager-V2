"""
run.py

PyInstaller entry point. Wraps app.main.main() so PyInstaller can
target a plain script instead of `python -m app.main`.
"""

import sys

from app.main import main

if __name__ == "__main__":
    sys.exit(main())