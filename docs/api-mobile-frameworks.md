# API Usage for Mobile Frameworks

This document provides comprehensive API usage examples for generating Flutter and React Native code using the Aibase REST API.

## Table of Contents

1. [Overview](#overview)
2. [Getting Started](#getting-started)
3. [API Endpoints](#api-endpoints)
4. [Language Parameters](#language-parameters)
5. [Request Examples](#request-examples)
6. [Response Format](#response-format)
7. [Integration Examples](#integration-examples)
8. [Best Practices](#best-practices)
9. [Error Handling](#error-handling)

## Overview

The Aibase API allows you to programmatically generate Flutter and React Native code from natural language descriptions. This is perfect for:

- **Mobile Development Tools**: Integrate code generation into IDEs or build tools
- **CI/CD Pipelines**: Automate component generation in your workflow
- **Code Generators**: Build custom code generation tools
- **Learning Platforms**: Create interactive coding tutorials
- **Prototyping Tools**: Rapid UI prototyping systems

## Getting Started

### Start the API Server

```bash
# Default (port 5000)
python api_server.py

# Custom port
python api_server.py --port 8080

# Production mode
python api_server.py --host 0.0.0.0 --port 80
```

### Base URL

```
http://localhost:5000
```

For production, use your deployed URL:
```
https://your-domain.com
```

## API Endpoints

### 1. Health Check

```http
GET /api/health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "aibase-api"
}
```

### 2. List Supported Languages

```http
GET /api/languages
```

**Response:**
```json
{
  "languages": [
    "python", "javascript", "java", "cpp", "csharp",
    "go", "rust", "typescript", "php", "ruby",
    "swift", "kotlin", "dart", "flutter",
    "flutter-widget", "react-native",
    "react-native-component"
  ],
  "count": 17
}
```

### 3. Generate Code

```http
POST /api/translate
Content-Type: application/json
```

**Request Body:**
```json
{
  "description": "your natural language description",
  "language": "flutter-widget",
  "include_comments": true,
  "model": "qwen2.5-coder:7b",
  "temperature": 0.7,
  "max_tokens": 2000
}
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| description | string | Yes | - | Natural language description |
| language | string | No | "python" | Target language (see options below) |
| include_comments | boolean | No | true | Include code comments |
| model | string | No | "qwen2.5-coder:7b" | Ollama model |
| temperature | float | No | 0.7 | Creativity (0.0-1.0) |
| max_tokens | integer | No | 2000 | Maximum response length |

## Language Parameters

### Flutter Options

#### `flutter-widget`
Generate individual Flutter widgets (StatelessWidget, StatefulWidget).

**Best for:**
- UI components
- Reusable widgets
- Single screen layouts

#### `flutter`
Generate complete Flutter applications.

**Best for:**
- Full apps with MaterialApp
- Multi-screen applications
- Complete project structure

#### `dart`
Generate pure Dart code without Flutter dependencies.

**Best for:**
- Business logic
- Data models
- Utilities and helpers

### React Native Options

#### `react-native-component`
Generate individual React Native components.

**Best for:**
- UI components
- Screens
- Reusable components

#### `react-native`
Generate complete React Native applications.

**Best for:**
- Full apps
- Navigation structure
- Multi-screen apps

## Request Examples

### Flutter Examples

#### 1. Generate a Flutter Widget

**cURL:**
```bash
curl -X POST http://localhost:5000/api/translate \
  -H "Content-Type: application/json" \
  -d '{
    "description": "create a Flutter counter StatefulWidget with increment and decrement buttons",
    "language": "flutter-widget"
  }'
```

**Python:**
```python
import requests

response = requests.post(
    "http://localhost:5000/api/translate",
    json={
        "description": "create a Flutter login form with email and password fields",
        "language": "flutter-widget"
    }
)

result = response.json()
if result["success"]:
    print(result["code"])
    # Save to file
    with open("login_form.dart", "w") as f:
        f.write(result["code"])
```

**JavaScript/Node.js:**
```javascript
const axios = require('axios');

async function generateFlutterWidget() {
  try {
    const response = await axios.post('http://localhost:5000/api/translate', {
      description: 'create a Flutter card widget with image, title, and description',
      language: 'flutter-widget'
    });

    if (response.data.success) {
      console.log(response.data.code);
      // Save to file
      const fs = require('fs');
      fs.writeFileSync('card_widget.dart', response.data.code);
    }
  } catch (error) {
    console.error('Error:', error.message);
  }
}

generateFlutterWidget();
```

#### 2. Generate Flutter App

```bash
curl -X POST http://localhost:5000/api/translate \
  -H "Content-Type: application/json" \
  -d '{
    "description": "create a complete Flutter todo app with add, delete, and mark complete functionality",
    "language": "flutter",
    "max_tokens": 3000
  }'
```

#### 3. Generate Pure Dart Code

```bash
curl -X POST http://localhost:5000/api/translate \
  -H "Content-Type: application/json" \
  -d '{
    "description": "create a Dart class for User with name, email, and toJson/fromJson methods",
    "language": "dart"
  }'
```

### React Native Examples

#### 1. Generate React Native Component

**cURL:**
```bash
curl -X POST http://localhost:5000/api/translate \
  -H "Content-Type: application/json" \
  -d '{
    "description": "create a React Native button component with TouchableOpacity and custom styling",
    "language": "react-native-component"
  }'
```

**Python:**
```python
import requests

response = requests.post(
    "http://localhost:5000/api/translate",
    json={
        "description": "create a React Native profile screen with avatar and user info",
        "language": "react-native-component"
    }
)

result = response.json()
if result["success"]:
    with open("ProfileScreen.js", "w") as f:
        f.write(result["code"])
```

**JavaScript/TypeScript:**
```typescript
async function generateReactNativeComponent() {
  const response = await fetch('http://localhost:5000/api/translate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      description: 'create a React Native FlatList component displaying user posts',
      language: 'react-native-component'
    })
  });

  const result = await response.json();
  if (result.success) {
    // Use the generated code
    console.log(result.code);
  }
}
```

#### 2. Generate with Custom Parameters

```bash
curl -X POST http://localhost:5000/api/translate \
  -H "Content-Type: application/json" \
  -d '{
    "description": "create a React Native navigation system with stack navigator",
    "language": "react-native",
    "include_comments": false,
    "temperature": 0.3,
    "max_tokens": 3000
  }'
```

## Response Format

### Success Response

```json
{
  "success": true,
  "code": "import React from 'react';\n...",
  "language": "react-native-component"
}
```

### Error Response

```json
{
  "success": false,
  "error": "Description is required"
}
```

### HTTP Status Codes

- `200 OK` - Success
- `400 Bad Request` - Invalid parameters
- `500 Internal Server Error` - Server error

## Integration Examples

### 1. CLI Tool

Create a simple CLI tool:

```python
#!/usr/bin/env python3
import sys
import requests

def generate_code(description, language, output_file):
    response = requests.post(
        "http://localhost:5000/api/translate",
        json={"description": description, "language": language}
    )
    
    result = response.json()
    if result["success"]:
        with open(output_file, "w") as f:
            f.write(result["code"])
        print(f"✓ Generated {output_file}")
    else:
        print(f"✗ Error: {result['error']}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: generate.py <description> <language> <output>")
        sys.exit(1)
    
    generate_code(sys.argv[1], sys.argv[2], sys.argv[3])
```

Usage:
```bash
./generate.py "create a login form" flutter-widget login.dart
```

### 2. VS Code Extension

```javascript
const vscode = require('vscode');
const axios = require('axios');

async function generateCode(description, language) {
  const response = await axios.post('http://localhost:5000/api/translate', {
    description,
    language
  });

  if (response.data.success) {
    const doc = await vscode.workspace.openTextDocument({
      content: response.data.code,
      language: getVSCodeLanguage(language)
    });
    await vscode.window.showTextDocument(doc);
  }
}

function getVSCodeLanguage(language) {
  const mapping = {
    'flutter-widget': 'dart',
    'flutter': 'dart',
    'dart': 'dart',
    'react-native-component': 'javascript',
    'react-native': 'javascript'
  };
  return mapping[language] || 'plaintext';
}
```

### 3. Build Tool Integration

**Gulp Task:**
```javascript
const gulp = require('gulp');
const axios = require('axios');
const fs = require('fs').promises;

gulp.task('generate-components', async () => {
  const components = [
    { desc: 'create a header component', file: 'Header.js' },
    { desc: 'create a footer component', file: 'Footer.js' }
  ];

  for (const comp of components) {
    const response = await axios.post('http://localhost:5000/api/translate', {
      description: comp.desc,
      language: 'react-native-component'
    });

    if (response.data.success) {
      await fs.writeFile(`src/components/${comp.file}`, response.data.code);
      console.log(`✓ Generated ${comp.file}`);
    }
  }
});
```

### 4. GitHub Action

```yaml
name: Generate Components

on:
  workflow_dispatch:
    inputs:
      description:
        description: 'Component description'
        required: true
      language:
        description: 'Target language'
        required: true
        default: 'react-native-component'

jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Generate Code
        run: |
          curl -X POST ${{ secrets.AIBASE_API_URL }}/api/translate \
            -H "Content-Type: application/json" \
            -d '{
              "description": "${{ github.event.inputs.description }}",
              "language": "${{ github.event.inputs.language }}"
            }' | jq -r '.code' > generated_component.js
      
      - name: Commit
        run: |
          git config user.name "Bot"
          git config user.email "bot@example.com"
          git add generated_component.js
          git commit -m "Generated component"
          git push
```

## Best Practices

### 1. Request Optimization

**Batch Related Requests:**
```python
import asyncio
import aiohttp

async def generate_multiple(descriptions):
    async with aiohttp.ClientSession() as session:
        tasks = []
        for desc in descriptions:
            task = session.post(
                'http://localhost:5000/api/translate',
                json={'description': desc, 'language': 'flutter-widget'}
            )
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks)
        return [await r.json() for r in responses]

# Use it
descriptions = [
    "create a header widget",
    "create a footer widget",
    "create a sidebar widget"
]
results = asyncio.run(generate_multiple(descriptions))
```

### 2. Error Handling

```python
def safe_generate(description, language, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.post(
                "http://localhost:5000/api/translate",
                json={"description": description, "language": language},
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            if result["success"]:
                return result["code"]
            else:
                print(f"Error: {result['error']}")
                
        except requests.exceptions.Timeout:
            print(f"Timeout on attempt {attempt + 1}")
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
        
        if attempt < max_retries - 1:
            time.sleep(2 ** attempt)  # Exponential backoff
    
    raise Exception("Failed after all retries")
```

### 3. Caching

```python
import hashlib
import json
from functools import lru_cache

def cache_key(description, language):
    data = json.dumps({"description": description, "language": language})
    return hashlib.md5(data.encode()).hexdigest()

@lru_cache(maxsize=100)
def generate_with_cache(description, language):
    response = requests.post(
        "http://localhost:5000/api/translate",
        json={"description": description, "language": language}
    )
    result = response.json()
    return result["code"] if result["success"] else None
```

### 4. Validation

```python
def validate_request(description, language):
    if not description or len(description.strip()) == 0:
        raise ValueError("Description cannot be empty")
    
    if len(description) > 1000:
        raise ValueError("Description too long (max 1000 characters)")
    
    valid_languages = [
        'flutter', 'flutter-widget', 'dart',
        'react-native', 'react-native-component'
    ]
    if language not in valid_languages:
        raise ValueError(f"Invalid language. Must be one of: {valid_languages}")
```

## Error Handling

### Common Errors

#### 1. Missing Description
```json
{
  "success": false,
  "error": "Description is required"
}
```

**Solution:** Ensure description is provided and not empty.

#### 2. Invalid Language
```json
{
  "success": false,
  "error": "Unsupported language: invalid-lang"
}
```

**Solution:** Use one of the supported languages from `/api/languages`.

#### 3. Ollama Not Running
```json
{
  "success": false,
  "error": "Cannot connect to Ollama"
}
```

**Solution:** Start Ollama with `ollama serve`.

#### 4. Timeout
**Solution:** Increase timeout or reduce complexity:
```python
response = requests.post(
    url,
    json=data,
    timeout=60  # Increase timeout
)
```

### Debugging Tips

1. **Check API Server Logs**
   ```bash
   python api_server.py --debug
   ```

2. **Verify Request Format**
   ```python
   import json
   print(json.dumps(request_data, indent=2))
   ```

3. **Test with cURL First**
   ```bash
   curl -v -X POST http://localhost:5000/api/translate \
     -H "Content-Type: application/json" \
     -d '{"description": "test", "language": "flutter-widget"}'
   ```

## Advanced Usage

### Custom Model Selection

```bash
curl -X POST http://localhost:5000/api/translate \
  -H "Content-Type: application/json" \
  -d '{
    "description": "create a complex Flutter app",
    "language": "flutter",
    "model": "llama3",
    "max_tokens": 4000
  }'
```

### Adjusting Creativity

```python
# More deterministic (less creative)
response = requests.post(url, json={
    "description": desc,
    "language": "flutter-widget",
    "temperature": 0.2
})

# More creative (more varied)
response = requests.post(url, json={
    "description": desc,
    "language": "flutter-widget",
    "temperature": 0.9
})
```

## Security Considerations

1. **Server Protection**: Never expose your API server to the public internet without authentication
2. **Input Validation**: Validate all user inputs before sending to API
3. **Rate Limiting**: Implement rate limiting in production
4. **HTTPS**: Always use HTTPS in production
5. **Authentication**: Add authentication for production deployments

## Next Steps

- Review [Flutter Getting Started](flutter-getting-started.md)
- Review [React Native Getting Started](react-native-getting-started.md)
- Check [Configuration Guide](configuration-guide.md)
- Read [Best Practices](best-practices.md)

---

**Need help? Open an issue on [GitHub](https://github.com/highskills123/Aibase/issues)**
