# Troubleshooting Guide

This guide helps you resolve common issues when generating Flutter and React Native code with Aibase.

## Table of Contents

1. [Installation Issues](#installation-issues)
2. [Ollama Connection Problems](#ollama-connection-problems)
3. [Generation Issues](#generation-issues)
4. [Flutter-Specific Issues](#flutter-specific-issues)
5. [React Native-Specific Issues](#react-native-specific-issues)
6. [API Server Issues](#api-server-issues)
7. [Code Quality Issues](#code-quality-issues)
8. [Performance Issues](#performance-issues)

## Installation Issues

### Problem: pip install fails

**Error:**
```
ERROR: Could not find a version that satisfies the requirement...
```

**Solutions:**

1. **Update pip:**
   ```bash
   pip install --upgrade pip
   ```

2. **Use Python 3.7+:**
   ```bash
   python --version  # Should be 3.7+
   ```

3. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

### Problem: Module not found after installation

**Error:**
```
ModuleNotFoundError: No module named 'flask'
```

**Solution:**
```bash
# Ensure you're in the correct environment
pip list | grep flask

# Reinstall if missing
pip install -r requirements.txt
```

## Ollama Connection Problems

### Problem: Cannot connect to Ollama

**Error:**
```
RuntimeError: Cannot connect to Ollama at http://localhost:11434
```

**Solutions:**

1. **Start Ollama:**
   ```bash
   ollama serve
   ```
   Or open the Ollama desktop app.

2. **Check Ollama is running:**
   ```bash
   curl http://localhost:11434/api/version
   ```

### Problem: Model not found

**Error:**
```
RuntimeError: Ollama returned 404
```

**Solution:**
```bash
ollama pull qwen2.5-coder:7b
```

## Generation Issues

### Problem: No code generated

**Error:**
```
Generated code is empty or None
```

**Solutions:**

1. **Check description:**
   ```bash
   # Too vague
   python aibase.py -d "widget" -l flutter-widget
   
   # Better
   python aibase.py -d "create a Flutter StatelessWidget with centered text" -l flutter-widget
   ```

2. **Increase max_tokens:**
   ```bash
   python aibase.py -d "..." -l flutter-widget --max-tokens 3000
   ```

3. **Check Ollama is running:**
   ```bash
   curl http://localhost:11434/api/version
   ```

### Problem: Generation is slow

**Causes:**
- Complex description
- Large max_tokens
- Network latency
- Ollama model loading

**Solutions:**

1. **Simplify description**
2. **Reduce max_tokens**
3. **Use a smaller model** like `qwen2.5-coder:3b`
4. **Check Ollama is running**

### Problem: Timeout errors

**Error:**
```
Timeout waiting for response
```

**Solutions:**

1. **Reduce max_tokens** - the model may be generating a large output

2. **Retry with simpler description**

3. **Check Ollama is running:**
   ```bash
   ollama ps
   ```

## Flutter-Specific Issues

### Problem: Import errors in generated code

**Error:**
```dart
Error: Not found: 'dart:ui'
Error: Not found: 'package:flutter/material.dart'
```

**Solutions:**

1. **Check pubspec.yaml:**
   ```yaml
   dependencies:
     flutter:
       sdk: flutter
   ```

2. **Run flutter pub get:**
   ```bash
   flutter pub get
   ```

3. **Regenerate with explicit imports:**
   ```bash
   python aibase.py -d "create a Flutter widget, include all necessary imports" -l flutter-widget
   ```

### Problem: Widget won't compile

**Error:**
```
Error: The method 'build' isn't defined for the class...
```

**Solutions:**

1. **Check widget structure:**
   - Extends StatelessWidget or StatefulWidget
   - Has build method
   - Returns Widget

2. **Regenerate with more specific description:**
   ```bash
   python aibase.py -d "create a complete, compilable Flutter StatelessWidget" -l flutter-widget
   ```

3. **Manually fix common issues:**
   ```dart
   // Add missing override
   @override
   Widget build(BuildContext context) {
     return Container();
   }
   ```

### Problem: StatefulWidget state issues

**Error:**
```
setState() called after dispose()
```

**Solutions:**

1. **Check lifecycle:**
   ```dart
   @override
   void dispose() {
     // Dispose controllers
     _controller.dispose();
     super.dispose();
   }
   ```

2. **Regenerate with proper lifecycle:**
   ```bash
   python aibase.py -d "create StatefulWidget with proper controller disposal in dispose method" -l flutter-widget
   ```

### Problem: Layout overflow errors

**Error:**
```
A RenderFlex overflowed by 123 pixels
```

**Solutions:**

1. **Use SingleChildScrollView:**
   ```bash
   python aibase.py -d "create widget wrapped in SingleChildScrollView to prevent overflow" -l flutter-widget
   ```

2. **Use Expanded or Flexible:**
   ```bash
   python aibase.py -d "create Column with Expanded widgets to fill available space" -l flutter-widget
   ```

## React Native-Specific Issues

### Problem: Component won't render

**Error:**
```
Element type is invalid
```

**Solutions:**

1. **Check export:**
   ```javascript
   // Ensure this is at the end
   export default ComponentName;
   ```

2. **Check import:**
   ```javascript
   // In App.js
   import ComponentName from './path/to/ComponentName';
   ```

3. **Regenerate with explicit export:**
   ```bash
   python aibase.py -d "create component with export default" -l react-native-component
   ```

### Problem: Hooks errors

**Error:**
```
Invalid hook call. Hooks can only be called inside...
```

**Solutions:**

1. **Ensure functional component:**
   ```bash
   python aibase.py -d "create functional component using hooks" -l react-native-component
   ```

2. **Check React Native version:**
   ```bash
   npm list react react-native
   # Should support hooks (React 16.8+)
   ```

### Problem: StyleSheet not working

**Issue:** Styles not applied

**Solutions:**

1. **Check StyleSheet syntax:**
   ```javascript
   const styles = StyleSheet.create({
     container: {
       flex: 1,
     },
   });
   ```

2. **Regenerate with StyleSheet:**
   ```bash
   python aibase.py -d "create component using StyleSheet.create for all styles" -l react-native-component
   ```

### Problem: Platform-specific issues

**Issue:** Different behavior on iOS/Android

**Solutions:**

1. **Use Platform.select:**
   ```bash
   python aibase.py -d "create component with Platform.select for iOS and Android specific styling" -l react-native-component
   ```

2. **SafeAreaView issues:**
   ```bash
   python aibase.py -d "create component with SafeAreaView" -l react-native-component
   ```

### Problem: Navigation errors

**Error:**
```
undefined is not an object (evaluating 'navigation.navigate')
```

**Solutions:**

1. **Install React Navigation:**
   ```bash
   npm install @react-navigation/native @react-navigation/native-stack
   npm install react-native-screens react-native-safe-area-context
   ```

2. **Wrap app in NavigationContainer:**
   ```javascript
   import { NavigationContainer } from '@react-navigation/native';
   
   const App = () => (
     <NavigationContainer>
       {/* Your screens */}
     </NavigationContainer>
   );
   ```

3. **Regenerate with navigation:**
   ```bash
   python aibase.py -d "create component with React Navigation integration" -l react-native-component
   ```

## API Server Issues

### Problem: Server won't start

**Error:**
```
Address already in use
```

**Solutions:**

1. **Check if port is in use:**
   ```bash
   # On Unix/Mac
   lsof -i :5000
   
   # On Windows
   netstat -ano | findstr :5000
   ```

2. **Use different port:**
   ```bash
   python api_server.py --port 8080
   ```

3. **Kill process using port:**
   ```bash
   # On Unix/Mac
   kill -9 <PID>
   
   # On Windows
   taskkill /PID <PID> /F
   ```

### Problem: API returns 500 error

**Error:**
```json
{
  "success": false,
  "error": "Internal server error"
}
```

**Solutions:**

1. **Check server logs:**
   ```bash
   python api_server.py --debug
   ```

2. **Verify request format:**
   ```bash
   curl -v -X POST http://localhost:5000/api/translate \
     -H "Content-Type: application/json" \
     -d '{"description": "test", "language": "flutter-widget"}'
   ```

3. **Check API key:**
   - Ensure .env is loaded
   - Restart server after changing .env

### Problem: CORS errors in browser

**Error:**
```
Access to fetch blocked by CORS policy
```

**Solutions:**

1. **CORS is enabled by default** in api_server.py

2. **If still seeing errors, check:**
   ```python
   # In api_server.py
   from flask_cors import CORS
   CORS(app)  # Should be present
   ```

3. **For specific origins:**
   ```python
   CORS(app, origins=["http://localhost:3000"])
   ```

## Code Quality Issues

### Problem: Generated code has syntax errors

**Solutions:**

1. **Use lower temperature:**
   ```bash
   python aibase.py -d "..." -l flutter-widget --temperature 0.3
   ```

2. **Be more specific:**
   ```bash
   # Instead of:
   python aibase.py -d "create a widget"
   
   # Use:
   python aibase.py -d "create a complete, syntactically correct Flutter StatelessWidget"
   ```

3. **Regenerate:**
   - Sometimes regenerating produces better results

### Problem: Code is too simple/complex

**Solutions:**

1. **Too simple - add details:**
   ```bash
   python aibase.py -d "create comprehensive widget with validation, error handling, and loading states" -l flutter-widget
   ```

2. **Too complex - simplify:**
   ```bash
   python aibase.py -d "create basic, minimal widget" -l flutter-widget
   ```

3. **Adjust max_tokens:**
   ```bash
   # For more code
   --max-tokens 3000
   
   # For less code
   --max-tokens 1000
   ```

### Problem: Missing features

**Issue:** Generated code doesn't include requested features

**Solutions:**

1. **List features explicitly:**
   ```bash
   python aibase.py -d "create widget with:
   - Feature 1
   - Feature 2
   - Feature 3" -l flutter-widget
   ```

2. **Use bullet points in description**

3. **Regenerate with emphasis:**
   ```bash
   python aibase.py -d "IMPORTANT: include validation. Create a form..." -l flutter-widget
   ```

## Performance Issues

### Problem: High generation costs

**Solutions:**

1. **Use a smaller model** like `qwen2.5-coder:3b`

2. **Reduce max_tokens:**
   ```bash
   --max-tokens 2000  # Instead of 4000
   ```

3. **Cache common requests**

4. **Optimize descriptions** to be concise

### Problem: Rate limit exceeded

**Error:**
```
Rate limit exceeded
```

**Solutions:**

1. **Wait and retry**

2. **Implement retry with backoff:**
   ```python
   import time
   
   for attempt in range(3):
       try:
           code = translator.translate(...)
           break
       except Exception as e:
           if 'rate limit' in str(e).lower():
               time.sleep(2 ** attempt)
           else:
               raise
   ```

3. **Use a faster/smaller Ollama model**

## Getting Help

### Still Having Issues?

1. **Check Examples:**
   - Review `examples/flutter/`
   - Review `examples/react-native/`

2. **Read Documentation:**
   - [Flutter Getting Started](../flutter-getting-started.md)
   - [React Native Getting Started](../react-native-getting-started.md)
   - [Best Practices](../best-practices.md)

3. **Search Issues:**
   - Check [GitHub Issues](https://github.com/highskills123/Aibase/issues)
   - Search for similar problems

4. **Ask for Help:**
   - Open new issue with:
     - Description of problem
     - Steps to reproduce
     - Error messages
     - Your environment (OS, Python version, etc.)

### Reporting Bugs

Include:
```markdown
**Environment:**
- OS: [e.g., macOS 12.0]
- Python version: [e.g., 3.9.0]
- Aibase version: [e.g., 1.0.0]

**Description:**
Clear description of the issue

**Steps to Reproduce:**
1. Run command...
2. See error...

**Expected Behavior:**
What should happen

**Actual Behavior:**
What actually happens

**Error Messages:**
```
Paste error messages here
```
```

## Quick Reference

### Common Commands

```bash
# Basic generation
python aibase.py -d "description" -l flutter-widget

# With options
python aibase.py -d "description" -l flutter-widget \
  --temperature 0.5 \
  --max-tokens 2000 \
  -o output.dart

# API server
python api_server.py
python api_server.py --port 8080 --debug

# API request
curl -X POST http://localhost:5000/api/translate \
  -H "Content-Type: application/json" \
  -d '{"description": "...", "language": "flutter-widget"}'
```

### Supported Languages

- `flutter` - Full Flutter apps
- `flutter-widget` - Flutter widgets
- `dart` - Pure Dart code
- `react-native` - Full RN apps
- `react-native-component` - RN components

---

**Still need help? Open an issue on [GitHub](https://github.com/highskills123/Aibase/issues)**
