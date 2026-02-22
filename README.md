# Aibase

![Flutter](https://img.shields.io/badge/Flutter-02569B?style=flat&logo=flutter&logoColor=white)
![React Native](https://img.shields.io/badge/React_Native-20232A?style=flat&logo=react&logoColor=61DAFB)
![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=flat&logo=javascript&logoColor=black)
![License](https://img.shields.io/badge/License-MIT-green.svg)

AI-powered Natural Language to Code Translator - Transform your ideas into working code instantly!

> **📥 Clone / Download the project:**
> ```
> git clone https://github.com/highskills123/Aibase.git
> cd Aibase
> git checkout copilot/resolve-merge-conflicts-pr-12
> ```
> Or download the latest ZIP directly (no git needed):  
> **https://github.com/highskills123/Aibase/archive/refs/heads/copilot/resolve-merge-conflicts-pr-12.zip**

## Overview

Aibase is an intelligent code generator that translates natural language descriptions into working code in multiple programming languages and mobile frameworks. Simply describe what you want in plain English, and Aibase will generate clean, efficient code for you.

## Features

- 🚀 **Multi-Language Support**: Generate code in Python, JavaScript, Java, C++, Go, Rust, TypeScript, and more
- 📱 **Mobile Framework Support**: Generate Flutter widgets and React Native components
- 💬 **Natural Language Input**: Describe what you want in plain English
- 🎯 **Interactive & CLI Modes**: Use interactively or integrate into your workflow
- 🌍 **Web UI**: Responsive browser interface — works on desktop, tablet, and phone
- 📝 **Smart Code Generation**: Produces clean, well-commented, production-ready code
- ⚡ **Fast & Efficient**: Powered by local Ollama models (free, no API key required)
- 🌐 **REST API**: Full-featured API for integrations
- 🤖 **Bot-Ready**: Easy to integrate with Discord, Telegram, Slack, and other platforms

## Supported Languages

### General Purpose
Python · JavaScript · TypeScript · Java · C++ · C# · Go · Rust · PHP · Ruby · Swift · Kotlin

### Mobile / Flutter
Flutter/Dart · Flutter Widget · Dart · React Native · React Native Component

### Game Dev (Flame)
Flame · Flame Complete Game · Flame Game Component · Game Sprite · Game Animation · Game Tilemap

### Mobile Frameworks
- **Flutter/Dart**: Generate complete Flutter widgets (StatelessWidget, StatefulWidget)
- **React Native**: Generate modern React Native components with hooks

## Installation

1. Clone the repository:
```bash
git clone https://github.com/highskills123/Aibase.git
cd Aibase
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install and start Ollama (free, no API key required):
```bash
# Install Ollama from https://ollama.com
# Then pull the default model:
ollama pull qwen2.5-coder:7b
```

4. (Optional) Copy `.env.example` to `.env` to customise settings:
```bash
cp .env.example .env
```

## Usage

### Web UI

Start the server and open the web interface in any browser — including on mobile:

```bash
python api_server.py
```

The startup output shows you exactly which URLs to use:

```
  This computer:  http://localhost:5000/
  Local network:  http://192.168.1.42:5000/
  (anyone on your Wi-Fi/LAN can use this URL)
  Public URL:     (ngrok not active — run with --ngrok to enable)
```

- **Same computer** → `http://localhost:5000/`
- **Other devices on the same Wi-Fi or LAN** → `http://<your-local-IP>:5000/`
- **Anyone on the internet** → see [Sharing over the internet](#sharing-over-the-internet) below

Once the page loads:
- Type a description of what you want to build
- Choose a target language from the dropdown
- Toggle comments on or off
- Click **Generate Code**
- Copy the result to your clipboard or download it as a file

### Sharing over the internet

`localhost` is only reachable from **your own machine**. The easiest way to share Aibase with anyone, anywhere is the built-in `--ngrok` flag:

**Option A — built-in ngrok tunnel (easiest):**
```bash
# Install ngrok support (one-time)
pip install pyngrok

# Start server with automatic public tunnel
python api_server.py --ngrok
```

The startup banner shows a shareable public link:

```
  🌍 Public URL:   https://abc123.ngrok-free.app
  Share this link with anyone — no router setup needed!
```

> **Optional:** Sign up free at https://ngrok.com and add `NGROK_AUTHTOKEN=your_token` to
> `.env` to remove the 2-hour session limit.

**Option B — router port forwarding:**
1. Log in to your router's admin page (usually `http://192.168.1.1`)
2. Add a port-forwarding rule: external port `<PORT>` → your computer's local IP, port `<PORT>`
   (replace `<PORT>` with your configured port, default `5000`)
3. Find your public IP at https://whatismyip.com and share `http://<public-IP>:<PORT>/`

> **Note:** When sharing publicly, anyone with the link can generate code using your
> machine's resources. Stop the server with `Ctrl+C` when you are done.

### Interactive Mode

Run Aibase in interactive mode for a conversational experience:

```bash
python aibase.py
```

### Direct Command Line

Generate code directly from the command line:

```bash
# Generate Python code
python aibase.py -d "create a function that sorts a list using quicksort"

# Generate JavaScript code
python aibase.py -d "create a REST API endpoint for user authentication" -l javascript

# Save output to file
python aibase.py -d "create a binary search tree class" -l python -o bst.py

# Generate without comments
python aibase.py -d "create a fibonacci function" --no-comments
```

### Programmatic Usage

Use Aibase in your Python projects:

```python
from aibase import AibaseTranslator

# Initialize translator
translator = AibaseTranslator()

# Generate code
code = translator.translate(
    description="Create a function that calculates factorial",
    target_language="python",
    include_comments=True
)

print(code)
```

### Mobile Framework Quick Start

#### Generate Flutter Widgets

```bash
# Generate a Flutter counter widget
python aibase.py -d "create a Flutter counter StatefulWidget with increment and decrement buttons" -l flutter-widget -o counter.dart

# Generate a Flutter login form
python aibase.py -d "create a Flutter login form with email and password validation" -l flutter-widget -o login.dart

# Generate a Flutter list view
python aibase.py -d "create a Flutter ListView displaying products with images and titles" -l flutter-widget -o product_list.dart
```

#### Generate React Native Components

```bash
# Generate a React Native component
python aibase.py -d "create a React Native button component with TouchableOpacity and custom styling" -l react-native-component -o Button.js

# Generate a React Native screen
python aibase.py -d "create a React Native profile screen with avatar and user info using hooks" -l react-native-component -o ProfileScreen.js

# Generate a React Native list
python aibase.py -d "create a React Native FlatList displaying user posts" -l react-native-component -o PostList.js
```

#### Using the API for Mobile

```python
import requests

# Generate Flutter widget via API
response = requests.post(
    "http://localhost:5000/api/translate",
    json={
        "description": "create a Flutter card widget with image and title",
        "language": "flutter-widget"
    }
)

code = response.json()["code"]
with open("card_widget.dart", "w") as f:
    f.write(code)
```

## Examples

### Code Examples

Check out `examples.py` for more usage examples:

```bash
python examples.py
```

### Mobile Framework Examples

Explore comprehensive examples:

- **Flutter Examples**: [`examples/flutter/`](examples/flutter/) - 5+ complete Flutter widget examples
- **React Native Examples**: [`examples/react-native/`](examples/react-native/) - 5+ complete React Native component examples

Each example includes:
- Complete, runnable code
- Generation commands
- Usage instructions
- Feature descriptions

## Documentation

### Getting Started Guides
- 📱 [Flutter Getting Started](docs/flutter-getting-started.md) - Complete guide for generating Flutter code
- ⚛️ [React Native Getting Started](docs/react-native-getting-started.md) - Complete guide for generating React Native code
- ⚙️ [Configuration Guide](docs/configuration-guide.md) - Detailed configuration options
- 📚 [Best Practices](docs/best-practices.md) - Tips for generating high-quality code

### API Documentation
- 🌐 [API Usage for Mobile Frameworks](docs/api-mobile-frameworks.md) - REST API examples and integration

### Developer Documentation
- 🏗️ [Architecture Overview](docs/architecture-overview.md) - System architecture and design
- 🔧 [Extending Generators](docs/extending-generators.md) - How to add custom generators
- 🤝 [Contributing Guide](docs/contributing-mobile.md) - How to contribute

### Tutorials
- 🎓 [Generate Your First Flutter Widget](docs/tutorials/flutter-first-widget.md) - Step-by-step tutorial
- 🎓 [Generate Your First React Native Component](docs/tutorials/react-native-first-component.md) - Step-by-step tutorial
- 🔍 [Troubleshooting Guide](docs/tutorials/troubleshooting.md) - Common issues and solutions

## How It Works

1. **Input**: You provide a natural language description of what you want
2. **Processing**: Aibase sends your description to a local Ollama model
3. **Generation**: The AI generates clean, efficient code in your target language
4. **Output**: You receive production-ready code with helpful comments

## Use Cases

- **Rapid Prototyping**: Quickly generate boilerplate code and functions
- **Mobile App Development**: Generate Flutter widgets and React Native components instantly
- **Learning**: Understand how to implement algorithms and UI patterns in different languages
- **Code Translation**: Convert logic from one language to another
- **Documentation**: Generate code examples from specifications
- **Problem Solving**: Get implementation ideas for complex problems
- **Bot Development**: Integrate code generation into Discord, Telegram, or Slack bots
- **API Integration**: Use the REST API in your applications and services
- **UI Development**: Generate mobile screens, forms, lists, and navigation flows
- **Cross-Platform Development**: Create components for both Flutter and React Native

## API Server

Aibase includes a REST API server for easy integration:

```bash
# Start the API server
python api_server.py

# Custom host and port
python api_server.py --host 0.0.0.0 --port 8080
```

### API Endpoints

- `GET /` - Web UI
- `GET /api/info` - API information (JSON)
- `GET /api/health` - Health check
- `GET /api/languages` - List supported languages
- `POST /api/translate` - Translate natural language to code

### API Example

```python
import requests

response = requests.post(
    "http://localhost:5000/api/translate",
    json={
        "description": "create a function that reverses a string",
        "language": "python"
    }
)

result = response.json()
if result["success"]:
    print(result["code"])
```

See [API.md](API.md) for complete API documentation.

## Building Bots

Aibase is perfect for building code generation bots! We include a Discord bot example:

```bash
# Set up Discord bot token in .env
DISCORD_BOT_TOKEN=your_token_here

# Start the API server
python api_server.py

# In another terminal, start the bot
python discord_bot.py
```

The bot supports commands like:
- `!code create a function that checks if a number is prime`
- `!code javascript create an async fetch function`
- `!languages` - List supported languages

See [discord_bot.py](discord_bot.py) for the implementation and [API.md](API.md) for examples with Telegram and Slack.

## Requirements

- Python 3.7+
- [Ollama](https://ollama.com) running locally with `qwen2.5-coder:7b` pulled
- Dependencies listed in `requirements.txt`

## Configuration

Copy `.env.example` to `.env` and adjust as needed:

```
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5-coder:7b
```

## Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest new features
- Submit pull requests
- Improve documentation

## License

This project is open source and available under the MIT License.

## Disclaimer

Aibase runs fully locally using [Ollama](https://ollama.com) — no API key required, no external services.

## Support

For issues, questions, or suggestions, please open an issue on GitHub.

---

**Made with ❤️ by the Aibase team**
