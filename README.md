# Aibase

AI-powered Natural Language to Code Translator - Transform your ideas into working code instantly!

## Overview

Aibase is an intelligent code generator that translates natural language descriptions into working code in multiple programming languages. Simply describe what you want in plain English, and Aibase will generate clean, efficient code for you.

## Features

- 🚀 **Multi-Language Support**: Generate code in Python, JavaScript, Java, C++, Go, Rust, TypeScript, and more
- 💬 **Natural Language Input**: Describe what you want in plain English
- 🎯 **Interactive & CLI Modes**: Use interactively or integrate into your workflow
- 📝 **Smart Code Generation**: Produces clean, well-commented, production-ready code
- ⚡ **Fast & Efficient**: Powered by OpenAI's GPT models
- 🌐 **REST API**: Full-featured API for integrations
- 🤖 **Bot-Ready**: Easy to integrate with Discord, Telegram, Slack, and other platforms

## Supported Languages

- Python
- JavaScript
- TypeScript
- Java
- C++
- C#
- Go
- Rust
- PHP
- Ruby
- Swift
- Kotlin

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

3. Set up your OpenAI API key:
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

## Usage

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

## Examples

Check out `examples.py` for more usage examples:

```bash
python examples.py
```

## How It Works

1. **Input**: You provide a natural language description of what you want
2. **Processing**: Aibase uses OpenAI's GPT models to understand your requirements
3. **Generation**: The AI generates clean, efficient code in your target language
4. **Output**: You receive production-ready code with helpful comments

## Use Cases

- **Rapid Prototyping**: Quickly generate boilerplate code and functions
- **Learning**: Understand how to implement algorithms in different languages
- **Code Translation**: Convert logic from one language to another
- **Documentation**: Generate code examples from specifications
- **Problem Solving**: Get implementation ideas for complex problems
- **Bot Development**: Integrate code generation into Discord, Telegram, or Slack bots
- **API Integration**: Use the REST API in your applications and services

## API Server

Aibase includes a REST API server for easy integration:

```bash
# Start the API server
python api_server.py

# Custom host and port
python api_server.py --host 0.0.0.0 --port 8080
```

### API Endpoints

- `GET /` - API information
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
- OpenAI API key
- Dependencies listed in `requirements.txt`

## Configuration

Create a `.env` file with your OpenAI API key:

```
OPENAI_API_KEY=your_openai_api_key_here
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

This tool uses OpenAI's API and requires a valid API key. API usage is subject to OpenAI's pricing and terms of service.

## Support

For issues, questions, or suggestions, please open an issue on GitHub.

---

**Made with ❤️ by the Aibase team**
