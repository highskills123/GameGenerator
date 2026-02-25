#!/usr/bin/env python3
"""
gamegen.py – GameGenerator CLI entry point.

Usage
-----
    python gamegen.py --prompt "top down space shooter" --out game.zip
    python gamegen.py --prompt "idle RPG with upgrades" \\
        --assets-dir "C:\\\\Users\\\\me\\\\assets" \\
        --out my_game.zip --platform android --scope vertical-slice --auto-fix

    # Interactive constraint prompts
    python gamegen.py --prompt "space shooter" --out game.zip --interactive

    # AI-enhanced spec (requires Ollama)
    python gamegen.py --prompt "..." --out game.zip --model qwen2.5-coder:7b
"""

import argparse
import sys

from colorama import Fore, Style, init

init(autoreset=True)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gamegen",
        description="GameGenerator – Flutter/Flame Game Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python gamegen.py --prompt "top down space shooter" --out game.zip
  python gamegen.py --prompt "idle RPG with upgrades" \\
      --assets-dir "C:\\\\Users\\\\me\\\\assets" --out my_game.zip \\
      --platform android --scope vertical-slice --auto-fix
        """,
    )

    # Required
    parser.add_argument("--prompt", required=True, help="Natural-language game description")
    parser.add_argument("--out", required=True, help="Output ZIP file path")

    # Generation flags
    parser.add_argument("--assets-dir", dest="assets_dir",
                        help="Local folder containing game assets (images/audio)")
    parser.add_argument("--platform", default="android",
                        choices=["android", "android+ios"],
                        help="Target platform (default: android)")
    parser.add_argument("--scope", default="prototype",
                        choices=["prototype", "vertical-slice"],
                        help="Project scope (default: prototype)")
    parser.add_argument("--art-style", dest="art_style", default="pixel-art",
                        help="Art style hint (default: pixel-art)")
    parser.add_argument("--online", action="store_true",
                        help="Generate an online-multiplayer game")

    # Validation flags
    parser.add_argument("--validate", action="store_true",
                        help="Run flutter pub get + flutter analyze after scaffolding")
    parser.add_argument("--auto-fix", dest="auto_fix", action="store_true",
                        help="Re-run validation and patch on failure (implies --validate)")

    # UX
    parser.add_argument("--interactive", action="store_true",
                        help="Prompt for constraint questions before generating")

    # Optional AI / Ollama flags
    parser.add_argument("--model", help="Ollama model for AI-enhanced spec")
    parser.add_argument("--temperature", type=float,
                        help="Ollama sampling temperature (0.0–1.0)")
    parser.add_argument("--max-tokens", dest="max_tokens", type=int,
                        help="Max tokens for Ollama generation")
    parser.add_argument("--timeout", type=int,
                        help="Ollama request timeout in seconds")

    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    print(f"{Fore.CYAN}{'='*70}")
    print(f"{Fore.CYAN}GameGenerator – Flutter/Flame Game Generator")
    print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}\n")

    # Optional Ollama translator (bring-your-own)
    translator = None
    if args.model:
        try:
            import importlib
            aibase = importlib.import_module("aibase")
            translator = aibase.AibaseTranslator(
                model=args.model,
                temperature=args.temperature,
                max_tokens=args.max_tokens,
                timeout=args.timeout,
            )
        except Exception:
            print(
                f"{Fore.YELLOW}[WARNING] Could not initialise AI translator; "
                f"falling back to heuristic spec.{Style.RESET_ALL}"
            )

    from gamegenerator.orchestrator import Orchestrator

    orchestrator = Orchestrator(interactive=args.interactive)
    try:
        orchestrator.run(
            prompt=args.prompt,
            output_zip=args.out,
            assets_dir=args.assets_dir,
            platform=args.platform,
            scope=args.scope,
            auto_fix=args.auto_fix,
            run_validation=args.validate,
            translator=translator,
            constraint_overrides={
                "art_style": args.art_style,
                "online": args.online if args.online else None,
            },
        )
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Cancelled.{Style.RESET_ALL}")
        sys.exit(0)
    except Exception as exc:
        print(f"{Fore.RED}Error: {exc}{Style.RESET_ALL}")
        sys.exit(1)


if __name__ == "__main__":
    main()
