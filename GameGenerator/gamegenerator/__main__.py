"""Entry point for ``python -m gamegenerator``."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gamegen import main  # noqa: E402

main()
