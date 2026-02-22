# Quick Start Guide

## 📥 Get the code first

```
git clone https://github.com/highskills123/Aibase.git
cd Aibase
```

No git? Download the ZIP instead:  
👉 **https://github.com/highskills123/Aibase/archive/refs/heads/main.zip**  
(extract it, then `cd` into the `Aibase-main` folder)

---

## ⚡ Share with a friend — quick steps

### Step 0 — Open Command Prompt IN the Aibase folder

**If you used git clone:**
```
cd Aibase
```

**If you downloaded the ZIP** (extracted to e.g. `Downloads\Aibase-main`):
```
cd C:\Users\high\Downloads\Aibase-main
```

> **Tip:** You can also open File Explorer, navigate into the Aibase folder,
> click the address bar, type `cmd`, and press Enter — this opens Command Prompt
> already in the right folder.

### Step 1 — Create your `.env` file

Copy the example file and open it in Notepad (or any text editor):

**Windows CMD:**
```
copy .env.example .env
notepad .env
```

**Mac/Linux:**
```bash
cp .env.example .env
nano .env   # or open with any editor
```

Uncomment and fill in these two lines:
```
NGROK_AUTHTOKEN=your_authtoken_here
NGROK_DOMAIN=costless-dorthy-unmeanderingly.ngrok-free.dev
```

> Get your free authtoken at https://dashboard.ngrok.com/get-started/your-authtoken

### Step 2 — Start the server

Run this command in Command Prompt (Windows) or Terminal (Mac/Linux):

```
python api_server.py --ngrok
```

That's it — works on Windows, Mac, and Linux without any extra scripts.

> Optional shortcuts if you prefer:
> - **Mac/Linux:** `./start.sh --ngrok`
> - **Windows (convenience script):** `run.bat --ngrok`

The startup output will show:
```
  🌍 Public URL:   https://costless-dorthy-unmeanderingly.ngrok-free.dev
  Share this link with anyone — no router setup needed!
```

Send that link to your friend and they can use the full Aibase UI in their browser.

> ⚠️ **Windows note:** Do **not** try to set variables like `NGROK_DOMAIN=value` directly
> in the command prompt — that syntax only works on Linux/Mac. Use the `.env` file instead,
> as shown above.

---

## Setup (One-time)

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Install Ollama and pull the default model (free, no API key needed):**
   ```bash
   # Install Ollama from https://ollama.com, then:
   ollama pull qwen2.5-coder:7b
   ```

3. **(Optional) Configure settings via `.env`:**
   ```bash
   cp .env.example .env
   # Edit .env to change the model or Ollama URL
   ```

## Accessing the Web UI

After running `python api_server.py`, look at the startup output:

```
  This computer:  http://localhost:5000/
  Local network:  http://192.168.1.42:5000/
```

| Who needs access | URL to use |
|---|---|
| You (same computer) | `http://localhost:5000/` |
| Friends on the same Wi-Fi/LAN | `http://<local IP shown above>:5000/` |
| Anyone on the internet | Start with `--ngrok` flag (see below) |

## Sharing with friends over the internet

The easiest way to let a friend access your Aibase from anywhere is the built-in `--ngrok` flag:

```bash
# Install ngrok support (one-time)
pip install pyngrok

# Start the server with a public tunnel
python api_server.py --ngrok
```

The startup output will show a link you can send to your friend:

```
  🌍 Public URL:   https://abc123.ngrok-free.app
  Share this link with anyone — no router setup needed!
```

That's it — your friend can open the link in any browser, including on their phone.

> **Optional:** Create a free account at https://ngrok.com and add your authtoken to `.env`:
> ```
> NGROK_AUTHTOKEN=your_token_here
> ```
> This removes the 2-hour session limit on the free tier.

## Usage Examples

### Interactive Mode (Recommended for Beginners)
```bash
python aibase.py
```
Then follow the prompts to describe your code and select a language.

### Command Line Examples

**Generate a Python function:**
```bash
python aibase.py -d "create a function that checks if a string is a palindrome"
```

**Generate JavaScript code:**
```bash
python aibase.py -d "create an async function to fetch data from an API" -l javascript
```

**Save to a file:**
```bash
python aibase.py -d "create a class for a stack data structure" -o stack.py
```

**Generate without comments:**
```bash
python aibase.py -d "create a merge sort function" --no-comments
```

## Common Use Cases

### 1. Algorithm Implementation
```bash
python aibase.py -d "implement binary search algorithm"
```

### 2. Data Structure
```bash
python aibase.py -d "create a linked list class with insert and delete methods" -l python
```

### 3. Utility Functions
```bash
python aibase.py -d "create a function to validate email addresses using regex"
```

### 4. API Endpoints
```bash
python aibase.py -d "create an Express.js endpoint for user registration" -l javascript
```

### 5. Database Queries
```bash
python aibase.py -d "create a SQL query to find top 10 customers by purchase amount"
```

## Programmatic Usage

```python
from aibase import AibaseTranslator

# Initialize
translator = AibaseTranslator()

# Generate code
code = translator.translate(
    description="Create a function that finds the longest common substring",
    target_language="python"
)

# Use the generated code
print(code)
```

## Tips for Best Results

1. **Be Specific**: The more detailed your description, the better the output
   - ❌ "create a function"
   - ✅ "create a function that takes a list of integers and returns the sum of even numbers"

2. **Specify Requirements**: Include any constraints or requirements
   - ✅ "create a REST API endpoint with error handling and input validation"

3. **Mention Data Structures**: If you need specific data structures, mention them
   - ✅ "create a function using a hash map to find duplicate elements"

4. **Include Edge Cases**: Mention important edge cases
   - ✅ "create a function that handles empty strings and null values"

## Troubleshooting

**Other devices can't connect to the server**
- Make sure they are using your **local IP** (e.g. `http://192.168.1.42:5000/`), not `localhost`
- `localhost` only works on the computer that is running the server
- Check that your firewall allows inbound connections on port 5000:
  - Windows: add a rule in Windows Defender Firewall
  - macOS: System Settings → Network → Firewall
  - Linux: `sudo ufw allow 5000/tcp`
- For access from outside your home network, use ngrok (`ngrok http 5000`)

**Error: Cannot connect to Ollama**
- Make sure Ollama is running: `ollama serve`
- Make sure you've pulled the model: `ollama pull qwen2.5-coder:7b`
- Check that `OLLAMA_BASE_URL` points to the right address (default: `http://localhost:11434`)

**Error: Unsupported language**
- Check the list of supported languages in README.md
- Use the exact language name (e.g., "javascript" not "js")

**Generated code is not what you expected**
- Try being more specific in your description
- Break complex requests into smaller parts
- Use the interactive mode to iterate on your request

## Next Steps

- Check out `examples.py` for more code examples
- Read the full README.md for detailed documentation
- Experiment with different languages and descriptions
