# Flutter Getting Started Guide

Welcome to generating Flutter code with Aibase! This guide will help you start generating Flutter widgets and Dart code using natural language descriptions.

## Table of Contents

1. [Introduction](#introduction)
2. [Prerequisites](#prerequisites)
3. [Installation](#installation)
4. [Basic Usage](#basic-usage)
5. [Language Options](#language-options)
6. [Common Use Cases](#common-use-cases)
7. [Tips and Best Practices](#tips-and-best-practices)
8. [Troubleshooting](#troubleshooting)

## Introduction

Aibase can generate Flutter widgets, Dart code, and complete Flutter applications from natural language descriptions. Whether you're building a simple button or a complex form, Aibase helps you generate clean, production-ready code.

## Prerequisites

Before you start, make sure you have:

1. **Aibase installed** - Follow the main [README](../README.md) for installation
2. **OpenAI API key** - Set in your `.env` file
3. **Flutter SDK** (optional, for running generated code) - [Install Flutter](https://flutter.dev/docs/get-started/install)

## Installation

If you haven't installed Aibase yet:

```bash
# Clone the repository
git clone https://github.com/highskills123/Aibase.git
cd Aibase

# Install dependencies
pip install -r requirements.txt

# Set up your API key
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

## Basic Usage

### Command Line Interface

#### 1. Generate a Simple Widget

```bash
python aibase.py -d "create a simple Flutter button widget" -l flutter-widget
```

#### 2. Generate and Save to File

```bash
python aibase.py -d "create a Flutter counter app" -l flutter-widget -o counter.dart
```

#### 3. Generate Without Comments

```bash
python aibase.py -d "create a Flutter login screen" -l flutter-widget --no-comments -o login.dart
```

### Interactive Mode

Start interactive mode for a conversational experience:

```bash
python aibase.py
```

Then:
1. Enter your description: "create a Flutter StatefulWidget with a counter"
2. Choose language: "flutter-widget"
3. View generated code

### Programmatic Usage

Use Aibase in your Python scripts:

```python
from aibase import AibaseTranslator

# Initialize
translator = AibaseTranslator()

# Generate Flutter widget
code = translator.translate(
    description="create a Flutter card widget with an image and title",
    target_language="flutter-widget",
    include_comments=True
)

print(code)

# Save to file
with open("card_widget.dart", "w") as f:
    f.write(code)
```

### REST API

Start the API server:

```bash
python api_server.py
```

Then make requests:

```bash
curl -X POST http://localhost:5000/api/translate \
  -H "Content-Type: application/json" \
  -d '{
    "description": "create a Flutter app bar with a title and actions",
    "language": "flutter-widget"
  }'
```

## Language Options

Aibase supports multiple Flutter-related language options:

### 1. `flutter-widget`
**Best for:** Individual widgets and components

```bash
python aibase.py -d "create a StatelessWidget that displays a greeting" -l flutter-widget
```

**Generates:** Complete widget code with imports and class definition

### 2. `flutter`
**Best for:** Full Flutter applications

```bash
python aibase.py -d "create a complete Flutter todo app" -l flutter
```

**Generates:** Full app with main(), MaterialApp, and screens

### 3. `dart`
**Best for:** Pure Dart code (no Flutter)

```bash
python aibase.py -d "create a Dart class for managing user data" -l dart
```

**Generates:** Dart code without Flutter dependencies

## Common Use Cases

### 1. Basic Widgets

#### StatelessWidget
```bash
python aibase.py -d "create a StatelessWidget that shows a centered text" -l flutter-widget
```

#### StatefulWidget
```bash
python aibase.py -d "create a StatefulWidget with a counter that increments on button press" -l flutter-widget
```

### 2. UI Components

#### Custom Button
```bash
python aibase.py -d "create a custom rounded button widget with gradient background" -l flutter-widget
```

#### Card Widget
```bash
python aibase.py -d "create a card widget with image, title, subtitle, and action buttons" -l flutter-widget
```

### 3. Forms

#### Login Form
```bash
python aibase.py -d "create a Flutter login form with email and password fields, validation, and submit button" -l flutter-widget -o login_screen.dart
```

#### Registration Form
```bash
python aibase.py -d "create a registration form with name, email, password, confirm password with validation" -l flutter-widget -o register_screen.dart
```

### 4. Lists

#### Simple List
```bash
python aibase.py -d "create a ListView with 10 items showing title and subtitle" -l flutter-widget
```

#### Grid View
```bash
python aibase.py -d "create a GridView showing product cards with images" -l flutter-widget
```

### 5. Navigation

#### Multi-Screen App
```bash
python aibase.py -d "create a Flutter app with home screen and detail screen with navigation" -l flutter
```

#### Bottom Navigation
```bash
python aibase.py -d "create a Flutter app with bottom navigation bar and three tabs" -l flutter
```

### 6. Advanced Features

#### API Integration
```bash
python aibase.py -d "create a Flutter widget that fetches and displays user data from an API" -l flutter-widget
```

#### State Management
```bash
python aibase.py -d "create a Flutter StatefulWidget with Provider for state management" -l flutter-widget
```

## Tips and Best Practices

### Writing Good Descriptions

#### ✅ Good Descriptions (Specific and Clear)

```
"create a Flutter StatefulWidget counter app with increment, decrement, and reset buttons"

"create a login screen with email and password TextFields, validation, and a submit button"

"create a product card widget with image, title, price, and add to cart button"
```

#### ❌ Poor Descriptions (Too Vague)

```
"make an app"
"create a widget"
"something with buttons"
```

### Best Practices

1. **Be Specific About Widget Types**
   - Mention "StatelessWidget" or "StatefulWidget"
   - Specify if you need "MaterialApp", "Scaffold", etc.

2. **Describe the UI Structure**
   - Mention layout: "Column", "Row", "Stack"
   - Describe positioning: "centered", "at the top"
   - Include styling details: "with blue background", "rounded corners"

3. **Include Functionality**
   - Describe interactions: "on button press", "when tapped"
   - Mention state changes: "updates counter", "toggles visibility"
   - Specify validation: "validate email format", "required fields"

4. **Specify Dependencies If Needed**
   - "using http package"
   - "with provider for state management"
   - "using cached_network_image"

### Example: Evolving a Description

**Basic:**
```
"create a button"
```

**Better:**
```
"create a Flutter button widget"
```

**Even Better:**
```
"create a Flutter ElevatedButton with text label"
```

**Best:**
```
"create a custom Flutter button widget with rounded corners, gradient background, and icon, that shows a loading indicator when pressed"
```

## Troubleshooting

### Issue: Generated code has import errors

**Solution:** Make sure you have the required dependencies in your `pubspec.yaml`

```yaml
dependencies:
  flutter:
    sdk: flutter
  # Add any additional packages the generated code uses
```

### Issue: Widget doesn't compile

**Solution:** 
1. Check for missing imports
2. Verify widget names are unique
3. Ensure all required parameters are provided
4. Try regenerating with more specific description

### Issue: Code is too complex or too simple

**Solution:** Adjust your description:
- For simpler code: Be more concise, ask for basic implementation
- For more complex code: Add more details, mention advanced features

### Issue: Generated code doesn't match expectations

**Solution:**
1. Refine your description to be more specific
2. Try generating multiple times with slight variations
3. Use the `--temperature` parameter to adjust creativity:
   ```bash
   python aibase.py -d "your description" -l flutter-widget --temperature 0.3
   ```
   - Lower values (0.1-0.3): More focused, deterministic
   - Higher values (0.7-0.9): More creative, varied

### Issue: Want to customize generation parameters

**Solution:** Use advanced options:

```bash
python aibase.py \
  -d "create a Flutter widget" \
  -l flutter-widget \
  --model gpt-4 \
  --temperature 0.5 \
  --max-tokens 3000 \
  -o output.dart
```

## Next Steps

1. **Explore Examples** - Check out `examples/flutter/` directory for complete examples
2. **Read Best Practices** - See [docs/best-practices.md](best-practices.md)
3. **Try Advanced Features** - Learn about [API usage](api-mobile-frameworks.md)
4. **Follow Tutorials** - Complete step-by-step tutorials in [docs/tutorials/](tutorials/)
5. **Join the Community** - Share your creations and get help

## Additional Resources

- [Flutter Documentation](https://flutter.dev/docs)
- [Dart Language Tour](https://dart.dev/guides/language/language-tour)
- [Flutter Widget Catalog](https://flutter.dev/docs/development/ui/widgets)
- [Aibase API Documentation](api-mobile-frameworks.md)
- [Troubleshooting Guide](tutorials/troubleshooting.md)

## Need Help?

- Check [Troubleshooting Guide](tutorials/troubleshooting.md)
- Review [Flutter Examples](../examples/flutter/)
- Open an issue on [GitHub](https://github.com/highskills123/Aibase/issues)

---

**Happy Flutter coding with Aibase! 🚀**
