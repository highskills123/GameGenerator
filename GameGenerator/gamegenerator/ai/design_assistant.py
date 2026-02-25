"""
design_assistant.py – Ollama-powered Idle RPG design document generator.

Public API
----------
    from gamegenerator.ai.design_assistant import generate_idle_rpg_design

    doc = generate_idle_rpg_design(
        "A dark fantasy idle RPG set in a cursed kingdom",
        model="qwen2.5-coder:7b",
    )

The function calls a local Ollama server (default http://localhost:11434)
via the /api/chat endpoint and returns a validated design document dict.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_MODEL = "qwen2.5-coder:7b"
DEFAULT_BASE_URL = "http://localhost:11434"
DEFAULT_TIMEOUT = 120

REQUIRED_KEYS = [
    "world",
    "premise",
    "main_story_beats",
    "quests",
    "characters",
    "factions",
    "locations",
    "items",
    "enemies",
]

# Keys that must be lists
_LIST_KEYS = ["main_story_beats", "quests", "characters", "factions", "locations", "items", "enemies"]

# Keys that must be dicts (or list of dicts; world/premise are strings here)
_DICT_KEYS: List[str] = []

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """\
You are an expert Idle RPG game designer. Given a game concept prompt, produce a \
comprehensive design document as a strict JSON object with EXACTLY these keys:

  world          (string) – setting/world description
  premise        (string) – core narrative premise
  main_story_beats (list of strings) – 5–8 major story milestones
  quests         (list of objects) – each with: title, summary, objectives (list), \
rewards (list), giver, level_range (list of 2 ints)
  characters     (list of objects) – each with: name, role, backstory, motivations \
(list), relationships (object mapping name -> relationship description)
  factions       (list of objects) – each with: name, description, alignment, goals (list)
  locations      (list of objects) – each with: name, description, type, notable_features (list)
  items          (list of objects) – each with: name, type, rarity, description, stats (object)
  enemies        (list of objects) – each with: name, type, description, abilities (list), \
loot (list)

Optional additional keys you MAY include:
  dialogue_samples (list of objects with: character, lines (list))
  upgrade_tree     (object with category keys mapping to lists of upgrade objects)
  idle_loops       (list of objects with: name, description, resource, tick_rate_seconds)

Output ONLY the JSON object. No markdown, no code fences, no extra text.
"""


# ---------------------------------------------------------------------------
# Public function
# ---------------------------------------------------------------------------


def generate_idle_rpg_design(
    prompt: str,
    *,
    model: Optional[str] = None,
    base_url: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    timeout: Optional[int] = None,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Generate an Idle RPG design document from a user prompt using Ollama.

    Args:
        prompt:      Natural-language game concept description.
        model:       Ollama model name (default: ``qwen2.5-coder:7b``).
        base_url:    Ollama server base URL (default: ``http://localhost:11434``).
        temperature: Sampling temperature (0.0–1.0).
        max_tokens:  Maximum number of tokens to generate.
        timeout:     HTTP request timeout in seconds (default: 120).
        seed:        Random seed for reproducibility (passed to Ollama if set).

    Returns:
        Validated design document as a Python dict.

    Raises:
        ImportError:   If ``requests`` is not installed.
        RuntimeError:  If Ollama is unreachable or returns an error response.
        ValueError:    If the response cannot be parsed as valid JSON or is
                       missing required design-document keys.
    """
    try:
        import requests  # type: ignore
    except ImportError as exc:
        raise ImportError(
            "The 'requests' package is required for Ollama integration. "
            "Install it with: pip install requests"
        ) from exc

    resolved_model = model or DEFAULT_MODEL
    resolved_base_url = (base_url or DEFAULT_BASE_URL).rstrip("/")
    resolved_timeout = timeout if timeout is not None else DEFAULT_TIMEOUT

    user_message = f"Game concept: {prompt}\n\nGenerate the design document JSON now."

    payload: Dict[str, Any] = {
        "model": resolved_model,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        "stream": False,
    }
    if temperature is not None:
        payload.setdefault("options", {})["temperature"] = temperature
    if max_tokens is not None:
        payload.setdefault("options", {})["num_predict"] = max_tokens
    if seed is not None:
        payload.setdefault("options", {})["seed"] = seed

    url = f"{resolved_base_url}/api/chat"
    try:
        response = requests.post(url, json=payload, timeout=resolved_timeout)
        response.raise_for_status()
    except requests.exceptions.ConnectionError as exc:
        raise RuntimeError(
            f"Could not connect to Ollama at {resolved_base_url}. "
            "Ensure Ollama is running (ollama serve) and try again."
        ) from exc
    except requests.exceptions.Timeout as exc:
        raise RuntimeError(
            f"Ollama request timed out after {resolved_timeout}s. "
            "Try increasing --ollama-timeout."
        ) from exc
    except requests.exceptions.HTTPError as exc:
        raise RuntimeError(
            f"Ollama returned HTTP {response.status_code}: {response.text[:200]}"
        ) from exc

    raw_content = response.json().get("message", {}).get("content", "")
    return _parse_and_validate(raw_content)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _strip_code_fences(text: str) -> str:
    """Remove leading/trailing markdown code fences if present."""
    text = text.strip()
    text = re.sub(r"^```[^\n]*\n?", "", text)
    text = re.sub(r"\n?```\s*$", "", text)
    return text.strip()


def _parse_and_validate(raw: str) -> Dict[str, Any]:
    """
    Parse a raw string response into a validated design document dict.

    Raises:
        ValueError: on parse failure or missing/wrong-typed required keys.
    """
    cleaned = _strip_code_fences(raw)

    # If the model wrapped the JSON in extra text, try to extract just the
    # outermost JSON object.
    if not cleaned.startswith("{"):
        match = re.search(r"\{", cleaned)
        if match:
            cleaned = cleaned[match.start():]

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Ollama response is not valid JSON: {exc}\n"
            f"Raw response (first 500 chars): {raw[:500]}"
        ) from exc

    if not isinstance(data, dict):
        raise ValueError(
            f"Expected a JSON object at the top level, got {type(data).__name__}."
        )

    # Check required keys exist
    missing = [k for k in REQUIRED_KEYS if k not in data]
    if missing:
        raise ValueError(
            f"Design document is missing required keys: {missing}. "
            f"Keys present: {list(data.keys())}"
        )

    # Check list keys are actually lists
    wrong_type_errors = []
    for key in _LIST_KEYS:
        if not isinstance(data[key], list):
            wrong_type_errors.append(
                f"'{key}' must be a list, got {type(data[key]).__name__}"
            )
    if wrong_type_errors:
        raise ValueError(
            "Design document has incorrect types:\n" + "\n".join(wrong_type_errors)
        )

    # Check string keys
    for key in ("world", "premise"):
        if not isinstance(data[key], str):
            raise ValueError(
                f"'{key}' must be a string, got {type(data[key]).__name__}"
            )

    return data


# ---------------------------------------------------------------------------
# Markdown renderer
# ---------------------------------------------------------------------------


def design_doc_to_markdown(doc: Dict[str, Any]) -> str:
    """Render a design document dict as a Markdown string."""
    lines: List[str] = []

    def _section(title: str) -> None:
        lines.append(f"\n## {title}\n")

    def _subsection(title: str) -> None:
        lines.append(f"\n### {title}\n")

    lines.append("# Idle RPG Design Document\n")

    _section("World")
    lines.append(doc.get("world", ""))

    _section("Premise")
    lines.append(doc.get("premise", ""))

    _section("Main Story Beats")
    for i, beat in enumerate(doc.get("main_story_beats", []), 1):
        lines.append(f"{i}. {beat}")

    _section("Quests")
    for quest in doc.get("quests", []):
        _subsection(quest.get("title", "Untitled Quest"))
        lines.append(f"**Summary:** {quest.get('summary', '')}")
        lines.append(f"\n**Giver:** {quest.get('giver', '')}")
        lr = quest.get("level_range", [])
        if lr:
            lines.append(f"\n**Level Range:** {lr[0]}–{lr[1]}")
        objs = quest.get("objectives", [])
        if objs:
            lines.append("\n**Objectives:**")
            for obj in objs:
                lines.append(f"- {obj}")
        rewards = quest.get("rewards", [])
        if rewards:
            lines.append("\n**Rewards:**")
            for r in rewards:
                lines.append(f"- {r}")

    _section("Characters")
    for char in doc.get("characters", []):
        _subsection(char.get("name", "Unknown"))
        lines.append(f"**Role:** {char.get('role', '')}")
        lines.append(f"\n**Backstory:** {char.get('backstory', '')}")
        motiv = char.get("motivations", [])
        if motiv:
            lines.append("\n**Motivations:**")
            for m in motiv:
                lines.append(f"- {m}")
        rels = char.get("relationships", {})
        if rels:
            lines.append("\n**Relationships:**")
            for name, rel in rels.items():
                lines.append(f"- *{name}*: {rel}")

    _section("Factions")
    for faction in doc.get("factions", []):
        _subsection(faction.get("name", "Unknown"))
        lines.append(f"**Alignment:** {faction.get('alignment', '')}")
        lines.append(f"\n{faction.get('description', '')}")
        goals = faction.get("goals", [])
        if goals:
            lines.append("\n**Goals:**")
            for g in goals:
                lines.append(f"- {g}")

    _section("Locations")
    for loc in doc.get("locations", []):
        _subsection(loc.get("name", "Unknown"))
        lines.append(f"**Type:** {loc.get('type', '')}")
        lines.append(f"\n{loc.get('description', '')}")
        features = loc.get("notable_features", [])
        if features:
            lines.append("\n**Notable Features:**")
            for f in features:
                lines.append(f"- {f}")

    _section("Items")
    for item in doc.get("items", []):
        _subsection(item.get("name", "Unknown"))
        lines.append(f"**Type:** {item.get('type', '')} | **Rarity:** {item.get('rarity', '')}")
        lines.append(f"\n{item.get('description', '')}")
        stats = item.get("stats", {})
        if stats:
            lines.append("\n**Stats:** " + ", ".join(f"{k}: {v}" for k, v in stats.items()))

    _section("Enemies")
    for enemy in doc.get("enemies", []):
        _subsection(enemy.get("name", "Unknown"))
        lines.append(f"**Type:** {enemy.get('type', '')}")
        lines.append(f"\n{enemy.get('description', '')}")
        abilities = enemy.get("abilities", [])
        if abilities:
            lines.append("\n**Abilities:**")
            for a in abilities:
                lines.append(f"- {a}")
        loot = enemy.get("loot", [])
        if loot:
            lines.append("\n**Loot:**")
            for l in loot:
                lines.append(f"- {l}")

    # Optional sections
    if "dialogue_samples" in doc:
        _section("Dialogue Samples")
        for sample in doc["dialogue_samples"]:
            _subsection(sample.get("character", "Unknown"))
            for line in sample.get("lines", []):
                lines.append(f'> "{line}"')

    if "upgrade_tree" in doc:
        _section("Upgrade Tree")
        for category, upgrades in doc["upgrade_tree"].items():
            _subsection(category)
            for upg in upgrades:
                if isinstance(upg, dict):
                    lines.append(f"- **{upg.get('name', '')}**: {upg.get('description', '')}")
                else:
                    lines.append(f"- {upg}")

    if "idle_loops" in doc:
        _section("Idle Loops")
        for loop in doc["idle_loops"]:
            _subsection(loop.get("name", "Unknown"))
            lines.append(f"**Resource:** {loop.get('resource', '')} | "
                         f"**Tick Rate:** {loop.get('tick_rate_seconds', '')}s")
            lines.append(f"\n{loop.get('description', '')}")

    return "\n".join(lines)
