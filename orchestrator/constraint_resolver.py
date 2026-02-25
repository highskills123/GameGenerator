"""
orchestrator/constraint_resolver.py – Constraint resolver.

Resolves game constraints from CLI arguments (non-interactive) or by
prompting the user (interactive mode).  Enforces Flame-specific limits
(e.g. 2D only).
"""

from __future__ import annotations

from typing import Any, Dict, Optional

# Sensible defaults applied when a value is not supplied.
DEFAULTS: Dict[str, Any] = {
    "dimension": "2D",          # Flame supports 2D only
    "art_style": "pixel-art",
    "online": False,
    "platform": "android",
    "scope": "prototype",
}


class ConstraintResolver:
    """Resolve game constraints, enforcing Flame engine limits."""

    def __init__(self, interactive: bool = False):
        self.interactive = interactive

    def resolve(self, overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Return a fully-populated constraints dict.

        Args:
            overrides: Values from CLI flags.  ``None`` or absent keys fall
                       back to ``DEFAULTS``.

        Returns:
            Dict with keys: dimension, art_style, online, platform, scope.
        """
        constraints = dict(DEFAULTS)
        if overrides:
            for key, val in overrides.items():
                if val is not None:
                    constraints[key] = val

        # Enforce Flame constraint: only 2D is supported.
        if constraints.get("dimension", "2D") != "2D":
            print(
                "[WARNING] Only 2D is supported with the Flame engine. "
                "Enforcing dimension=2D."
            )
            constraints["dimension"] = "2D"

        if self.interactive:
            constraints = self._ask_questions(constraints)

        return constraints

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _ask_questions(self, constraints: Dict[str, Any]) -> Dict[str, Any]:
        """Prompt the user to confirm or override each constraint."""
        print("\n=== Game Constraints (press Enter to accept default) ===\n")

        art = input(f"Art style [{constraints['art_style']}]: ").strip()
        if art:
            constraints["art_style"] = art

        platform_raw = input(
            f"Target platform (android / android+ios) [{constraints['platform']}]: "
        ).strip()
        if platform_raw in ("android", "android+ios"):
            constraints["platform"] = platform_raw

        online_default = "yes" if constraints["online"] else "no"
        online_raw = input(
            f"Online multiplayer? (yes/no) [{online_default}]: "
        ).strip().lower()
        if online_raw in ("yes", "y"):
            constraints["online"] = True
        elif online_raw in ("no", "n"):
            constraints["online"] = False

        scope_raw = input(
            f"Scope (prototype / vertical-slice) [{constraints['scope']}]: "
        ).strip()
        if scope_raw in ("prototype", "vertical-slice"):
            constraints["scope"] = scope_raw

        return constraints
