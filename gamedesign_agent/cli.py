"""
cli.py – Command-line interface for the AI Design Assistant.

Usage
-----
Interactive multi-turn chat (default):
    python -m gamedesign_agent

Sub-commands (non-interactive):
    python -m gamedesign_agent level   [--seed N] [--width W] [--height H] [--rooms R] [--ascii]
    python -m gamedesign_agent npc     [--type TYPE] [--mood MOOD] [--lines N] [--seed N]
    python -m gamedesign_agent art     [--scene SCENE] [--style STYLE] [--description "..."] [--seed N]
    python -m gamedesign_agent chat    "your message here"

Environment variables:
    GAMEDESIGN_LLM_BACKEND  – none|ollama|hf_api  (default: none)
    GAMEDESIGN_ART_BACKEND  – none|auto1111|diffusers (default: none)
    See gamedesign_agent/config.py for the full list.
"""

from __future__ import annotations

import argparse
import json
import sys

from . import config
from .agent import GameDesignAgent


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gamedesign_agent",
        description="AI Game Design Assistant (free/OSS only)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--backend",
        default=config.LLM_BACKEND,
        choices=["none", "ollama", "hf_api"],
        help="LLM backend to use (default: %(default)s)",
    )

    sub = parser.add_subparsers(dest="command")

    # ------------------------------------------------------------------ level
    level_p = sub.add_parser("level", help="Generate a procedural dungeon level")
    level_p.add_argument("--seed", type=int, default=None, help="RNG seed")
    level_p.add_argument("--width", type=int, default=60)
    level_p.add_argument("--height", type=int, default=40)
    level_p.add_argument("--rooms", type=int, default=12, dest="num_rooms")
    level_p.add_argument(
        "--ascii", action="store_true", help="Print ASCII tile map to stdout"
    )
    level_p.add_argument(
        "--json", action="store_true", dest="as_json",
        help="Print full level data as JSON"
    )

    # ------------------------------------------------------------------ npc
    npc_p = sub.add_parser("npc", help="Generate NPC dialogue")
    npc_p.add_argument("--type", default="villager", dest="npc_type",
                       help="NPC type (merchant|guard|wizard|villager|enemy|quest_giver)")
    npc_p.add_argument("--mood", default="neutral",
                       help="NPC mood (friendly|neutral|hostile)")
    npc_p.add_argument("--lines", type=int, default=3, dest="num_lines")
    npc_p.add_argument("--context", default=None,
                       help="Scene context (for LLM backends)")
    npc_p.add_argument("--seed", type=int, default=None)

    # ------------------------------------------------------------------ art
    art_p = sub.add_parser("art", help="Generate a Stable Diffusion / DALL-E art prompt")
    art_p.add_argument("--scene", default="dungeon", dest="scene_type",
                       help="Scene type (dungeon|forest|castle|city|character|creature|item|landscape)")
    art_p.add_argument("--style", default="fantasy",
                       help="Visual style (fantasy|sci-fi|horror|cartoon|realistic|pixel)")
    art_p.add_argument("--description", default=None)
    art_p.add_argument("--seed", type=int, default=None)
    art_p.add_argument("--generate-image", action="store_true",
                       help="Submit the prompt to the configured image backend")
    art_p.add_argument("--output", default=None, help="Output image file path")

    # ------------------------------------------------------------------ chat
    chat_p = sub.add_parser("chat", help="Send a single message to the assistant")
    chat_p.add_argument("message", nargs="+", help="Message text")

    return parser


def _cmd_level(args: argparse.Namespace, agent: GameDesignAgent) -> None:
    from .level_generation import ProceduralLevelGenerator
    gen = ProceduralLevelGenerator(
        width=args.width,
        height=args.height,
        num_rooms=args.num_rooms,
    )
    level = gen.generate(seed=args.seed)

    if args.as_json:
        print(level.to_json())
        return

    print(f"Seed: {level.seed}")
    print(f"Rooms: {level.metadata['room_count']}  Corridors: {level.metadata['corridor_count']}")
    if args.ascii:
        print()
        print(level.to_ascii())
    else:
        print("\nRooms:")
        for r in level.rooms:
            print(f"  [{r.id}] {r.room_type:10s}  ({r.x},{r.y})  {r.width}×{r.height}")
        print("\nRun with --ascii to see the tile map, or --json for full data.")


def _cmd_npc(args: argparse.Namespace, agent: GameDesignAgent) -> None:
    lines = agent.write_npc_dialogue(
        npc_type=args.npc_type,
        mood=args.mood,
        num_lines=args.num_lines,
        context=args.context,
        seed=args.seed,
    )
    print(f"[{args.npc_type.upper()} – {args.mood}]")
    for line in lines:
        print(f"  \"{line}\"")


def _cmd_art(args: argparse.Namespace, agent: GameDesignAgent) -> None:
    prompt = agent.create_art_prompt(
        scene_type=args.scene_type,
        style=args.style,
        description=args.description,
        seed=args.seed,
    )
    print(f"Scene: {prompt.scene_type}  |  Style: {prompt.style}  |  Seed: {prompt.seed}")
    print(f"\nPositive prompt:\n  {prompt.positive}")
    print(f"\nNegative prompt:\n  {prompt.negative}")

    if args.generate_image:
        from .art_prompting import ArtPromptGenerator
        gen = ArtPromptGenerator()
        result = gen.generate_image(prompt, output_path=args.output)
        if result.image_path:
            print(f"\n✅ Image saved to: {result.image_path}")
        elif result.backend_used == "none":
            print(
                "\nℹ️  Image generation is disabled (GAMEDESIGN_ART_BACKEND=none).\n"
                "   Set GAMEDESIGN_ART_BACKEND=auto1111 or GAMEDESIGN_ART_BACKEND=diffusers "
                "to enable local image generation."
            )


def _cmd_chat_single(args: argparse.Namespace, agent: GameDesignAgent) -> None:
    message = " ".join(args.message)
    response = agent.chat(message)
    print(response)


def _interactive_chat(agent: GameDesignAgent) -> None:
    print("╔══════════════════════════════════════════════════════╗")
    print("║   AI Game Design Assistant  (type 'quit' to exit)   ║")
    print("╚══════════════════════════════════════════════════════╝")
    print(f"  LLM backend : {config.LLM_BACKEND}")
    print(f"  Art backend : {config.ART_BACKEND}")
    print()

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            break
        if user_input.lower() in ("reset", "clear"):
            agent.reset()
            print("Conversation cleared.\n")
            continue

        try:
            response = agent.chat(user_input)
        except Exception as exc:  # noqa: BLE001
            print(f"[Error] {exc}")
            continue

        print(f"\nAssistant: {response}\n")


def main(argv: list | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    agent = GameDesignAgent(llm_backend=args.backend)

    if args.command == "level":
        _cmd_level(args, agent)
    elif args.command == "npc":
        _cmd_npc(args, agent)
    elif args.command == "art":
        _cmd_art(args, agent)
    elif args.command == "chat":
        _cmd_chat_single(args, agent)
    else:
        _interactive_chat(agent)

    return 0


if __name__ == "__main__":
    sys.exit(main())
