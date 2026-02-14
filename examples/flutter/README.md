# Flutter Examples

This directory contains comprehensive Flutter widget examples demonstrating various UI patterns and features that can be generated using Aibase.

## Examples Overview

### 1. Hello World (`01_hello_world.dart`)
**Type:** StatelessWidget  
**Description:** A simple Flutter app demonstrating basic widget structure with centered text.

**Generate with:**
```bash
python aibase.py -d "create a simple Flutter hello world app with centered text" -l flutter-widget
```

**Features:**
- MaterialApp setup
- StatelessWidget
- Scaffold with AppBar
- Center widget with styled Text

---

### 2. Counter App (`02_counter_app.dart`)
**Type:** StatefulWidget  
**Description:** Interactive counter app with increment, decrement, and reset functionality.

**Generate with:**
```bash
python aibase.py -d "create a Flutter counter app with increment and decrement buttons" -l flutter-widget
```

**Features:**
- StatefulWidget with state management
- Multiple FloatingActionButtons
- setState() for state updates
- Row layout with spacing
- Hero tags for multiple FABs

---

### 3. List View (`03_list_view.dart`)
**Type:** StatelessWidget with ListView.builder  
**Description:** Scrollable list displaying items with titles and descriptions.

**Generate with:**
```bash
python aibase.py -d "create a Flutter app with a scrollable list of items with titles and subtitles" -l flutter-widget
```

**Features:**
- ListView.builder for efficient list rendering
- Card widgets with elevation
- ListTile for structured item layout
- CircleAvatar for leading icons
- onTap handling with SnackBar feedback

---

### 4. Form with Validation (`04_form_validation.dart`)
**Type:** StatefulWidget with Form  
**Description:** Registration form with input validation for name, email, and password.

**Generate with:**
```bash
python aibase.py -d "create a Flutter form with text fields for name, email, password with validation" -l flutter-widget
```

**Features:**
- Form widget with GlobalKey
- TextFormField with validators
- Email regex validation
- Password visibility toggle
- TextEditingController management
- SingleChildScrollView for keyboard handling
- Custom validation functions

---

### 5. Navigation (`05_navigation.dart`)
**Type:** Multi-screen app with Navigator  
**Description:** App demonstrating navigation between home screen and detail screens.

**Generate with:**
```bash
python aibase.py -d "create a Flutter app with navigation between home screen and details screen" -l flutter-widget
```

**Features:**
- Multiple screens (HomeScreen, DetailScreen)
- Navigator.push for forward navigation
- Navigator.pop for back navigation
- Passing data between screens
- ListView with navigation items
- MaterialPageRoute

---

## How to Use These Examples

### 1. Using Aibase to Generate Similar Code

```bash
# Generate a widget
python aibase.py -d "your description here" -l flutter-widget -o output.dart

# Generate general Dart code
python aibase.py -d "your description here" -l dart -o output.dart

# Generate full Flutter app
python aibase.py -d "your description here" -l flutter -o output.dart
```

### 2. Running These Examples

1. Create a new Flutter project:
```bash
flutter create my_app
cd my_app
```

2. Replace `lib/main.dart` with the example code:
```bash
cp examples/flutter/01_hello_world.dart lib/main.dart
```

3. Run the app:
```bash
flutter run
```

### 3. Using the API

```python
import requests

url = "http://localhost:5000/api/translate"
data = {
    "description": "create a Flutter counter app",
    "language": "flutter-widget"
}

response = requests.post(url, json=data)
result = response.json()

if result["success"]:
    with open("generated_widget.dart", "w") as f:
        f.write(result["code"])
```

### 4. Using cURL

```bash
curl -X POST http://localhost:5000/api/translate \
  -H "Content-Type: application/json" \
  -d '{
    "description": "create a Flutter login screen with email and password fields",
    "language": "flutter-widget"
  }' | jq -r '.code' > login_screen.dart
```

## Common Widget Patterns

### StatelessWidget
Use when your widget doesn't need to maintain state:
- Display static content
- Pure presentation logic
- No user interaction that changes data

### StatefulWidget
Use when your widget needs to maintain state:
- User input and forms
- Counters and toggles
- Dynamic data that changes

### Best Practices Demonstrated

1. **Proper Disposal**: TextEditingControllers are properly disposed
2. **Const Constructors**: Used where applicable for performance
3. **Separation of Concerns**: UI and logic separated appropriately
4. **Responsive Design**: Using flexible layouts
5. **Material Design**: Following Flutter Material guidelines

## Dependencies

All examples use Flutter's built-in widgets and don't require additional packages. For production apps, you might want to add:

```yaml
# pubspec.yaml
dependencies:
  flutter:
    sdk: flutter
  # Add as needed:
  # provider: ^6.0.0  # State management
  # http: ^1.0.0      # API calls
  # shared_preferences: ^2.0.0  # Local storage
```

## Next Steps

1. Modify these examples to fit your needs
2. Combine patterns from multiple examples
3. Use Aibase to generate custom variations
4. Explore Flutter's extensive widget catalog
5. Check out the documentation in `docs/` directory

## Resources

- [Flutter Documentation](https://flutter.dev/docs)
- [Widget Catalog](https://flutter.dev/docs/development/ui/widgets)
- [Dart Language Tour](https://dart.dev/guides/language/language-tour)
- [Aibase Documentation](../../docs/)

## Contributing

Want to add more examples? See [Contributing Guidelines](../../docs/contributing-mobile.md)
