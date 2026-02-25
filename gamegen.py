#!/usr/bin/env python3
"""
gamegen.py – Standalone CLI entry point for the Aibase Flutter/Flame Game Generator.

This entry point complements the existing ``aibase.py --generate-game`` flag
and exposes the full orchestrator pipeline with constraint resolution,
validation, and auto-fix.

Usage
-----
    python gamegen.py --prompt "top down space shooter" --out game.zip
    python gamegen.py --prompt "idle RPG with upgrades" \\
        --assets-dir "C:\\\\Users\\\\me\\\\Desktop\\\\MyAssets" \\
        --out my_game.zip --platform android --scope vertical-slice --auto-fix

    # Interactive constraint prompts
    python gamegen.py --prompt "space shooter" --out game.zip --interactive

    # AI-enhanced spec via Ollama
    python gamegen.py --prompt "..." --out game.zip --model qwen2.5-coder:7b
"""

import argparse
import sys

from colorama import Fore, Style, init

init(autoreset=True)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gamegen",
        description="Aibase – Flutter/Flame Game Generator",
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

    # Optional generation flags
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
    parser.add_argument("--smoke-test", dest="smoke_test", action="store_true",
                        help="Run an optional smoke test after validation: flutter test or flutter build apk --debug (opt-in)")
    parser.add_argument("--smoke-test-mode", dest="smoke_test_mode",
                        choices=["test", "build"], default="test",
                        help="Smoke test command: 'test' (flutter test) or 'build' (flutter build apk --debug) (default: test)")

    # UX flags
    parser.add_argument("--interactive", action="store_true",
                        help="Prompt for constraint questions before generating")

    # Ollama / AI flags
    parser.add_argument("--model", help="Ollama model for AI-enhanced spec")
    parser.add_argument("--temperature", type=float,
                        help="Ollama sampling temperature (0.0–1.0)")
    parser.add_argument("--max-tokens", dest="max_tokens", type=int,
                        help="Max tokens for Ollama generation")
    parser.add_argument("--timeout", type=int,
                        help="Ollama request timeout in seconds")

    # Design doc flags
    parser.add_argument("--design-doc", dest="design_doc", action="store_true",
                        help="Generate an Idle RPG design document via Ollama")
    parser.add_argument("--design-doc-format", dest="design_doc_format",
                        choices=["json", "md"], default="json",
                        help="Design document output format (default: json)")
    parser.add_argument("--design-doc-path", dest="design_doc_path",
                        help="Path inside the project ZIP for the design doc "
                             "(default: assets/design/design.json or DESIGN.md)")
    parser.add_argument("--ollama-base-url", dest="ollama_base_url",
                        default="http://localhost:11434",
                        help="Ollama server base URL (default: http://localhost:11434)")
    parser.add_argument("--ollama-model", dest="ollama_model",
                        default="qwen2.5-coder:7b",
                        help="Ollama model for design doc generation (default: qwen2.5-coder:7b)")
    parser.add_argument("--ollama-temperature", dest="ollama_temperature", type=float,
                        help="Sampling temperature for design doc generation")
    parser.add_argument("--ollama-max-tokens", dest="ollama_max_tokens", type=int,
                        help="Max tokens for design doc generation")
    parser.add_argument("--ollama-timeout", dest="ollama_timeout", type=int,
                        help="Request timeout for design doc generation (seconds)")
    parser.add_argument("--ollama-seed", dest="ollama_seed", type=int,
                        help="Random seed for design doc generation")

    # One-shot Idle RPG generator
    parser.add_argument("--idle-rpg", dest="idle_rpg", action="store_true",
                        help=(
                            "One-shot Idle RPG generator: generate design doc + "
                            "complete Flutter/Flame project end-to-end. "
                            "Uses Ollama when available; falls back to a template "
                            "design doc so the command works fully offline."
                        ))
    parser.add_argument("--seed", dest="seed", type=int,
                        help="Global RNG seed for deterministic offline content generation")

    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    print(f"{Fore.CYAN}{'='*70}")
    print(f"{Fore.CYAN}Aibase – Flutter/Flame Game Generator")
    if args.idle_rpg:
        print(f"{Fore.CYAN}Mode: One-Shot Idle RPG Generator")
    print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}\n")

    # Optional Ollama translator
    translator = None
    if args.model:
        try:
            from game_generator.ai.translator import OllamaTranslator
            translator = OllamaTranslator(
                model=args.model,
                temperature=args.temperature,
                max_tokens=args.max_tokens,
                timeout=args.timeout,
            )
        except Exception:
            print(
                f"{Fore.YELLOW}[WARNING] Could not initialise Ollama translator; "
                f"falling back to heuristic spec.{Style.RESET_ALL}"
            )

    from orchestrator.orchestrator import Orchestrator

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
            smoke_test=args.smoke_test,
            smoke_test_mode=args.smoke_test_mode,
            translator=translator,
            constraint_overrides={
                "art_style": args.art_style,
                "online": args.online if args.online else None,
            },
            design_doc=args.design_doc,
            design_doc_format=args.design_doc_format,
            design_doc_path=args.design_doc_path,
            ollama_base_url=args.ollama_base_url,
            ollama_model=args.ollama_model,
            ollama_temperature=args.ollama_temperature,
            ollama_max_tokens=args.ollama_max_tokens,
            ollama_timeout=args.ollama_timeout,
            ollama_seed=args.ollama_seed,
            idle_rpg=args.idle_rpg,
            seed=args.seed,
        )
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Cancelled.{Style.RESET_ALL}")
        sys.exit(0)
    except Exception as exc:
        print(f"{Fore.RED}Error: {exc}{Style.RESET_ALL}")
        sys.exit(1)


if __name__ == "__main__":
    main()
