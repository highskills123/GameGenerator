# Aibase API Documentation

## Overview

Aibase provides a REST API that allows you to integrate AI-powered code generation into your applications, bots, or services.

## Base URL

```
http://localhost:5000
```

## Authentication

The API server uses a local Ollama model and requires no API key. Simply ensure Ollama is running and the model is available on the server machine.

## Endpoints

### 1. API Information

Get information about the API and available endpoints.

**Endpoint:** `GET /`

**Response:**
```json
{
  "name": "Aibase API",
  "version": "1.0.0",
  "description": "AI-powered Natural Language to Code Translator",
  "endpoints": {
    "POST /api/translate": "Translate natural language to code",
    "GET /api/languages": "Get list of supported languages",
    "GET /api/health": "Health check endpoint"
  }
}
```

### 2. Health Check

Check if the API is running.

**Endpoint:** `GET /api/health`

**Response:**
```json
{
  "status": "healthy",
  "service": "aibase-api"
}
```

### 3. Get Supported Languages

Get a list of all supported programming languages.

**Endpoint:** `GET /api/languages`

**Response:**
```json
{
  "languages": [
    "python",
    "javascript",
    "java",
    "cpp",
    "csharp",
    "go",
    "rust",
    "typescript",
    "php",
    "ruby",
    "swift",
    "kotlin"
  ],
  "count": 12
}
```

### 4. Translate Natural Language to Code

Generate code from a natural language description.

**Endpoint:** `POST /api/translate`

**Request Body:**
```json
{
  "description": "create a function that checks if a number is prime",
  "language": "python",
  "include_comments": true,
  "model": "qwen2.5-coder:7b",
  "temperature": 0.7,
  "max_tokens": 2000
}
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| description | string | Yes | - | Natural language description of the code to generate |
| language | string | No | "python" | Target programming language |
| include_comments | boolean | No | true | Whether to include comments in generated code |
| model | string | No | provider default | Ollama model to use (e.g. `qwen2.5-coder:7b`) |
| temperature | float | No | 0.7 | Temperature for generation (0.0-1.0) |
| max_tokens | integer | No | 2000 | Maximum tokens to generate |

**Success Response:**
```json
{
  "success": true,
  "code": "def is_prime(n):\n    if n < 2:\n        return False\n    ...",
  "language": "python"
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "Description is required"
}
```

**Status Codes:**
- `200 OK` - Request successful
- `400 Bad Request` - Invalid request parameters
- `500 Internal Server Error` - Server error

## Usage Examples

### Python

```python
import requests

url = "http://localhost:5000/api/translate"
data = {
    "description": "create a function that reverses a string",
    "language": "python"
}

response = requests.post(url, json=data)
result = response.json()

if result["success"]:
    print(result["code"])
else:
    print(f"Error: {result['error']}")
```

### JavaScript

```javascript
const url = "http://localhost:5000/api/translate";
const data = {
  description: "create a function that sorts an array",
  language: "javascript"
};

fetch(url, {
  method: "POST",
  headers: {
    "Content-Type": "application/json"
  },
  body: JSON.stringify(data)
})
  .then(response => response.json())
  .then(result => {
    if (result.success) {
      console.log(result.code);
    } else {
      console.error("Error:", result.error);
    }
  });
```

### cURL

```bash
curl -X POST http://localhost:5000/api/translate \
  -H "Content-Type: application/json" \
  -d '{
    "description": "create a binary search function",
    "language": "python",
    "include_comments": true
  }'
```

## Running the API Server

### Start the server:

```bash
python api_server.py
```

### With custom host and port:

```bash
python api_server.py --host 0.0.0.0 --port 8080
```

### In debug mode:

```bash
python api_server.py --debug
```

## Rate Limiting

Currently, there are no rate limits on the API. Generation speed depends on your local hardware and the Ollama model you use.

## Error Handling

All errors return a JSON response with the following format:

```json
{
  "success": false,
  "error": "Error message describing what went wrong"
}
```

Common error scenarios:
- Missing or invalid description
- Unsupported programming language
- Ollama not running or model not pulled

## Building a Bot with Aibase API

The API is designed to be easily integrated into bots:

### Discord Bot Example

```python
import discord
import requests

client = discord.Client()
AIBASE_URL = "http://localhost:5000/api/translate"

@client.event
async def on_message(message):
    if message.content.startswith('!code'):
        # Extract description after command
        description = message.content[6:]
        
        # Call Aibase API
        response = requests.post(AIBASE_URL, json={
            "description": description,
            "language": "python"
        })
        
        result = response.json()
        if result["success"]:
            await message.channel.send(f"```python\n{result['code']}\n```")
        else:
            await message.channel.send(f"Error: {result['error']}")

client.run('YOUR_DISCORD_TOKEN')
```

### Telegram Bot Example

```python
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import requests

AIBASE_URL = "http://localhost:5000/api/translate"

def code_command(update: Update, context):
    description = ' '.join(context.args)
    
    response = requests.post(AIBASE_URL, json={
        "description": description,
        "language": "python"
    })
    
    result = response.json()
    if result["success"]:
        update.message.reply_text(f"```\n{result['code']}\n```", parse_mode='Markdown')
    else:
        update.message.reply_text(f"Error: {result['error']}")

updater = Updater("YOUR_TELEGRAM_TOKEN")
updater.dispatcher.add_handler(CommandHandler('code', code_command))
updater.start_polling()
```

### Slack Bot Example

```python
from slack_bolt import App
import requests

app = App(token="YOUR_SLACK_TOKEN")
AIBASE_URL = "http://localhost:5000/api/translate"

@app.command("/code")
def code_command(ack, command):
    ack()
    
    description = command["text"]
    response = requests.post(AIBASE_URL, json={
        "description": description,
        "language": "python"
    })
    
    result = response.json()
    if result["success"]:
        return f"```\n{result['code']}\n```"
    else:
        return f"Error: {result['error']}"

app.start()
```

## Best Practices

1. **Error Handling**: Always check the `success` field in responses
2. **Rate Limiting**: Implement your own rate limiting if you deploy this as a shared service
3. **Caching**: Consider caching frequently requested code snippets
4. **Input Validation**: Sanitize and validate user input before sending to the API
5. **Timeouts**: Set appropriate timeouts for API requests (code generation can take 5-10 seconds)

## Deployment

For production deployment, consider:

- Using a production WSGI server like Gunicorn or uWSGI
- Setting up HTTPS with SSL certificates
- Implementing authentication and authorization
- Adding request logging and monitoring
- Using a reverse proxy like Nginx
- Containerizing with Docker

### Example Docker deployment:

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 5000
CMD ["python", "api_server.py", "--host", "0.0.0.0"]
```

## Support

For issues or questions, please open an issue on GitHub.
