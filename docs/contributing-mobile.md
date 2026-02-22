# Contributing to Aibase - Mobile Framework Features

Thank you for your interest in contributing to Aibase's mobile framework features! This guide will help you contribute effectively to Flutter and React Native code generation.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Development Setup](#development-setup)
3. [Contributing Areas](#contributing-areas)
4. [Contribution Workflow](#contribution-workflow)
5. [Code Guidelines](#code-guidelines)
6. [Testing](#testing)
7. [Documentation](#documentation)
8. [Pull Request Process](#pull-request-process)

## Getting Started

### Prerequisites

- Python 3.7+
- Git
- GitHub account
- Ollama installed (https://ollama.com)
- (Optional) Flutter SDK for testing Flutter examples
- (Optional) React Native environment for testing RN examples

### Ways to Contribute

- 🐛 **Bug Reports**: Report issues with mobile code generation
- 💡 **Feature Requests**: Suggest new mobile framework features
- 📝 **Documentation**: Improve guides, examples, or tutorials
- 🎨 **Examples**: Add new Flutter or React Native examples
- 🔧 **Code**: Fix bugs or implement features
- 🧪 **Testing**: Add or improve tests

## Development Setup

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then:
git clone https://github.com/YOUR_USERNAME/Aibase.git
cd Aibase

# Add upstream remote
git remote add upstream https://github.com/highskills123/Aibase.git
```

### 2. Create Development Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies (if any)
pip install pytest black flake8
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env if you want to customize Ollama settings
```

### 4. Verify Setup

```bash
# Verify setup
python aibase.py --help

# Try generation
python aibase.py -d "test" -l flutter-widget
```

## Contributing Areas

### 1. Examples

**What to Contribute:**
- New Flutter widget examples
- New React Native component examples
- Real-world use cases
- Advanced patterns

**Location:** `examples/flutter/` or `examples/react-native/`

**Example Contribution:**
```dart
// examples/flutter/06_animated_widget.dart
// Flutter Animated Widget Example
// Generated using: python aibase.py -d "..." -l flutter-widget

import 'package:flutter/material.dart';

// ... your example code
```

**Guidelines:**
- Follow existing example structure
- Include generation command in comments
- Add description and features in comment header
- Update README.md in examples directory
- Ensure code runs without errors

### 2. Documentation

**What to Contribute:**
- Improve getting started guides
- Add tutorials
- Fix typos or unclear sections
- Add troubleshooting tips
- Translate documentation

**Location:** `docs/`

**Guidelines:**
- Use clear, simple language
- Include code examples
- Add practical use cases
- Follow existing documentation style
- Test code examples

### 3. Language Support

**What to Contribute:**
- Add new mobile framework support
- Improve prompt engineering for existing languages
- Add language-specific validations

**Example:**
```python
# In aibase.py
SUPPORTED_LANGUAGES = {
    # ... existing
    'swiftui': 'SwiftUI',  # New addition
    'jetpack-compose': 'Jetpack Compose'
}
```

### 4. API Enhancements

**What to Contribute:**
- New API endpoints
- Improved error handling
- Request validation
- Response formatting

**Location:** `api_server.py`

### 5. Testing

**What to Contribute:**
- Unit tests for new features
- Integration tests
- Test fixtures
- Test documentation

**Location:** Add test files as needed in the repository root.

## Contribution Workflow

### 1. Create a Branch

```bash
# Update your fork
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/add-flutter-animation-example
```

### 2. Make Changes

Follow the code guidelines and make your changes.

### 3. Test Your Changes

```bash
# Test manually
python aibase.py -d "test your feature" -l flutter-widget

# Test API if applicable
python api_server.py
curl -X POST http://localhost:5000/api/translate ...
```

### 4. Commit Changes

```bash
# Stage changes
git add .

# Commit with descriptive message
git commit -m "Add Flutter animation example with setState

- Add animated container example
- Include start/stop animation controls
- Update examples README
- Add generation instructions"
```

**Commit Message Guidelines:**
- Use present tense ("Add feature" not "Added feature")
- First line: Brief summary (50 chars or less)
- Blank line, then detailed description if needed
- Reference issues: "Fixes #123" or "Related to #456"

### 5. Push and Create PR

```bash
# Push to your fork
git push origin feature/add-flutter-animation-example
```

Then create a Pull Request on GitHub.

## Code Guidelines

### Python Code Style

Follow PEP 8:

```python
# Good
def translate_code(description, language):
    """Translate natural language to code."""
    if not description:
        raise ValueError("Description is required")
    return generated_code

# Use type hints where appropriate
def translate(self, description: str, language: str = 'python') -> str:
    pass
```

**Run Linter:**
```bash
flake8 aibase.py api_server.py
black aibase.py api_server.py
```

### Flutter Code Style

Follow Dart/Flutter conventions:

```dart
// Good
class CustomWidget extends StatelessWidget {
  const CustomWidget({Key? key}) : super(key: key);
  
  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16.0),
      child: Text('Hello'),
    );
  }
}
```

### React Native Code Style

Follow React/JavaScript conventions:

```javascript
// Good
const CustomComponent = ({ title, onPress }) => {
  const [count, setCount] = useState(0);
  
  return (
    <View style={styles.container}>
      <Text>{title}</Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 16,
  },
});

export default CustomComponent;
```

### Documentation Style

```markdown
# Clear Headings

Use descriptive headings and organize content hierarchically.

## Code Examples

Always include code examples:

\`\`\`bash
python aibase.py -d "example" -l flutter-widget
\`\`\`

## Lists

- Use bullet points
- Keep items concise
- Parallel structure
```

## Testing

### Running Tests

```bash
# Test manually
python aibase.py -d "test" -l flutter-widget
```

### Writing Tests

Add tests for new features:

```python
def test_flutter_widget_generation():
    """Test Flutter widget generation"""
    translator = AibaseTranslator()
    
    code = translator.translate(
        "create a simple widget",
        "flutter-widget"
    )
    
    # Assertions
    assert code is not None
    assert len(code) > 0
    assert 'Widget' in code or 'class' in code
```

### Manual Testing Checklist

For new examples:

- [ ] Code runs without errors
- [ ] Follows framework best practices
- [ ] Includes proper imports
- [ ] Has appropriate styling
- [ ] Handles edge cases
- [ ] Works on target platforms

## Documentation

### Documentation Requirements

All contributions should include:

1. **Code Comments**: For complex logic
2. **Docstrings**: For functions and classes
3. **README Updates**: For new features
4. **Example Documentation**: For new examples
5. **API Documentation**: For API changes

### Example Documentation

```python
def generate_widget(self, widget_type, name, description, **kwargs):
    """
    Generate a Flutter widget with specified parameters.
    
    Args:
        widget_type (str): Type of widget (e.g., 'StatelessWidget')
        name (str): Widget class name
        description (str): Natural language description
        **kwargs: Additional options:
            - stateful (bool): Use StatefulWidget if True
            - material_design (bool): Follow Material Design
    
    Returns:
        str: Generated Flutter widget code
    
    Example:
        >>> generator = FlutterGenerator()
        >>> code = generator.generate_widget('Button', 'MyButton', 'has icon')
        >>> print(code)
    """
    # Implementation
```

## Pull Request Process

### Before Submitting

- [ ] Code follows style guidelines
- [ ] All tests pass
- [ ] New tests added for new features
- [ ] Documentation updated
- [ ] Examples tested (if applicable)
- [ ] Commit messages are clear
- [ ] No merge conflicts with main

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Example addition
- [ ] Code refactoring

## Testing
Describe how you tested the changes

## Related Issues
Fixes #123
Related to #456

## Screenshots (if applicable)
Add screenshots for UI changes

## Checklist
- [ ] Code follows style guidelines
- [ ] Tests pass
- [ ] Documentation updated
- [ ] Examples tested
```

### Review Process

1. **Automated Checks**: CI/CD runs tests
2. **Code Review**: Maintainer reviews code
3. **Feedback**: Address review comments
4. **Approval**: Maintainer approves PR
5. **Merge**: PR is merged to main

### After Merge

```bash
# Update your fork
git checkout main
git pull upstream main
git push origin main

# Delete feature branch
git branch -d feature/your-feature
git push origin --delete feature/your-feature
```

## Examples of Good Contributions

### Example 1: Adding Flutter Example

```dart
// examples/flutter/07_api_integration.dart
// Flutter API Integration Example
// Fetches and displays data from REST API
// Generated using: python aibase.py -d "create a Flutter widget that fetches user data from API" -l flutter-widget

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

// ... complete working example
```

**With README Update:**
```markdown
### 7. API Integration (`07_api_integration.dart`)
**Description:** Demonstrates fetching data from REST API
**Features:**
- HTTP requests with http package
- JSON parsing
- Loading states
- Error handling
```

### Example 2: Documentation Improvement

```markdown
## Common Issues

### Issue: Generated Flutter code has import errors

**Problem:** Missing package import

**Solution:**
Add the required package to `pubspec.yaml`:

\`\`\`yaml
dependencies:
  flutter:
    sdk: flutter
  http: ^0.13.0  # Add this
\`\`\`

Then run:
\`\`\`bash
flutter pub get
\`\`\`
```

## Getting Help

- **Questions**: Open a [Discussion](https://github.com/highskills123/Aibase/discussions)
- **Bugs**: Open an [Issue](https://github.com/highskills123/Aibase/issues)
- **Chat**: Join our community (if available)

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on code, not person
- Help newcomers
- Follow project guidelines

## Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Recognized in project documentation

## Thank You!

Every contribution helps make Aibase better. We appreciate your time and effort! 🎉

---

**Questions? Open an issue or discussion on [GitHub](https://github.com/highskills123/Aibase)**
