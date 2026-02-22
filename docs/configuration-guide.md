# Configuration Guide

This guide covers all configuration options for using Aibase to generate Flutter and React Native code.

## Table of Contents

1. [Environment Setup](#environment-setup)
2. [API Configuration](#api-configuration)
3. [Model Parameters](#model-parameters)
4. [Language-Specific Settings](#language-specific-settings)
5. [Performance Tuning](#performance-tuning)
6. [Production Deployment](#production-deployment)

## Environment Setup

### Basic Setup

1. **Clone Repository**
   ```bash
   git clone https://github.com/highskills123/Aibase.git
   cd Aibase
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**
   ```bash
   cp .env.example .env
   ```

### Environment Variables

Create a `.env` file in the root directory:

```bash
# Ollama Settings
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5-coder:7b

# Optional API Server Settings
API_HOST=0.0.0.0
API_PORT=5000
API_DEBUG=false

# Optional Discord Bot Settings (if using)
DISCORD_BOT_TOKEN=your_discord_token_here
```

### Ollama Setup

1. Install Ollama from [https://ollama.com](https://ollama.com)
2. Pull the default model:
   ```bash
   ollama pull qwen2.5-coder:7b
   ```

**Security Note:** Never commit `.env` file to version control.

## API Configuration

### Starting the API Server

#### Development Mode
```bash
python api_server.py
```

#### Custom Host/Port
```bash
python api_server.py --host 0.0.0.0 --port 8080
```

#### Debug Mode
```bash
python api_server.py --debug
```

### CORS Configuration

The API enables CORS by default. To customize:

Edit `api_server.py`:
```python
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=[
    "http://localhost:3000",
    "https://your-domain.com"
])
```

### API Rate Limiting

For production, add rate limiting:

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["100 per day", "10 per hour"]
)

@app.route('/api/translate', methods=['POST'])
@limiter.limit("20 per hour")
def translate():
    # ... existing code
```

## Model Parameters

### Available Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| model | string | qwen2.5-coder:7b | - | Ollama model to use |
| temperature | float | 0.7 | 0.0-1.0 | Creativity level |
| max_tokens | integer | 2000 | 1-4096 | Maximum response length |

### Temperature Guide

**Low Temperature (0.0-0.3):**
- More focused and deterministic
- Better for production code
- Consistent outputs
- Use for: Standard components, forms, layouts

**Medium Temperature (0.4-0.7):**
- Balanced creativity and consistency
- Good for general use
- Moderate variation
- Use for: Most use cases (default)

**High Temperature (0.8-1.0):**
- More creative and varied
- Experimental outputs
- Higher randomness
- Use for: Exploration, inspiration, prototyping

### Model Selection

#### qwen2.5-coder:7b (Default)
- **Speed:** Fast
- **Cost:** Free (local)
- **Quality:** Good
- **Best for:** Most use cases, code generation

#### llama3
- **Speed:** Moderate
- **Cost:** Free (local)
- **Quality:** Good
- **Best for:** General-purpose tasks

#### codellama
- **Speed:** Moderate
- **Cost:** Free (local)
- **Quality:** Good
- **Best for:** Code-focused tasks

### Usage Examples

#### CLI
```bash
# Use llama3 with low temperature
python aibase.py \
  -d "create a Flutter widget" \
  -l flutter-widget \
  --model llama3 \
  --temperature 0.3 \
  --max-tokens 3000
```

#### API
```bash
curl -X POST http://localhost:5000/api/translate \
  -H "Content-Type: application/json" \
  -d '{
    "description": "create a React Native component",
    "language": "react-native-component",
    "model": "llama3",
    "temperature": 0.5,
    "max_tokens": 2500
  }'
```

#### Programmatic
```python
from aibase import AibaseTranslator

translator = AibaseTranslator(
    model="llama3",
    temperature=0.5,
    max_tokens=3000
)

code = translator.translate(
    description="create a login form",
    target_language="flutter-widget"
)
```

## Language-Specific Settings

### Flutter Configuration

#### Recommended Settings

**For Simple Widgets:**
```python
{
    "language": "flutter-widget",
    "temperature": 0.5,
    "max_tokens": 2000
}
```

**For Complex Widgets:**
```python
{
    "language": "flutter-widget",
    "temperature": 0.4,
    "max_tokens": 3000,
    "model": "llama3"
}
```

**For Full Apps:**
```python
{
    "language": "flutter",
    "temperature": 0.6,
    "max_tokens": 4000,
    "model": "llama3"
}
```

#### Description Tips

Be specific about:
- Widget type (StatelessWidget, StatefulWidget)
- Layout (Column, Row, Stack)
- State management needs
- Material Design components

### React Native Configuration

#### Recommended Settings

**For Simple Components:**
```python
{
    "language": "react-native-component",
    "temperature": 0.5,
    "max_tokens": 2000
}
```

**For Complex Components:**
```python
{
    "language": "react-native-component",
    "temperature": 0.4,
    "max_tokens": 3000,
    "model": "llama3"
}
```

**For Full Apps:**
```python
{
    "language": "react-native",
    "temperature": 0.6,
    "max_tokens": 4000,
    "model": "llama3"
}
```

#### Description Tips

Specify:
- Component type (functional with hooks)
- UI components (View, Text, TouchableOpacity)
- State management (useState, useEffect)
- Navigation needs
- Platform-specific features

## Performance Tuning

### Optimizing Response Time

1. **Use Appropriate max_tokens**
   - Don't request more than needed
   - Simple components: 1000-2000 tokens
   - Complex components: 2000-3000 tokens
   - Full apps: 3000-4000 tokens

2. **Choose Right Model**
   - Use default qwen2.5-coder:7b for most tasks
   - Use llama3 for general-purpose tasks

3. **Optimize Descriptions**
   - Be specific but concise
   - Avoid unnecessary details
   - Focus on requirements

### Caching Strategy

Implement caching for repeated requests:

```python
import hashlib
import json
from functools import lru_cache

@lru_cache(maxsize=100)
def generate_code(description, language):
    translator = AibaseTranslator()
    return translator.translate(description, language)
```

### Batch Processing

For multiple components:

```python
import asyncio
import aiohttp

async def generate_batch(descriptions, language):
    async with aiohttp.ClientSession() as session:
        tasks = [
            generate_single(session, desc, language)
            for desc in descriptions
        ]
        return await asyncio.gather(*tasks)

async def generate_single(session, description, language):
    async with session.post(
        'http://localhost:5000/api/translate',
        json={'description': description, 'language': language}
    ) as response:
        return await response.json()
```

## Production Deployment

### Using Gunicorn

1. **Install Gunicorn**
   ```bash
   pip install gunicorn
   ```

2. **Create WSGI Entry Point**
   
   Create `wsgi.py`:
   ```python
   from api_server import app
   
   if __name__ == "__main__":
       app.run()
   ```

3. **Run with Gunicorn**
   ```bash
   gunicorn --bind 0.0.0.0:5000 --workers 4 wsgi:app
   ```

### Using Docker

Create `Dockerfile`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "wsgi:app"]
```

Build and run:
```bash
docker build -t aibase-api .
docker run -p 5000:5000 --env-file .env aibase-api
```

### Using Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "5000:5000"
    environment:
      - OLLAMA_BASE_URL=${OLLAMA_BASE_URL}
    restart: unless-stopped
    
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - api
```

### Nginx Configuration

Create `nginx.conf`:

```nginx
upstream aibase {
    server api:5000;
}

server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://aibase;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Increase timeout for code generation
        proxy_read_timeout 120s;
        proxy_connect_timeout 120s;
    }
}
```

### Environment-Specific Configs

#### Development
```bash
# .env.development
OLLAMA_BASE_URL=http://localhost:11434
API_DEBUG=true
API_HOST=localhost
API_PORT=5000
```

#### Production
```bash
# .env.production
OLLAMA_BASE_URL=http://localhost:11434
API_DEBUG=false
API_HOST=0.0.0.0
API_PORT=5000
```

### Monitoring

Add logging:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('aibase.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

@app.route('/api/translate', methods=['POST'])
def translate():
    logger.info(f"Request received: {request.json}")
    # ... existing code
    logger.info(f"Response sent: success={result['success']}")
```

### Health Checks

Add comprehensive health check:

```python
@app.route('/api/health', methods=['GET'])
def health():
    try:
        # Test Ollama connection
        translator = AibaseTranslator()
        
        return jsonify({
            "status": "healthy",
            "service": "aibase-api",
            "version": "1.0.0",
            "ollama_configured": True
        })
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 500
```

## Security Best Practices

1. **Protect API Keys**
   - Never commit to version control
   - Use environment variables
   - Rotate keys regularly

2. **Input Validation**
   - Validate all user inputs
   - Limit description length
   - Sanitize inputs

3. **Rate Limiting**
   - Implement per-IP limits
   - Add authentication for production
   - Monitor for abuse

4. **HTTPS Only**
   - Use SSL certificates in production
   - Redirect HTTP to HTTPS
   - Use secure headers

5. **Authentication**
   
   Add API key authentication:
   ```python
   from functools import wraps
   
   def require_api_key(f):
       @wraps(f)
       def decorated_function(*args, **kwargs):
           api_key = request.headers.get('X-API-Key')
           if api_key != os.getenv('API_SECRET_KEY'):
               return jsonify({"error": "Unauthorized"}), 401
           return f(*args, **kwargs)
       return decorated_function
   
   @app.route('/api/translate', methods=['POST'])
   @require_api_key
   def translate():
       # ... existing code
   ```

## Troubleshooting

### Common Issues

**API Server Won't Start:**
- Check port availability
- Verify dependencies installed
- Check .env file exists and is valid

**Slow Responses:**
- Reduce max_tokens
- Ensure Ollama is running locally
- Implement caching

**Rate Limit Errors:**
- Add retry logic with backoff
- Reduce request frequency
- Implement request queuing

## Next Steps

- Review [Best Practices](best-practices.md)
- Check [API Documentation](api-mobile-frameworks.md)
- See [Tutorials](tutorials/)

---

**Questions? Open an issue on [GitHub](https://github.com/highskills123/Aibase/issues)**
