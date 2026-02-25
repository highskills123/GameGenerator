"""
schemas/build_spec.py – BuildSpec model.

Describes how the generated project should be built and packaged.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class BuildSpec:
    """Configuration for a single game generation run."""
    platform: str = "android"           # android | android+ios
    scope: str = "prototype"            # prototype | vertical-slice
    output_zip: str = "output.zip"      # destination ZIP path
    auto_fix: bool = False              # run flutter validate + patch loop
    max_fix_retries: int = 3
    run_validation: bool = False        # run flutter pub get + analyze
    run_tests: bool = False             # also run flutter test
