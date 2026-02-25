# Tutorial: Generate Your First Flutter Widget

This step-by-step tutorial will guide you through generating your first Flutter widget using Aibase.

## What You'll Learn

- How to use Aibase CLI to generate Flutter widgets
- How to run generated Flutter code
- How to customize generation parameters
- Best practices for describing widgets

## Prerequisites

- Aibase installed ([Installation Guide](../README.md))
- Ollama installed and running with model pulled (see README)
- (Optional) Flutter SDK for running the widget

## Step 1: Verify Setup

First, let's verify Aibase is working:

```bash
# Check if aibase.py runs
python aibase.py --help
```

You should see the help message with available options.

## Step 2: Generate a Simple Widget

Let's start with a simple "Hello World" widget.

### Using CLI

```bash
python aibase.py \
  -d "create a Flutter StatelessWidget that displays 'Hello, Flutter!' in the center of the screen" \
  -l flutter-widget \
  -o hello_widget.dart
```

**Explanation:**
- `-d`: Description of what you want
- `-l flutter-widget`: Target language
- `-o`: Output file name

### Expected Output

You should see:
```
Generating code...
...
Code saved to: hello_widget.dart
```

### View the Generated Code

```bash
cat hello_widget.dart
```

You'll see something like:

```dart
import 'package:flutter/material.dart';

class HelloWidget extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Hello Widget'),
      ),
      body: Center(
        child: Text(
          'Hello, Flutter!',
          style: TextStyle(fontSize: 24),
        ),
      ),
    );
  }
}
```

## Step 3: Run the Widget

### Create a Flutter Project

```bash
flutter create my_first_app
cd my_first_app
```

### Replace main.dart

```bash
# Copy generated widget
cp ../hello_widget.dart lib/hello_widget.dart
```

### Update lib/main.dart

```dart
import 'package:flutter/material.dart';
import 'hello_widget.dart';

void main() {
  runApp(MyApp());
}

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'My First App',
      home: HelloWidget(),
    );
  }
}
```

### Run the App

```bash
flutter run
```

🎉 You should see your widget running!

## Step 4: Generate a StatefulWidget

Now let's generate something more interactive.

```bash
python aibase.py \
  -d "create a Flutter StatefulWidget counter with increment and decrement buttons" \
  -l flutter-widget \
  -o counter_widget.dart
```

### View the Result

```bash
cat counter_widget.dart
```

You'll see a complete counter widget with state management!

## Step 5: Customize Generation

### Add More Details

More specific descriptions generate better code:

```bash
python aibase.py \
  -d "create a Flutter StatefulWidget counter with:
  - A large counter display in the center
  - Increment button (green with + icon)
  - Decrement button (red with - icon)
  - Reset button (gray)
  - Material Design styling" \
  -l flutter-widget \
  -o styled_counter.dart
```

### Adjust Creativity

Use `--temperature` to control creativity:

```bash
# More consistent (less creative)
python aibase.py \
  -d "create a simple button widget" \
  -l flutter-widget \
  --temperature 0.3

# More creative (more varied)
python aibase.py \
  -d "create a simple button widget" \
  -l flutter-widget \
  --temperature 0.9
```

### Generate Without Comments

```bash
python aibase.py \
  -d "create a simple Flutter widget" \
  -l flutter-widget \
  --no-comments \
  -o clean_widget.dart
```

## Step 6: Generate a Form

Let's generate something more complex:

```bash
python aibase.py \
  -d "create a Flutter login form with:
  - Email TextFormField with validation
  - Password TextFormField with show/hide toggle
  - Remember me checkbox
  - Login button
  - Forgot password link
  - Material Design styling" \
  -l flutter-widget \
  -o login_form.dart
```

This generates a complete, working form with validation!

## Step 7: Using the API

Instead of CLI, you can use the API:

### Start API Server

```bash
python api_server.py
```

### Generate via API

```bash
curl -X POST http://localhost:5000/api/translate \
  -H "Content-Type: application/json" \
  -d '{
    "description": "create a Flutter card widget with image and title",
    "language": "flutter-widget"
  }' | jq -r '.code' > card_widget.dart
```

## Step 8: Interactive Mode

For experimentation, use interactive mode:

```bash
python aibase.py
```

Then follow the prompts:
```
Enter your description: create a Flutter widget with a list of items
Target language: flutter-widget
```

## Common Patterns

### Simple Display Widget

```bash
python aibase.py \
  -d "create a Flutter Text widget displaying a welcome message" \
  -l flutter-widget
```

### Layout Widget

```bash
python aibase.py \
  -d "create a Flutter Column with 3 containers of different colors" \
  -l flutter-widget
```

### Interactive Widget

```bash
python aibase.py \
  -d "create a Flutter toggle switch that changes background color" \
  -l flutter-widget
```

### List Widget

```bash
python aibase.py \
  -d "create a Flutter ListView with 10 items showing title and subtitle" \
  -l flutter-widget
```

## Tips for Better Results

### 1. Be Specific About Widget Type

✅ Good:
```
"create a Flutter StatefulWidget counter"
```

❌ Too vague:
```
"create a counter"
```

### 2. Include Layout Details

✅ Good:
```
"create a Flutter Column with centered text and a button at the bottom"
```

❌ Missing details:
```
"create text and button"
```

### 3. Specify Styling

✅ Good:
```
"create a button with blue background, white text, and rounded corners"
```

❌ Generic:
```
"create a button"
```

### 4. Mention Material Design

```
"create a card widget following Material Design guidelines"
```

## Troubleshooting

### Issue: Import Errors

**Solution:** Ensure your pubspec.yaml has:
```yaml
dependencies:
  flutter:
    sdk: flutter
```

### Issue: Widget Won't Compile

**Solution:** Try regenerating with more specific description:
```bash
python aibase.py \
  -d "create a complete, compilable Flutter StatelessWidget" \
  -l flutter-widget
```

### Issue: Output Too Simple

**Solution:** Add more details to description or use higher temperature:
```bash
python aibase.py \
  -d "detailed description here" \
  -l flutter-widget \
  --temperature 0.7 \
  --max-tokens 3000
```

## Next Steps

1. **Explore Examples**: Check `examples/flutter/` for more examples
2. **Try Complex Widgets**: Generate forms, lists, navigation
3. **Customize**: Experiment with different parameters
4. **Build an App**: Combine multiple generated widgets
5. **Read More**: Check [Flutter Getting Started](../flutter-getting-started.md)

## Practice Exercises

Try generating these on your own:

1. **Exercise 1**: Profile card widget with avatar, name, and bio
2. **Exercise 2**: Search bar with clear button
3. **Exercise 3**: Settings screen with toggle switches
4. **Exercise 4**: Product card for e-commerce app
5. **Exercise 5**: Chat message bubble

## Conclusion

Congratulations! You've learned how to:
- Generate Flutter widgets with Aibase
- Run generated code in Flutter apps
- Customize generation parameters
- Write effective descriptions

Keep practicing and exploring!

## Resources

- [Flutter Documentation](https://flutter.dev/docs)
- [Flutter Widget Catalog](https://flutter.dev/docs/development/ui/widgets)
- [Aibase Examples](../../examples/flutter/)
- [Best Practices](../best-practices.md)

---

**Questions? Check the [Troubleshooting Guide](troubleshooting.md) or open an issue on [GitHub](https://github.com/highskills123/Aibase/issues)**
