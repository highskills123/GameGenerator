"""Basic packaging metadata and import tests."""

import importlib
import importlib.metadata


def test_package_importable():
    """gamedesign_agent must be importable."""
    mod = importlib.import_module("gamedesign_agent")
    assert mod is not None


def test_gamegen_importable():
    """gamegen module (root gamegen.py) must be importable."""
    mod = importlib.import_module("gamegen")
    assert mod is not None


def test_gamegen_has_main():
    """gamegen must expose a callable main() for the console script."""
    mod = importlib.import_module("gamegen")
    assert callable(getattr(mod, "main", None))


def test_package_metadata():
    """Installed package metadata must expose the expected extras."""
    meta = importlib.metadata.metadata("gamegenerator-design-assistant")
    assert meta["Name"] == "gamegenerator-design-assistant"
    assert meta["Version"]


def test_ollama_extra_declared():
    """The [ollama] extra must be declared in package metadata."""
    reqs = importlib.metadata.requires("gamegenerator-design-assistant") or []
    extras = {r for r in reqs if 'extra == "ollama"' in r}
    assert extras, "[ollama] extra not found in package metadata"


def test_dev_extra_declared():
    """The [dev] extra must be declared in package metadata."""
    reqs = importlib.metadata.requires("gamegenerator-design-assistant") or []
    extras = {r for r in reqs if 'extra == "dev"' in r}
    assert extras, "[dev] extra not found in package metadata"
