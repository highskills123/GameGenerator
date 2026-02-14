# Architecture Overview

This document describes the architecture of Aibase's code generation system, with a focus on Flutter and React Native support.

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Core Components](#core-components)
3. [Code Generation Flow](#code-generation-flow)
4. [Language Support System](#language-support-system)
5. [API Layer](#api-layer)
6. [Extension Points](#extension-points)

## System Architecture

Aibase follows a modular architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────┐
│                     User Interfaces                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │   CLI    │  │ REST API │  │Discord   │  │  Python  │ │
│  │  aibase  │  │  Server  │  │   Bot    │  │   SDK    │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘ │
└───────┼─────────────┼─────────────┼─────────────┼────────┘
        │             │             │             │
        └─────────────┴─────────────┴─────────────┘
                           │
        ┌──────────────────▼──────────────────┐
        │      AibaseTranslator Core          │
        │  ┌────────────────────────────────┐ │
        │  │  Language Configuration        │ │
        │  │  SUPPORTED_LANGUAGES dict      │ │
        │  └────────────────────────────────┘ │
        │  ┌────────────────────────────────┐ │
        │  │  Translation Engine            │ │
        │  │  - Prompt Generation           │ │
        │  │  - OpenAI API Client           │ │
        │  │  - Response Processing         │ │
        │  └────────────────────────────────┘ │
        └─────────────────┬───────────────────┘
                          │
        ┌─────────────────▼───────────────────┐
        │       OpenAI API                    │
        │  ┌────────────────────────────────┐ │
        │  │  GPT-3.5-turbo / GPT-4         │ │
        │  └────────────────────────────────┘ │
        └─────────────────────────────────────┘
```

## Core Components

### 1. AibaseTranslator Class

**Location:** `aibase.py`

**Responsibilities:**
- Initialize OpenAI client
- Manage language configurations
- Generate prompts for different languages
- Process and clean responses
- Handle errors

**Key Methods:**

```python
class AibaseTranslator:
    def __init__(self, api_key, model, temperature, max_tokens):
        """Initialize translator with configuration"""
        
    def translate(self, description, target_language, include_comments):
        """Main translation method"""
        # 1. Validate language
        # 2. Generate system and user prompts
        # 3. Call OpenAI API
        # 4. Process response
        # 5. Clean markdown artifacts
        # 6. Return generated code
```

**Supported Languages Dictionary:**

```python
SUPPORTED_LANGUAGES = {
    # General purpose
    'python': 'Python',
    'javascript': 'JavaScript',
    'typescript': 'TypeScript',
    # ... other languages
    
    # Mobile frameworks
    'dart': 'Dart',
    'flutter': 'Flutter/Dart',
    'flutter-widget': 'Flutter Widget',
    'react-native': 'React Native',
    'react-native-component': 'React Native Component'
}
```

### 2. API Server

**Location:** `api_server.py`

**Responsibilities:**
- Expose REST API endpoints
- Handle HTTP requests/responses
- Manage CORS
- Error handling and validation

**Endpoints:**

```python
@app.route('/', methods=['GET'])
def index():
    """API information"""

@app.route('/api/health', methods=['GET'])
def health():
    """Health check"""

@app.route('/api/languages', methods=['GET'])
def get_languages():
    """List supported languages"""

@app.route('/api/translate', methods=['POST'])
def translate():
    """Generate code from description"""
```

### 3. CLI Interface

**Location:** `aibase.py` (main function)

**Responsibilities:**
- Parse command-line arguments
- Interactive mode handling
- File I/O operations
- Colored output formatting

**Modes:**
- Direct mode: `python aibase.py -d "description" -l language`
- Interactive mode: `python aibase.py`

### 4. Bot Interfaces

**Location:** `discord_bot.py`

**Responsibilities:**
- Platform-specific bot logic
- Command parsing
- Response formatting for platforms
- File handling for large outputs

## Code Generation Flow

### Request Flow

```
1. User Input
   ├─ CLI: Command line arguments
   ├─ API: HTTP POST request
   ├─ Bot: Platform-specific command
   └─ SDK: Python function call
        │
        ▼
2. Input Validation
   ├─ Check description present
   ├─ Validate language
   └─ Validate parameters
        │
        ▼
3. Prompt Generation
   ├─ System Prompt
   │  └─ Role: Expert programmer in target language
   │     └─ Instructions: Generate clean, efficient code
   └─ User Prompt
      └─ Description + Target Language + Requirements
        │
        ▼
4. OpenAI API Call
   ├─ Send messages to GPT model
   ├─ Apply temperature and max_tokens
   └─ Receive completion
        │
        ▼
5. Response Processing
   ├─ Extract generated code
   ├─ Remove markdown code blocks
   └─ Clean formatting
        │
        ▼
6. Output Delivery
   ├─ CLI: Print to console / save to file
   ├─ API: JSON response
   ├─ Bot: Message reply / file upload
   └─ SDK: Return string
```

### Prompt Engineering

#### System Prompt Template

```python
f"You are an expert programmer that translates natural language descriptions "
f"into clean, efficient, and well-structured {lang_name} code. "
f"Provide only the code without additional explanations unless specifically asked. "
f"{'Include helpful comments to explain the code.' if include_comments else 'Minimize comments.'}"
```

#### User Prompt Template

```python
f"Convert the following natural language description into {lang_name} code:\n\n"
f"{description}\n\n"
f"Provide complete, working code that can be run or used directly."
```

#### Language-Specific Adjustments

The system prompt adapts based on language:

**For flutter-widget:**
```
"You are an expert Flutter developer. Generate complete Flutter widgets 
following Material Design guidelines. Include proper imports, widget structure, 
and styling."
```

**For react-native-component:**
```
"You are an expert React Native developer. Generate modern functional components 
using hooks. Include proper imports, StyleSheet, and platform-specific code 
where appropriate."
```

## Language Support System

### Adding New Language Support

To add a new language or framework:

**1. Update SUPPORTED_LANGUAGES:**

```python
SUPPORTED_LANGUAGES = {
    # ... existing languages
    'new-language': 'Display Name'
}
```

**2. (Optional) Add Language-Specific Prompt Engineering:**

```python
def _get_system_prompt(self, language, include_comments):
    base_prompt = f"You are an expert programmer..."
    
    # Add language-specific instructions
    if language == 'new-language':
        base_prompt += "\nUse specific patterns for this language..."
    
    return base_prompt
```

**3. Update Documentation:**
- Add to README.md
- Add examples
- Add getting started guide

### Language Categories

Languages are categorized by use case:

**General Purpose:**
- python, javascript, java, cpp, go, rust, etc.

**Mobile Native:**
- swift (iOS), kotlin (Android)

**Cross-Platform Mobile:**
- flutter, flutter-widget, dart
- react-native, react-native-component

**Web:**
- javascript, typescript, php

## API Layer

### Request Flow in API Server

```python
@app.route('/api/translate', methods=['POST'])
def translate():
    # 1. Parse JSON request
    data = request.get_json()
    
    # 2. Validate required fields
    if not data or 'description' not in data:
        return error_response("Description is required")
    
    # 3. Extract parameters with defaults
    description = data['description']
    language = data.get('language', 'python')
    include_comments = data.get('include_comments', True)
    
    # 4. Initialize translator with custom params
    translator = AibaseTranslator(
        model=data.get('model'),
        temperature=data.get('temperature'),
        max_tokens=data.get('max_tokens')
    )
    
    # 5. Generate code
    code = translator.translate(description, language, include_comments)
    
    # 6. Return success response
    return success_response(code, language)
```

### Error Handling

```python
try:
    # ... translation logic
except ValueError as e:
    # User input errors (invalid language, etc.)
    return jsonify({"success": False, "error": str(e)}), 400
except Exception as e:
    # Server errors (API errors, etc.)
    return jsonify({"success": False, "error": str(e)}), 500
```

## Extension Points

### 1. Custom Language Support

Extend `AibaseTranslator` to add custom language processing:

```python
class CustomTranslator(AibaseTranslator):
    def translate(self, description, target_language, include_comments):
        # Pre-processing
        if target_language == 'custom-lang':
            description = self.preprocess_custom(description)
        
        # Call parent translate
        code = super().translate(description, target_language, include_comments)
        
        # Post-processing
        if target_language == 'custom-lang':
            code = self.postprocess_custom(code)
        
        return code
```

### 2. Custom Prompt Engineering

Override prompt generation:

```python
class CustomTranslator(AibaseTranslator):
    def _generate_system_prompt(self, language, include_comments):
        if language == 'flutter-widget':
            return "Custom Flutter-specific prompt..."
        return super()._generate_system_prompt(language, include_comments)
```

### 3. Response Processing

Add custom response processing:

```python
def _process_response(self, response, language):
    code = response.choices[0].message.content.strip()
    
    # Language-specific processing
    if language == 'flutter-widget':
        code = self._ensure_flutter_imports(code)
    
    return code
```

### 4. API Middleware

Add custom middleware for authentication, logging, etc.:

```python
from functools import wraps

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # Custom authentication logic
        return f(*args, **kwargs)
    return decorated

@app.route('/api/translate', methods=['POST'])
@require_auth
def translate():
    # ... existing logic
```

### 5. Template System (Future)

For advanced scaffolding:

```python
class TemplateGenerator:
    def generate_from_template(self, template_name, params):
        template = self.load_template(template_name)
        return self.render_template(template, params)
```

## Testing Architecture

### Unit Tests

**Location:** `test_aibase.py`

**Test Categories:**
1. Initialization tests
2. Language support tests
3. Translation workflow tests (mocked)
4. Error handling tests
5. Parameter validation tests

### Integration Tests

**Location:** `test_api.py`

**Test Categories:**
1. API endpoint tests
2. Request/response validation
3. Error response tests

## Performance Considerations

### Caching Strategy

Consider implementing caching for:
- Repeated identical requests
- Common patterns
- Language-specific templates

### Async Support

For high-volume scenarios:

```python
import asyncio
from openai import AsyncOpenAI

class AsyncTranslator(AibaseTranslator):
    async def translate_async(self, description, target_language):
        # Async implementation
        pass
```

### Rate Limiting

Implement rate limiting for API:

```python
from flask_limiter import Limiter

limiter = Limiter(app, key_func=get_remote_address)

@app.route('/api/translate', methods=['POST'])
@limiter.limit("10 per minute")
def translate():
    # ... existing logic
```

## Security Considerations

### API Key Protection

- Store in environment variables
- Never log or expose
- Rotate regularly

### Input Validation

- Sanitize all user inputs
- Limit description length
- Validate language values

### Output Sanitization

- Remove any injected code patterns
- Validate generated code structure
- Check for malicious patterns

## Deployment Architecture

### Production Deployment

```
Internet → Load Balancer → Nginx → Gunicorn → Flask App → OpenAI API
                             ├─> Instance 1
                             ├─> Instance 2
                             └─> Instance N
```

### Containerization

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "wsgi:app", "--workers", "4"]
```

## Monitoring and Observability

### Logging

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
```

### Metrics

Track:
- Request count by language
- Response times
- Error rates
- OpenAI API costs

## Future Enhancements

1. **Template System**: Pre-built templates for common patterns
2. **Multi-File Generation**: Generate complete project structures
3. **Code Optimization**: Post-processing for code improvements
4. **Validation**: Syntax checking of generated code
5. **Caching Layer**: Redis/Memcached for frequent requests
6. **Streaming**: Stream responses for large code generation

## Related Documentation

- [Extending Generators](extending-generators.md)
- [Contributing Guide](contributing-mobile.md)
- [Configuration Guide](configuration-guide.md)

---

**Questions? Open an issue on [GitHub](https://github.com/highskills123/Aibase/issues)**
