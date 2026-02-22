# Extending Generators

This guide explains how to extend Aibase to add new language support, custom generators, and specialized features.

## Table of Contents

1. [Adding New Languages](#adding-new-languages)
2. [Custom Prompt Engineering](#custom-prompt-engineering)
3. [Post-Processing](#post-processing)
4. [Adding Templates](#adding-templates)
5. [Creating Custom Generators](#creating-custom-generators)

## Adding New Languages

### Basic Language Support

To add a new programming language or framework:

**Step 1: Update SUPPORTED_LANGUAGES**

Edit `aibase.py`:

```python
SUPPORTED_LANGUAGES = {
    # ... existing languages
    
    # Add your new language
    'vue': 'Vue.js',
    'svelte': 'Svelte',
    'angular': 'Angular'
}
```

**Step 2: Test the Addition**

```bash
# Test with CLI
python aibase.py -d "create a component" -l vue

# Test with API
curl -X POST http://localhost:5000/api/translate \
  -H "Content-Type: application/json" \
  -d '{"description": "create a component", "language": "vue"}'
```

That's it! The AI model will understand the language name and generate appropriate code.

### Advanced Language Support with Custom Prompts

For better results, add language-specific prompt engineering:

**Step 1: Create Language-Specific Prompt Method**

```python
class AibaseTranslator:
    # ... existing code
    
    def _get_language_specific_instructions(self, language):
        """Get additional instructions for specific languages"""
        
        instructions = {
            'flutter-widget': (
                "Generate a complete Flutter widget following these guidelines:\n"
                "- Include all necessary imports\n"
                "- Follow Material Design principles\n"
                "- Use proper widget lifecycle methods\n"
                "- Add const constructors where applicable\n"
                "- Include proper state management"
            ),
            'react-native-component': (
                "Generate a React Native component following these guidelines:\n"
                "- Use functional components with hooks\n"
                "- Include SafeAreaView for proper display\n"
                "- Use StyleSheet.create for styling\n"
                "- Add Platform-specific code where needed\n"
                "- Follow React best practices"
            ),
            'vue': (
                "Generate a Vue.js component following these guidelines:\n"
                "- Use Vue 3 Composition API\n"
                "- Include template, script, and style sections\n"
                "- Use TypeScript if appropriate\n"
                "- Follow Vue.js best practices"
            )
        }
        
        return instructions.get(language, "")
```

**Step 2: Update translate Method**

```python
def translate(self, description, target_language='python', include_comments=True):
    # ... existing validation code
    
    lang_name = self.SUPPORTED_LANGUAGES[target_language.lower()]
    additional_instructions = self._get_language_specific_instructions(target_language.lower())
    
    system_prompt = (
        f"You are an expert programmer that translates natural language descriptions "
        f"into clean, efficient, and well-structured {lang_name} code. "
        f"{additional_instructions}\n"
        f"Provide only the code without additional explanations unless specifically asked. "
        f"{'Include helpful comments to explain the code.' if include_comments else 'Minimize comments.'}"
    )
    
    # ... rest of the method
```

## Custom Prompt Engineering

### Creating a Custom Translator Class

For full control over prompt generation:

```python
from aibase import AibaseTranslator

class CustomFlutterTranslator(AibaseTranslator):
    """Custom translator with Flutter-specific enhancements"""
    
    def translate(self, description, target_language='flutter-widget', include_comments=True):
        # Add custom preprocessing
        if target_language in ['flutter', 'flutter-widget']:
            description = self._preprocess_flutter_description(description)
        
        # Call parent translate
        code = super().translate(description, target_language, include_comments)
        
        # Add custom postprocessing
        if target_language in ['flutter', 'flutter-widget']:
            code = self._postprocess_flutter_code(code)
        
        return code
    
    def _preprocess_flutter_description(self, description):
        """Add Flutter-specific context to description"""
        # Automatically mention Material Design if not specified
        if 'material' not in description.lower() and 'cupertino' not in description.lower():
            description += " (use Material Design widgets)"
        return description
    
    def _postprocess_flutter_code(self, code):
        """Clean up and enhance generated Flutter code"""
        # Ensure imports are present
        if "import 'package:flutter/material.dart';" not in code:
            code = "import 'package:flutter/material.dart';\n\n" + code
        
        # Add other enhancements as needed
        return code
```

**Usage:**

```python
translator = CustomFlutterTranslator()
code = translator.translate(
    "create a login screen",
    target_language="flutter-widget"
)
```

### Dynamic Prompt Modification

```python
class DynamicTranslator(AibaseTranslator):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.custom_instructions = {}
    
    def add_instruction(self, language, instruction):
        """Add custom instruction for a language"""
        if language not in self.custom_instructions:
            self.custom_instructions[language] = []
        self.custom_instructions[language].append(instruction)
    
    def translate(self, description, target_language='python', include_comments=True):
        # Modify description with custom instructions
        if target_language in self.custom_instructions:
            for instruction in self.custom_instructions[target_language]:
                description += f"\n{instruction}"
        
        return super().translate(description, target_language, include_comments)

# Usage
translator = DynamicTranslator()
translator.add_instruction('flutter-widget', 'Use Provider for state management')
translator.add_instruction('flutter-widget', 'Add error handling')
code = translator.translate("create a data fetching widget", "flutter-widget")
```

## Post-Processing

### Adding Code Formatters

```python
import subprocess

class FormattedTranslator(AibaseTranslator):
    def translate(self, description, target_language='python', include_comments=True):
        code = super().translate(description, target_language, include_comments)
        return self._format_code(code, target_language)
    
    def _format_code(self, code, language):
        """Format code using language-specific formatters"""
        if language == 'python':
            return self._format_python(code)
        elif language in ['flutter', 'flutter-widget', 'dart']:
            return self._format_dart(code)
        elif language in ['react-native', 'javascript']:
            return self._format_javascript(code)
        return code
    
    def _format_python(self, code):
        """Format Python code with black"""
        try:
            # Save to temp file
            with open('/tmp/temp.py', 'w') as f:
                f.write(code)
            
            # Run black
            subprocess.run(['black', '/tmp/temp.py'], check=True)
            
            # Read formatted code
            with open('/tmp/temp.py', 'r') as f:
                return f.read()
        except:
            return code  # Return original if formatting fails
    
    def _format_dart(self, code):
        """Format Dart code with dart format"""
        try:
            result = subprocess.run(
                ['dart', 'format'],
                input=code.encode(),
                capture_output=True,
                check=True
            )
            return result.stdout.decode()
        except:
            return code
    
    def _format_javascript(self, code):
        """Format JavaScript with prettier"""
        try:
            result = subprocess.run(
                ['npx', 'prettier', '--parser', 'babel'],
                input=code.encode(),
                capture_output=True,
                check=True
            )
            return result.stdout.decode()
        except:
            return code
```

### Adding Validation

```python
class ValidatingTranslator(AibaseTranslator):
    def translate(self, description, target_language='python', include_comments=True):
        code = super().translate(description, target_language, include_comments)
        
        # Validate generated code
        if not self._validate_code(code, target_language):
            # Retry with more explicit instructions
            description += "\nEnsure the code is syntactically correct and complete."
            code = super().translate(description, target_language, include_comments)
        
        return code
    
    def _validate_code(self, code, language):
        """Basic validation of generated code"""
        if language == 'python':
            return self._validate_python(code)
        elif language in ['dart', 'flutter', 'flutter-widget']:
            return self._validate_dart(code)
        # Add more validators
        return True
    
    def _validate_python(self, code):
        """Validate Python syntax"""
        try:
            compile(code, '<string>', 'exec')
            return True
        except SyntaxError:
            return False
    
    def _validate_dart(self, code):
        """Basic Dart validation"""
        # Check for required imports
        if 'import' not in code and 'class' in code:
            return False
        # Add more checks
        return True
```

## Adding Templates

### Creating a Template System

```python
import os
import json

class TemplateTranslator(AibaseTranslator):
    def __init__(self, *args, template_dir='templates', **kwargs):
        super().__init__(*args, **kwargs)
        self.template_dir = template_dir
        self.templates = self._load_templates()
    
    def _load_templates(self):
        """Load templates from directory"""
        templates = {}
        if os.path.exists(self.template_dir):
            for filename in os.listdir(self.template_dir):
                if filename.endswith('.json'):
                    path = os.path.join(self.template_dir, filename)
                    with open(path, 'r') as f:
                        template_name = filename[:-5]  # Remove .json
                        templates[template_name] = json.load(f)
        return templates
    
    def generate_from_template(self, template_name, params):
        """Generate code from a template"""
        if template_name not in self.templates:
            raise ValueError(f"Template {template_name} not found")
        
        template = self.templates[template_name]
        
        # Build description from template
        description = template['base_description']
        for key, value in params.items():
            description += f"\n{template.get(key, '')}: {value}"
        
        return self.translate(
            description,
            template.get('language', 'python'),
            template.get('include_comments', True)
        )
```

**Template Example** (`templates/flutter-login.json`):

```json
{
  "name": "Flutter Login Screen",
  "base_description": "create a Flutter login screen with Material Design",
  "language": "flutter-widget",
  "include_comments": true,
  "fields": "with text fields for",
  "validation": "include validation for",
  "actions": "with buttons for",
  "styling": "styled with"
}
```

**Usage:**

```python
translator = TemplateTranslator()
code = translator.generate_from_template('flutter-login', {
    'fields': 'email and password',
    'validation': 'email format and required fields',
    'actions': 'submit and forgot password',
    'styling': 'blue theme and rounded inputs'
})
```

## Creating Custom Generators

### Specialized Generator Class

```python
class FlutterGenerator:
    """Specialized generator for Flutter code"""
    
    def __init__(self, translator=None):
        self.translator = translator or AibaseTranslator()
    
    def generate_widget(self, widget_type, name, description, **kwargs):
        """Generate a Flutter widget"""
        full_description = f"create a Flutter {widget_type} named {name} that {description}"
        
        if kwargs.get('stateful'):
            full_description += " (use StatefulWidget)"
        else:
            full_description += " (use StatelessWidget)"
        
        if kwargs.get('material_design'):
            full_description += " following Material Design"
        
        return self.translator.translate(full_description, 'flutter-widget')
    
    def generate_screen(self, name, components, navigation=False):
        """Generate a complete screen"""
        description = f"create a Flutter screen named {name} with "
        description += ", ".join(components)
        
        if navigation:
            description += ", include navigation back button"
        
        return self.translator.translate(description, 'flutter-widget')
    
    def generate_form(self, fields, validation=True, submit_handler=True):
        """Generate a form widget"""
        description = "create a Flutter form with fields: " + ", ".join(fields)
        
        if validation:
            description += " with validation"
        
        if submit_handler:
            description += " and a submit button with handler"
        
        return self.translator.translate(description, 'flutter-widget')

# Usage
generator = FlutterGenerator()

# Generate widget
button = generator.generate_widget(
    'ElevatedButton',
    'CustomButton',
    'has text label and icon',
    stateful=False,
    material_design=True
)

# Generate screen
screen = generator.generate_screen(
    'ProfileScreen',
    ['avatar image', 'username', 'bio text', 'edit button'],
    navigation=True
)

# Generate form
form = generator.generate_form(
    ['name', 'email', 'phone'],
    validation=True,
    submit_handler=True
)
```

### React Native Generator

```python
class ReactNativeGenerator:
    """Specialized generator for React Native code"""
    
    def __init__(self, translator=None):
        self.translator = translator or AibaseTranslator()
    
    def generate_component(self, name, description, hooks=None):
        """Generate a React Native component"""
        full_description = f"create a React Native functional component named {name} that {description}"
        
        if hooks:
            full_description += f" using hooks: {', '.join(hooks)}"
        
        return self.translator.translate(full_description, 'react-native-component')
    
    def generate_screen(self, name, sections, navigation_params=None):
        """Generate a screen component"""
        description = f"create a React Native screen component named {name} with sections: "
        description += ", ".join(sections)
        
        if navigation_params:
            description += f" that receives navigation params: {', '.join(navigation_params)}"
        
        return self.translator.translate(description, 'react-native-component')
    
    def generate_list_component(self, item_structure, data_source='data'):
        """Generate a FlatList component"""
        description = f"create a React Native FlatList component displaying items with "
        description += ", ".join(item_structure)
        description += f" from {data_source} prop"
        
        return self.translator.translate(description, 'react-native-component')

# Usage
generator = ReactNativeGenerator()

# Generate component
card = generator.generate_component(
    'ProductCard',
    'displays product image, title, price, and add to cart button',
    hooks=['useState']
)

# Generate screen
profile = generator.generate_screen(
    'ProfileScreen',
    ['header with avatar', 'user info section', 'posts list'],
    navigation_params=['userId']
)

# Generate list
list_view = generator.generate_list_component(
    ['thumbnail image', 'title', 'subtitle', 'action button'],
    data_source='items'
)
```

## Integration with API

### Adding Custom Endpoints

Edit `api_server.py`:

```python
@app.route('/api/generate/flutter-widget', methods=['POST'])
def generate_flutter_widget():
    """Specialized endpoint for Flutter widgets"""
    data = request.get_json()
    
    if not data or 'widget_type' not in data:
        return jsonify({"success": False, "error": "widget_type is required"}), 400
    
    generator = FlutterGenerator()
    
    try:
        code = generator.generate_widget(
            widget_type=data['widget_type'],
            name=data.get('name', 'CustomWidget'),
            description=data.get('description', ''),
            stateful=data.get('stateful', False),
            material_design=data.get('material_design', True)
        )
        
        return jsonify({
            "success": True,
            "code": code,
            "language": "flutter-widget"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
```

## Testing Custom Generators

```python
import unittest
from unittest.mock import Mock, patch

class TestCustomGenerator(unittest.TestCase):
    def setUp(self):
        self.mock_translator = Mock()
        self.generator = FlutterGenerator(self.mock_translator)
    
    def test_generate_widget(self):
        """Test widget generation"""
        self.mock_translator.translate.return_value = "class CustomWidget..."
        
        result = self.generator.generate_widget(
            'ElevatedButton',
            'MyButton',
            'has text',
            stateful=False
        )
        
        self.assertIn('CustomWidget', result)
        self.mock_translator.translate.assert_called_once()
    
    def test_generate_form(self):
        """Test form generation"""
        self.mock_translator.translate.return_value = "class FormWidget..."
        
        result = self.generator.generate_form(
            ['name', 'email'],
            validation=True
        )
        
        self.assertIsNotNone(result)

if __name__ == '__main__':
    unittest.main()
```

## Best Practices for Extensions

1. **Maintain Backward Compatibility**: Don't break existing functionality
2. **Add Tests**: Test new generators thoroughly
3. **Document**: Add documentation for new features
4. **Follow Conventions**: Match existing code style
5. **Error Handling**: Handle errors gracefully
6. **Performance**: Consider caching for repeated requests

## Contributing Back

If you create useful extensions:

1. Open an issue describing the enhancement
2. Submit a pull request with your changes
3. Include tests and documentation
4. Follow the [Contributing Guide](contributing-mobile.md)

## Related Documentation

- [Architecture Overview](architecture-overview.md)
- [Contributing Guide](contributing-mobile.md)
- [API Documentation](api-mobile-frameworks.md)

---

**Questions? Open an issue on [GitHub](https://github.com/highskills123/Aibase/issues)**
