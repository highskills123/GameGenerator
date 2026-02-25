#!/usr/bin/env python3
"""
idle_rpg_gen.py – One-shot Idle RPG game generator.

Generates a complete, runnable Idle RPG Flutter/Flame project from a
natural-language prompt in a single command:

  1. Generates an Idle RPG design document (via Ollama when available,
     or a deterministic template fallback when offline).
  2. Scaffolds a Flutter/Flame project implementing core Idle RPG mechanics.
  3. Packages everything as a ZIP at --out.

Usage
-----
    idle-rpg-gen --prompt "A dark fantasy idle RPG set in a cursed kingdom" \\
                 --out my_idle_rpg.zip

    # Offline / deterministic (no Ollama required):
    idle-rpg-gen --prompt "space colony idle RPG" --out game.zip --seed 42

    # Specify Ollama model:
    idle-rpg-gen --prompt "sci-fi idle RPG" --out game.zip \\
                 --ollama-model qwen2.5-coder:7b

Prerequisites
-------------
    pip install -e ".[ollama]"
    # Flutter SDK must be installed to run the generated project.
"""

import argparse
import sys

from colorama import Fore, Style, init

init(autoreset=True)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="idle-rpg-gen",
        description="Aibase – One-Shot Idle RPG Game Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  idle-rpg-gen --prompt "A dark fantasy idle RPG" --out my_game.zip
  idle-rpg-gen --prompt "sci-fi space colony RPG" --out game.zip --seed 42
  idle-rpg-gen --prompt "cursed kingdom" --out game.zip \\
      --ollama-model qwen2.5-coder:7b --design-doc-format md
        """,
    )

    # Required
    parser.add_argument("--prompt", required=True, help="Natural-language Idle RPG description")
    parser.add_argument("--out", required=True, help="Output ZIP file path")

    # Optional generation flags
    parser.add_argument("--platform", default="android",
                        choices=["android", "android+ios"],
                        help="Target platform (default: android)")
    parser.add_argument("--scope", default="prototype",
                        choices=["prototype", "vertical-slice"],
                        help="Project scope (default: prototype)")

    # Design doc format
    parser.add_argument("--design-doc-format", dest="design_doc_format",
                        choices=["json", "md"], default="json",
                        help="Design document output format (default: json)")
    parser.add_argument("--design-doc-path", dest="design_doc_path",
                        help="Path inside the project ZIP for the design doc")

    # Ollama flags
    parser.add_argument("--ollama-base-url", dest="ollama_base_url",
                        default="http://localhost:11434",
                        help="Ollama server base URL (default: http://localhost:11434)")
    parser.add_argument("--ollama-model", dest="ollama_model",
                        default="qwen2.5-coder:7b",
                        help="Ollama model for design doc (default: qwen2.5-coder:7b)")
    parser.add_argument("--ollama-temperature", dest="ollama_temperature", type=float,
                        help="Sampling temperature for design doc generation")
    parser.add_argument("--ollama-max-tokens", dest="ollama_max_tokens", type=int,
                        help="Max tokens for design doc generation")
    parser.add_argument("--ollama-timeout", dest="ollama_timeout", type=int,
                        help="Request timeout for design doc generation (seconds)")

    # Seed for deterministic offline generation
    parser.add_argument("--seed", dest="seed", type=int,
                        help="RNG seed for deterministic offline content (no Ollama required)")

    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    print(f"{Fore.CYAN}{'='*70}")
    print(f"{Fore.CYAN}Aibase – One-Shot Idle RPG Game Generator")
    print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}\n")
    print(f"  Prompt : {args.prompt}")
    print(f"  Output : {args.out}\n")

    from orchestrator.orchestrator import Orchestrator

    orchestrator = Orchestrator(interactive=False)
    try:
        orchestrator.run(
            prompt=args.prompt,
            output_zip=args.out,
            platform=args.platform,
            scope=args.scope,
            design_doc_format=args.design_doc_format,
            design_doc_path=args.design_doc_path,
            ollama_base_url=args.ollama_base_url,
            ollama_model=args.ollama_model,
            ollama_temperature=args.ollama_temperature,
            ollama_max_tokens=args.ollama_max_tokens,
            ollama_timeout=args.ollama_timeout,
            ollama_seed=args.seed,
            idle_rpg=True,
            seed=args.seed,
        )
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Cancelled.{Style.RESET_ALL}")
        sys.exit(0)
    except Exception as exc:
        print(f"{Fore.RED}Error: {exc}{Style.RESET_ALL}")
        sys.exit(1)

    print(f"\n{Fore.GREEN}✓ Idle RPG project generated!{Style.RESET_ALL}")
    print(f"  ZIP: {args.out}")
    print("  Next steps:")
    print("    1. Unzip the file")
    print("    2. cd <project-folder>")
    print("    3. flutter pub get")
    print("    4. flutter run\n")


if __name__ == "__main__":
    main()
