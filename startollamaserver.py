#!/usr/bin/env python3
"""
startollamaserver.py — One-command Aibase launcher
====================================================
Does everything in the right order so you can go from zero to a live
HTTPS code-generation endpoint in one step:

  1. Start Ollama in the background (skipped if already running)
  2. Wait until Ollama is ready to accept requests
  3. Pull the configured model if it is not already downloaded
  4. Start the Aibase API server with a public HTTPS tunnel (--ngrok)

Usage
-----
  python startollamaserver.py                # uses defaults
  python startollamaserver.py --port 8080   # different port
  python startollamaserver.py --no-ngrok    # local-only (no HTTPS tunnel)
  python startollamaserver.py --no-pull     # skip model pull check

Configuration (via .env or environment variables)
--------------------------------------------------
  OLLAMA_BASE_URL   Ollama base URL  (default: http://localhost:11434)
  OLLAMA_MODEL      Model to use     (default: qwen2.5-coder:7b)
  NGROK_AUTHTOKEN   ngrok auth token (optional, extends session limit)
  NGROK_DOMAIN      Static ngrok domain (optional)
"""

import argparse
import atexit
import os
import subprocess
import sys
import time

import requests
from dotenv import load_dotenv

load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")

# ── colour helpers ────────────────────────────────────────────────────────────
try:
    from colorama import Fore, Style, init as _colorama_init
    _colorama_init(autoreset=True)
    def _c(color, text): return f"{color}{text}{Style.RESET_ALL}"
except ImportError:
    def _c(_color, text): return text

def info(msg):  print(_c(Fore.CYAN,   f"  ℹ  {msg}"))
def ok(msg):    print(_c(Fore.GREEN,  f"  ✓  {msg}"))
def warn(msg):  print(_c(Fore.YELLOW, f"  ⚠  {msg}"))
def err(msg):   print(_c(Fore.RED,    f"  ✗  {msg}"), file=sys.stderr)
def step(n, total, msg): print(_c(Fore.YELLOW, f"\n[{n}/{total}] {msg}"))


# ── subprocess tracking ───────────────────────────────────────────────────────
_ollama_proc = None


def _cleanup():
    """Kill the Ollama subprocess we launched (if any) on exit."""
    if _ollama_proc is not None and _ollama_proc.poll() is None:
        info("Stopping Ollama subprocess…")
        _ollama_proc.terminate()
        try:
            _ollama_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            _ollama_proc.kill()


atexit.register(_cleanup)


# ── helpers ───────────────────────────────────────────────────────────────────

def _ollama_is_running():
    """Return True if Ollama is already responding at OLLAMA_BASE_URL."""
    try:
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/version", timeout=3)
        return resp.ok
    except Exception:
        return False


def _start_ollama():
    """
    Launch `ollama serve` as a background subprocess.

    Returns the Popen object, or None if the `ollama` binary is not found.
    """
    global _ollama_proc
    try:
        # On Windows, CREATE_NO_WINDOW keeps the subprocess hidden
        kwargs = {}
        if sys.platform == "win32":
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
        _ollama_proc = subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            **kwargs,
        )
        return _ollama_proc
    except FileNotFoundError:
        return None


def _wait_for_ollama(timeout=60):
    """
    Poll until Ollama is ready or *timeout* seconds have elapsed.

    Returns True if Ollama became ready, False on timeout.
    """
    deadline = time.time() + timeout
    dots = 0
    while time.time() < deadline:
        if _ollama_is_running():
            return True
        print(".", end="", flush=True)
        dots += 1
        time.sleep(1)
    if dots:
        print()
    return False


def _model_is_available():
    """Return True if OLLAMA_MODEL is already pulled in Ollama."""
    try:
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        if not resp.ok:
            return False
        models = [m.get("name", "") for m in resp.json().get("models", [])]
        model_base = OLLAMA_MODEL.split(":")[0]
        return any(
            m == OLLAMA_MODEL or m.split(":")[0] == model_base
            for m in models
        )
    except Exception:
        return False


def _pull_model():
    """
    Run `ollama pull <model>` and stream its output.

    Returns True on success, False on failure.
    """
    info(f"Pulling model '{OLLAMA_MODEL}' — this may take a few minutes on first run…")
    try:
        result = subprocess.run(
            ["ollama", "pull", OLLAMA_MODEL],
            check=False,
        )
        return result.returncode == 0
    except FileNotFoundError:
        err("'ollama' binary not found. Install Ollama from https://ollama.com")
        return False


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Start Ollama + Aibase API server with optional HTTPS tunnel",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--port", type=int, default=5000,
        help="Port for the Aibase API server (default: 5000)",
    )
    parser.add_argument(
        "--no-ngrok", dest="ngrok", action="store_false", default=True,
        help="Disable the ngrok HTTPS tunnel (local access only)",
    )
    parser.add_argument(
        "--no-pull", dest="pull", action="store_false", default=True,
        help="Skip automatic model pull if model is not found",
    )
    parser.add_argument(
        "--debug", action="store_true",
        help="Run api_server.py in debug mode",
    )
    args = parser.parse_args()

    total_steps = 4 if args.ngrok else 3

    print()
    print(_c(Fore.CYAN, "╔══════════════════════════════════════════════════════════════╗"))
    print(_c(Fore.CYAN, "║            Aibase — Full Stack Launcher                      ║"))
    print(_c(Fore.CYAN, "╚══════════════════════════════════════════════════════════════╝"))
    print()
    info(f"Ollama URL : {OLLAMA_BASE_URL}")
    info(f"Model      : {OLLAMA_MODEL}")
    info(f"API port   : {args.port}")
    info(f"HTTPS      : {'yes (ngrok)' if args.ngrok else 'no (local only)'}")

    # ── Step 1: Ollama ────────────────────────────────────────────────────────
    step(1, total_steps, "Starting Ollama…")

    if _ollama_is_running():
        ok("Ollama is already running — skipping launch")
    else:
        info("Launching 'ollama serve' in the background…")
        proc = _start_ollama()
        if proc is None:
            err(
                "'ollama' binary not found.\n"
                "  Install Ollama from https://ollama.com, then re-run this script."
            )
            sys.exit(1)

        info("Waiting for Ollama to be ready (up to 60 s)…")
        print("  ", end="", flush=True)
        if not _wait_for_ollama(timeout=60):
            err(
                "Ollama did not become ready within 60 seconds.\n"
                "  Try running 'ollama serve' manually and check for errors."
            )
            sys.exit(1)
        ok("Ollama is ready")

    # ── Step 2: Model ─────────────────────────────────────────────────────────
    step(2, total_steps, f"Checking model '{OLLAMA_MODEL}'…")

    if _model_is_available():
        ok(f"Model '{OLLAMA_MODEL}' is available")
    elif args.pull:
        if not _pull_model():
            err(
                f"Failed to pull model '{OLLAMA_MODEL}'.\n"
                f"  You can pull it manually:  ollama pull {OLLAMA_MODEL}"
            )
            sys.exit(1)
        ok(f"Model '{OLLAMA_MODEL}' pulled successfully")
    else:
        warn(
            f"Model '{OLLAMA_MODEL}' is not available and --no-pull was set.\n"
            f"  Run:  ollama pull {OLLAMA_MODEL}"
        )

    # ── Step 3: (optional) ngrok ──────────────────────────────────────────────
    if args.ngrok:
        step(3, total_steps, "ngrok HTTPS tunnel will be opened by api_server…")
        info("pyngrok is required — installing if missing…")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-q", "pyngrok"],
            check=False,
        )

    # ── Step 4: API server ────────────────────────────────────────────────────
    api_step = total_steps
    step(api_step, total_steps, "Starting Aibase API server…")
    print()

    cmd = [sys.executable, "api_server.py", "--port", str(args.port)]
    if args.ngrok:
        cmd.append("--ngrok")
    if args.debug:
        cmd.append("--debug")

    # Replace the current process with api_server so Ctrl-C is forwarded cleanly
    try:
        if sys.platform == "win32":
            # On Windows exec-style replacement isn't available; use run() instead
            result = subprocess.run(cmd)
            sys.exit(result.returncode)
        else:
            os.execv(sys.executable, cmd)
    except KeyboardInterrupt:
        print("\n\nStopped by user.")
        sys.exit(0)


if __name__ == "__main__":
    main()
