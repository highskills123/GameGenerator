# Quick Start – GameGenerator

Generate a complete, runnable Flutter/Flame game from a single prompt in minutes.

---

## 📋 Prerequisites (one-time setup)

| # | What | Download |
|---|------|---------|
| 1 | **Python 3.9+** | https://www.python.org/downloads/ |
| 2 | **Flutter SDK ≥ 3.10** | https://docs.flutter.dev/get-started/install |
| 3 | **Ollama** *(optional – for AI-enhanced content)* | https://ollama.com |

> **Windows tip:** when installing Python, tick ☑ "Add Python to PATH" in the installer.

---

## 📥 Step 1 — Get the code

**Option A — Download ZIP (easiest, no git needed):**

1. Go to https://github.com/highskills123/GameGenerator
2. Click **Code → Download ZIP**
3. Extract the ZIP to a folder (e.g. `C:\Users\you\GameGenerator`)
4. Open a terminal and `cd` into that folder:
   ```
   cd C:\Users\you\GameGenerator
   ```
   > **Tip (Windows):** Open File Explorer, navigate into the folder, click the address bar, type `cmd`, press Enter.

**Option B — git clone:**
```bash
git clone https://github.com/highskills123/GameGenerator.git
cd GameGenerator
```

---

## 📦 Step 2 — Install Python dependencies

```bash
pip install -e .
```

To enable AI-enhanced content with Ollama:
```bash
pip install -e ".[ollama]"
```

You only need to do this once.

---

## 🚀 Step 3 — Generate your game

### Offline (no AI, works immediately)

```bash
# Top-down space shooter
gamegen --prompt "top down space shooter with asteroids" --out shooter.zip

# Idle RPG (template-based content, no Ollama needed)
idle-rpg-gen --prompt "A dark fantasy idle RPG in a cursed kingdom" --out my_game.zip
```

### With AI-enhanced content (requires Ollama)

```bash
# 1. Pull the AI model (one-time, ~4 GB)
ollama pull qwen2.5-coder:7b

# 2. Start Ollama
ollama serve

# 3. Generate with AI content
idle-rpg-gen --prompt "A sci-fi space colony idle RPG" \
             --out space_colony.zip \
             --ollama-model qwen2.5-coder:7b
```

---

## 📱 Step 4 — Run the game on Android

```bash
# Unzip the generated project
unzip my_game.zip -d my_game
cd my_game

# Install Flutter packages
flutter pub get

# Connect an Android device (or start an emulator) and run
flutter run
```

The generated project includes **all required Android files** so `flutter run`
works out of the box — no extra Android setup needed.

---

## 💡 Common commands

| What you want | Command |
|--------------|---------|
| Top-down shooter | `gamegen --prompt "space shooter" --out game.zip` |
| Idle RPG (offline) | `idle-rpg-gen --prompt "idle RPG with upgrades" --out game.zip` |
| Idle RPG with AI content | `idle-rpg-gen --prompt "..." --out game.zip --ollama-model qwen2.5-coder:7b` |
| Repeatable / deterministic | Add `--seed 42` to any command |
| See all options | `gamegen --help` or `idle-rpg-gen --help` |

---

## 🛠️ Troubleshooting

| Problem | Fix |
|---------|-----|
| `gamegen: command not found` | Run `pip install -e .` first, or use `python gamegen.py` |
| `flutter: command not found` | Install Flutter SDK from https://docs.flutter.dev/get-started/install |
| `Cannot connect to Ollama` | Run `ollama serve` (or skip `--ollama-model` to use offline mode) |
| `Model not found` | Run `ollama pull qwen2.5-coder:7b` |
| `pip install` fails | Make sure Python 3.9+ is installed and on PATH |

---

## 📖 More

See the full [README.md](README.md) for a complete CLI reference and list of all generated project features.

