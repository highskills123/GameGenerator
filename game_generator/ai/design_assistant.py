"""
design_assistant.py – Ollama-powered Idle RPG design document generator.

Public API
----------
    from game_generator.ai.design_assistant import generate_idle_rpg_design

    doc = generate_idle_rpg_design(
        "A dark fantasy idle RPG set in a cursed kingdom",
        model="qwen2.5-coder:7b",
    )

    # Offline / no-Ollama fallback:
    from game_generator.ai.design_assistant import generate_idle_rpg_design_template
    doc = generate_idle_rpg_design_template("A dark fantasy idle RPG", seed=42)

The Ollama function calls a local Ollama server (default http://localhost:11434)
via the /api/chat endpoint and returns a validated design document dict.
The template function is fully offline and deterministic (optionally seeded).
"""

from __future__ import annotations

import json
import random
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

    # Deep-validate against the Pydantic schema model
    try:
        from schemas.idle_rpg_design_doc import validate_idle_rpg_design_doc
        validate_idle_rpg_design_doc(data)
    except ImportError:
        pass  # schemas package not on path – skip Pydantic validation

    return data


# ---------------------------------------------------------------------------
# Template-based offline fallback generator
# ---------------------------------------------------------------------------

_WORLDS = [
    "A cursed kingdom frozen in eternal twilight where the undead roam freely.",
    "A sprawling space colony fighting for survival on a hostile alien world.",
    "An ancient empire crumbling under the weight of dark sorcery and betrayal.",
    "A steampunk city powered by stolen magic where guilds wage shadow wars.",
    "A post-apocalyptic wasteland where survivors rebuild civilisation shard by shard.",
]

_PREMISES = [
    "A lone hero must rally allies and grow powerful enough to defeat the dark overlord.",
    "Scattered survivors unite under a visionary leader to reclaim their lost homeland.",
    "An unlikely champion rises from obscurity to challenge an immortal tyrant.",
    "Ancient prophecy drives a reluctant hero toward a destiny they cannot escape.",
    "An alliance of outcasts builds an empire from nothing, overcoming impossible odds.",
]

_STORY_BEATS_POOL = [
    "The hero awakens to a world in chaos and takes their first steps.",
    "A mentor figure reveals the true scope of the threat.",
    "First major victory: the hero defeats a champion of the enemy.",
    "A devastating betrayal forces the hero to rethink their alliances.",
    "The hero discovers a hidden power that changes everything.",
    "Mid-game crisis: all seems lost as the enemy strikes at the heart.",
    "The tide turns as old enemies become unlikely allies.",
    "Final preparations: the hero gathers strength for the ultimate battle.",
    "The climactic confrontation with the main antagonist.",
    "Epilogue: a fragile peace settles over the land.",
]

_QUEST_TEMPLATES = [
    {
        "title": "First Blood",
        "summary": "Defeat your first enemies to prove your worth.",
        "giver": "Village Elder",
        "level_range": [1, 3],
        "objectives": ["Defeat 5 enemies", "Return alive"],
        "rewards": ["50 gold", "5 XP"],
    },
    {
        "title": "The Gathering Storm",
        "summary": "Collect resources before the enemy reinforcements arrive.",
        "giver": "Scout Captain",
        "level_range": [3, 6],
        "objectives": ["Collect 100 iron", "Defeat 10 scouts"],
        "rewards": ["150 gold", "Iron Shield"],
    },
    {
        "title": "Trial by Fire",
        "summary": "Survive a deadly gauntlet to earn the guild's trust.",
        "giver": "Guild Master",
        "level_range": [5, 10],
        "objectives": ["Survive 10 waves", "Don't use potions"],
        "rewards": ["300 gold", "Guild Badge", "30 XP"],
    },
    {
        "title": "Into the Depths",
        "summary": "Explore the forbidden zone and return with ancient secrets.",
        "giver": "Archivist Mira",
        "level_range": [8, 15],
        "objectives": ["Reach the inner sanctum", "Defeat the guardian"],
        "rewards": ["500 gold", "Ancient Tome"],
    },
    {
        "title": "The Final Stand",
        "summary": "Lead the last army against the darkness itself.",
        "giver": "High Commander",
        "level_range": [15, 20],
        "objectives": ["Destroy the dark beacon", "Protect the fortress"],
        "rewards": ["1000 gold", "Legendary Sword", "100 XP"],
    },
]

_CHARACTER_TEMPLATES = [
    {
        "name": "Aela the Brave",
        "role": "Hero",
        "backstory": "A former soldier who lost everything to the darkness.",
        "motivations": ["Protect the innocent", "Reclaim lost honour"],
        "relationships": {"Elder Mira": "mentor", "Raven": "rival"},
    },
    {
        "name": "Elder Mira",
        "role": "Mentor NPC",
        "backstory": "Ancient keeper of knowledge who foresaw the coming darkness.",
        "motivations": ["Guide the chosen hero", "Preserve ancient wisdom"],
        "relationships": {"Aela the Brave": "student"},
    },
    {
        "name": "Raven",
        "role": "Antagonist",
        "backstory": "Once a hero, now consumed by power and bitterness.",
        "motivations": ["Rule through fear", "Prove superiority"],
        "relationships": {"Aela the Brave": "nemesis"},
    },
]

_FACTION_TEMPLATES = [
    {
        "name": "The Silver Order",
        "description": "A knightly order sworn to protect the realm.",
        "alignment": "lawful good",
        "goals": ["Defeat the darkness", "Restore the old kingdom"],
    },
    {
        "name": "The Shadow Syndicate",
        "description": "A ruthless criminal network thriving in the chaos.",
        "alignment": "neutral evil",
        "goals": ["Control the black market", "Undermine the heroes"],
    },
    {
        "name": "The Free Cities Alliance",
        "description": "Independent city-states united by mutual self-interest.",
        "alignment": "true neutral",
        "goals": ["Maintain independence", "Profit from the conflict"],
    },
]

_LOCATION_TEMPLATES = [
    {
        "name": "Ironhold Citadel",
        "type": "fortress",
        "description": "The last bastion of civilisation against the tide of darkness.",
        "notable_features": ["Great Hall", "Armoury", "Training Grounds"],
    },
    {
        "name": "The Whispering Wood",
        "type": "forest",
        "description": "An ancient forest where spirits dwell and dark things lurk.",
        "notable_features": ["Hidden shrine", "Bandit camp", "Spirit grove"],
    },
    {
        "name": "Ashfall Crater",
        "type": "dungeon",
        "description": "A vast crater left by a catastrophic ancient explosion.",
        "notable_features": ["Lava pools", "Treasure vault", "Boss lair"],
    },
    {
        "name": "Market Haven",
        "type": "town",
        "description": "A bustling trading hub where merchants and adventurers meet.",
        "notable_features": ["Blacksmith", "Alchemist shop", "Tavern"],
    },
]

_ITEM_TEMPLATES = [
    {
        "name": "Iron Sword",
        "type": "weapon",
        "rarity": "common",
        "description": "A reliable blade for any aspiring hero.",
        "stats": {"attack": 5},
    },
    {
        "name": "Leather Armour",
        "type": "armour",
        "rarity": "common",
        "description": "Basic protection against light attacks.",
        "stats": {"defence": 3},
    },
    {
        "name": "Silver Blade",
        "type": "weapon",
        "rarity": "uncommon",
        "description": "Effective against undead and dark creatures.",
        "stats": {"attack": 15, "dark_bonus": 10},
    },
    {
        "name": "Amulet of Might",
        "type": "accessory",
        "rarity": "rare",
        "description": "Channels ancient power into the wearer.",
        "stats": {"attack": 10, "hp_bonus": 20},
    },
    {
        "name": "Legendary Heartstone",
        "type": "accessory",
        "rarity": "legendary",
        "description": "A gem said to be the crystallised heart of a fallen god.",
        "stats": {"attack": 30, "defence": 20, "hp_bonus": 50},
    },
]

_ENEMY_TEMPLATES = [
    {
        "name": "Shadow Wraith",
        "type": "undead",
        "description": "A wisp of pure darkness that drains the will to fight.",
        "abilities": ["Life Drain", "Phase Shift"],
        "loot": ["Shadow Essence", "10 gold"],
    },
    {
        "name": "Iron Golem",
        "type": "construct",
        "description": "A hulking automaton built to guard ancient treasure.",
        "abilities": ["Slam", "Iron Skin"],
        "loot": ["Iron Ingot", "50 gold"],
    },
    {
        "name": "Forest Troll",
        "type": "beast",
        "description": "A regenerating brute that haunts the deep woods.",
        "abilities": ["Regeneration", "Boulder Throw"],
        "loot": ["Troll Hide", "25 gold"],
    },
    {
        "name": "Dark Sorcerer",
        "type": "humanoid",
        "description": "A mage who sold their soul for forbidden power.",
        "abilities": ["Fireball", "Curse", "Teleport"],
        "loot": ["Spell Scroll", "80 gold", "Dark Crystal"],
    },
]

_UPGRADE_TREE_TEMPLATE = {
    "Combat": [
        {"name": "Sharpened Blade", "description": "Increase attack damage by 20%.", "cost": 100},
        {"name": "Battle Frenzy", "description": "Auto-attack speed increased by 15%.", "cost": 250},
        {"name": "Crushing Blow", "description": "Chance to deal double damage.", "cost": 500},
    ],
    "Defence": [
        {"name": "Reinforced Armour", "description": "Reduce incoming damage by 10%.", "cost": 100},
        {"name": "Iron Will", "description": "Increase max HP by 25%.", "cost": 250},
        {"name": "Last Stand", "description": "Survive a killing blow once per battle.", "cost": 500},
    ],
    "Economy": [
        {"name": "Gold Rush", "description": "Enemies drop 25% more gold.", "cost": 150},
        {"name": "Merchant's Eye", "description": "Shop items cost 15% less.", "cost": 300},
        {"name": "Treasure Hunter", "description": "Chance to find bonus loot on kills.", "cost": 600},
    ],
}

_IDLE_LOOPS_TEMPLATE = [
    {
        "name": "Gold Mine",
        "description": "Passive gold generation from your mines.",
        "resource": "gold",
        "tick_rate_seconds": 5,
    },
    {
        "name": "Experience Training",
        "description": "Heroes train automatically, gaining XP over time.",
        "resource": "experience",
        "tick_rate_seconds": 10,
    },
    {
        "name": "Auto Battle",
        "description": "Your hero fights enemies automatically.",
        "resource": "combat_progress",
        "tick_rate_seconds": 1,
    },
]


def generate_idle_rpg_design_template(
    prompt: str,
    *,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Generate a deterministic template-based Idle RPG design document.

    This function works fully offline without Ollama.  It uses a fixed set of
    templates combined with optional seeding for reproducibility.

    Args:
        prompt: Natural-language game concept description (used to seed RNG
                when *seed* is not provided).
        seed:   Explicit integer seed.  If omitted, the hash of *prompt* is used,
                making the output deterministic for a given prompt string.

    Returns:
        Validated design document dict (same schema as ``generate_idle_rpg_design``).
    """
    rng = random.Random(seed if seed is not None else hash(prompt) & 0xFFFFFFFF)

    world = rng.choice(_WORLDS)
    premise = rng.choice(_PREMISES)
    story_beats = rng.sample(_STORY_BEATS_POOL, k=min(6, len(_STORY_BEATS_POOL)))
    quests = rng.sample(_QUEST_TEMPLATES, k=min(3, len(_QUEST_TEMPLATES)))
    characters = list(_CHARACTER_TEMPLATES)
    factions = list(_FACTION_TEMPLATES)
    locations = rng.sample(_LOCATION_TEMPLATES, k=min(3, len(_LOCATION_TEMPLATES)))
    items = rng.sample(_ITEM_TEMPLATES, k=min(4, len(_ITEM_TEMPLATES)))
    enemies = rng.sample(_ENEMY_TEMPLATES, k=min(3, len(_ENEMY_TEMPLATES)))

    doc: Dict[str, Any] = {
        "world": world,
        "premise": premise,
        "main_story_beats": story_beats,
        "quests": quests,
        "characters": characters,
        "factions": factions,
        "locations": locations,
        "items": items,
        "enemies": enemies,
        "upgrade_tree": _UPGRADE_TREE_TEMPLATE,
        "idle_loops": _IDLE_LOOPS_TEMPLATE,
    }

    # Validate using the same logic as the Ollama path
    return _parse_and_validate(json.dumps(doc))


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
