"""Allow the package to be run as ``python -m gamedesign_agent``."""
from .cli import main
import sys

sys.exit(main())
