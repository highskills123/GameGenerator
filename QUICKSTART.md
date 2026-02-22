# Quick Start Guide

## 📋 Prerequisites (one-time setup)

Before anything else, make sure you have these three things installed:

| # | What | Download |
|---|---|---|
| 1 | **Python 3.9+** | https://www.python.org/downloads/ |
| 2 | **Ollama** (runs AI models locally, free) | https://ollama.com |
| 3 | **pip** (comes with Python) | — |

> **Windows tip:** when installing Python, tick ☑ "Add Python to PATH" in the installer.

---

## 📥 Step 1 — Get the code

**Option A — Download ZIP (easiest, no git needed):**  
👉 **https://github.com/highskills123/Aibase/archive/refs/heads/copilot/fix-ollama-integration.zip**

1. Click the link above — a ZIP file downloads
2. Right-click the ZIP → **Extract All** → choose a folder (e.g. `C:\Users\you\Aibase`)
3. Open **Command Prompt** (Windows) or **Terminal** (Mac/Linux) and `cd` into the extracted folder:
   ```
   cd C:\Users\you\Aibase\Aibase-copilot-fix-ollama-integration
   ```
   > **Tip (Windows):** Open File Explorer, navigate into the Aibase folder, click the address bar, type `cmd`, press Enter — this opens Command Prompt already in the right folder.

**Option B — git clone:**
```
git clone https://github.com/highskills123/Aibase.git
cd Aibase
git checkout copilot/fix-ollama-integration
```

---

## 📦 Step 2 — Install Python dependencies

```
pip install -r requirements.txt
```

You only need to do this once.

---

## 🚀 Step 3 — Start everything

### Recommended: one command does it all

```
python startollamaserver.py
```

This single command:
1. **Starts `ollama serve`** in the background (skips this if Ollama is already running)
2. **Waits** until Ollama is ready
3. **Pulls the AI model** automatically if you don't have it yet (`qwen2.5-coder:7b`, ~4 GB on first run)
4. **Starts the Aibase web server** and opens a public **HTTPS URL** via ngrok

The output will look like this:

```
  ✓  Ollama is ready
  ✓  Model 'qwen2.5-coder:7b' is available

  🌍 Public URL:   https://abc123.ngrok-free.app
  Share this link with anyone — no router setup needed!

  This computer:   http://localhost:5000/
  Local network:   http://192.168.1.42:5000/
```

Open one of those URLs in your browser and start generating code!

### Useful flags

| Command | What it does |
|---|---|
| `python startollamaserver.py` | Full stack — Ollama + HTTPS tunnel (default) |
| `python startollamaserver.py --no-ngrok` | Local only — no public URL |
| `python startollamaserver.py --port 8080` | Use a different port |
| `python startollamaserver.py --no-pull` | Skip the automatic model download |

---

## 🔑 Step 4 — (Optional) Set up ngrok for a permanent URL

By default ngrok gives you a random URL that changes every time. To get a **fixed URL** that stays the same:

1. Sign up free at https://ngrok.com
2. Copy your authtoken from https://dashboard.ngrok.com/get-started/your-authtoken
3. Copy `.env.example` to `.env`:
   - **Windows:** `copy .env.example .env`
   - **Mac/Linux:** `cp .env.example .env`
4. Open `.env` in a text editor and fill in:
   ```
   NGROK_AUTHTOKEN=paste_your_token_here
   ```

> Once you have an authtoken, ngrok also lets you reserve a **static domain** (free tier: 1 domain).  
> Add it to `.env` as `NGROK_DOMAIN=your-reserved-domain.ngrok-free.app` and the URL will never change.

---

## 🌐 Step 5 — Use the web UI

Open the URL printed by the launcher in any browser.

- Type a description of what you want to build
- Pick a language from the dropdown (Python, Flutter, React Native, JavaScript, …)
- Click **Generate Code**
- Copy or download the result

---

## ⚠️ Keep the terminal open!

The public link **only works while the server is running**.  
If you close the terminal window, the link returns a 404 error.  
Just run `python startollamaserver.py` again to bring it back.

---

## 🛠️ Troubleshooting

| Problem | Fix |
|---|---|
| `Cannot connect to Ollama` | Ollama is not running — `startollamaserver.py` starts it for you, but if you see this in a manual run: `ollama serve` |
| `Model not found` / 503 from API | Pull the model: `ollama pull qwen2.5-coder:7b` |
| `pip install` fails | Make sure Python is installed and on PATH, then retry |
| Friend sees 404 on ngrok URL | Your terminal was closed — re-run `python startollamaserver.py` |
| Can't reach local IP from other device | Make sure both devices are on the same Wi-Fi; allow port 5000 in your firewall |
| Want a different AI model | Set `OLLAMA_MODEL=llama3` in `.env`, then `ollama pull llama3` |

---

## 💡 Usage examples

### Web UI
Just open the browser URL and describe what you want.

### Command line (quick single generation)
```bash
python aibase.py -d "create a function that checks if a number is prime"
python aibase.py -d "create a Flutter login screen with email/password" -l flutter
python aibase.py -d "create a REST API endpoint for user signup" -l javascript -o signup.js
```

### Programmatic (Python)
```python
from aibase import AibaseTranslator

translator = AibaseTranslator()
code = translator.translate("create a binary search function", "python")
print(code)
```

### REST API
```bash
curl -X POST http://localhost:5000/api/translate \
  -H "Content-Type: application/json" \
  -d '{"description": "create a hello world function", "language": "python"}'
```

---

## Next steps

- See `README.md` for the full feature list and API docs
- See `API.md` for all REST endpoints
- Check `examples/` for Flutter and React Native examples

## Next steps

- See `README.md` for the full feature list and API docs
- See `API.md` for all REST endpoints
- Check `examples/` for Flutter and React Native examples
