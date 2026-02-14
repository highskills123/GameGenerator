# Best Practices for Mobile Code Generation

This guide provides best practices for generating high-quality Flutter and React Native code using Aibase.

## Table of Contents

1. [Writing Effective Descriptions](#writing-effective-descriptions)
2. [Flutter Best Practices](#flutter-best-practices)
3. [React Native Best Practices](#react-native-best-practices)
4. [Code Quality](#code-quality)
5. [Performance Optimization](#performance-optimization)
6. [Security Considerations](#security-considerations)
7. [Testing Generated Code](#testing-generated-code)

## Writing Effective Descriptions

### Be Specific and Clear

#### ✅ Good Examples

```
"create a Flutter StatefulWidget counter with increment, decrement, and reset buttons styled with Material Design"

"create a React Native login form with email and password TextInput fields, validation, error messages, and a submit button using hooks"

"create a Flutter ListView.builder displaying 20 product cards with images, titles, prices, and add to cart buttons"
```

#### ❌ Poor Examples

```
"make a counter"
"create a form"
"build an app"
```

### Structure Your Descriptions

Use this pattern: **Widget/Component Type + Main Feature + Details + Styling/Behavior**

```
"create a [StatefulWidget/Functional Component] 
that [main functionality]
with [specific details]
styled with [design requirements]"
```

### Include Technical Details

- **Widget/Component types**: StatelessWidget, StatefulWidget, functional component
- **Layout**: Column, Row, Stack, flexDirection
- **State management**: useState, setState, Provider
- **Styling**: Colors, sizes, borders, shadows
- **Interactions**: onPress, onTap, onChanged

### Examples by Complexity

#### Simple
```
"create a Flutter Text widget displaying 'Hello World' centered and styled with blue color"
```

#### Medium
```
"create a React Native FlatList component that displays user profiles with avatar, name, email, and a follow button"
```

#### Complex
```
"create a Flutter registration form with TextFormFields for name, email, password, and confirm password, include validation for email format and password matching, display error messages, and submit button that shows loading indicator"
```

## Flutter Best Practices

### Widget Design

#### Use Const Constructors
**Request:** "use const constructors where possible"
```dart
const Text('Hello')  // Good
Text('Hello')        // Works but less efficient
```

#### Separate Widgets
For complex UIs, request separate widgets:
```
"create a Flutter screen with header, body, and footer as separate widgets"
```

#### StatelessWidget vs StatefulWidget
- **StatelessWidget**: No changing data, pure display
- **StatefulWidget**: Has changing data, user interaction

**Request appropriately:**
```
"create a StatelessWidget for displaying user profile"
"create a StatefulWidget for editable profile form"
```

### State Management

#### Local State
For simple state, use setState:
```
"create a StatefulWidget with local state using setState for toggle"
```

#### App-Wide State
For complex state, specify provider:
```
"create a Flutter widget using Provider for state management"
"create a Flutter widget with Riverpod for dependency injection"
```

### Layout

#### Responsive Design
```
"create a responsive Flutter layout that adapts to different screen sizes"
"use MediaQuery to make the widget responsive"
```

#### Proper Constraints
```
"use Expanded widgets to fill available space"
"wrap with SingleChildScrollView to handle overflow"
```

### Performance

#### Efficient Lists
```
"use ListView.builder for efficient rendering of large lists"
"use GridView.builder with itemExtent for performance"
```

#### Image Loading
```
"use cached_network_image for loading images efficiently"
"add placeholder while images load"
```

### Material Design

```
"follow Material Design guidelines"
"use Material widgets like Card, ListTile, AppBar"
"add elevation and shadows following Material Design"
```

## React Native Best Practices

### Component Design

#### Functional Components with Hooks
Always prefer functional components:
```
"create a functional React Native component with hooks"
"use useState and useEffect hooks"
```

#### Component Composition
Break down complex UIs:
```
"create separate components for header, list item, and footer"
```

### Hooks Usage

#### useState
For local state:
```
"create a component with useState for managing form inputs"
```

#### useEffect
For side effects:
```
"use useEffect to fetch data when component mounts"
```

#### useCallback and useMemo
For performance:
```
"use useCallback for event handlers"
"use useMemo for expensive computations"
```

### Styling

#### StyleSheet.create
Always use StyleSheet:
```
"use StyleSheet.create for all styles"
```

#### Platform-Specific Styles
```
"add platform-specific styles using Platform.select"
"use elevation for Android and shadow for iOS"
```

#### Responsive Design
```
"make layout responsive using Dimensions API"
"use percentage-based widths for responsiveness"
```

### Performance

#### FlatList for Lists
```
"use FlatList for scrollable lists"
"add keyExtractor and optimizations to FlatList"
```

#### Avoid Inline Functions
```
"define event handlers outside render for better performance"
```

#### Image Optimization
```
"add placeholder images"
"use appropriate resizeMode"
```

### Navigation

#### React Navigation
```
"use React Navigation for screen navigation"
"implement stack navigator with proper typing"
```

## Code Quality

### Naming Conventions

#### Flutter (Dart)
```
"use PascalCase for widget names"
"use camelCase for variables and methods"
"prefix private members with underscore"
```

#### React Native (JavaScript)
```
"use PascalCase for component names"
"use camelCase for variables and functions"
"use descriptive names"
```

### Code Organization

```
"organize imports at top"
"group related functions together"
"separate UI from business logic"
```

### Documentation

Request comments when needed:
```
"include JSDoc comments for functions"
"add comments explaining complex logic"
```

For production code:
```bash
python aibase.py -d "your description" -l flutter-widget
# (default includes comments)
```

For minimal code:
```bash
python aibase.py -d "your description" -l flutter-widget --no-comments
```

### Error Handling

```
"add try-catch blocks for async operations"
"display error messages to user"
"handle edge cases like empty data"
```

## Performance Optimization

### Request Efficient Code

#### Flutter
```
"use const constructors"
"implement ListView.builder for efficiency"
"add keys to list items"
"use cached_network_image for images"
```

#### React Native
```
"use FlatList instead of ScrollView for long lists"
"implement shouldComponentUpdate or React.memo"
"use useCallback for event handlers"
"lazy load images with placeholder"
```

### Memory Management

```
"dispose controllers in Flutter widgets"
"cleanup subscriptions in useEffect"
"cancel network requests on unmount"
```

### Bundle Size

```
"import only needed components"
"avoid large dependencies when possible"
"use tree-shaking compatible imports"
```

## Security Considerations

### Input Validation

```
"validate all user inputs"
"sanitize text inputs"
"check for SQL injection in search queries"
"validate email format and password strength"
```

### Data Security

```
"don't store sensitive data in plain text"
"use SecureStore for tokens"
"implement proper authentication"
```

### API Security

```
"don't include API keys in code"
"use environment variables for secrets"
"implement API key rotation"
```

### Request Example
```
"create a login form with secure password input, validate inputs, and store token securely"
```

## Testing Generated Code

### Manual Testing

1. **Copy Code**
   ```bash
   python aibase.py -d "your description" -l flutter-widget -o widget.dart
   ```

2. **Add to Project**
   ```bash
   cp widget.dart your_project/lib/
   ```

3. **Run App**
   ```bash
   flutter run  # or
   npx react-native run-ios
   ```

### Unit Testing

Request testable code:
```
"create a widget with testable business logic separated from UI"
"create pure functions for data manipulation"
```

### Integration Testing

```
"create component with test ids for integration testing"
"add testID prop to React Native components"
"add key properties to Flutter widgets for testing"
```

## Common Patterns

### Flutter Patterns

#### Form with Validation
```
"create a Form widget with GlobalKey and TextFormField validators"
```

#### Navigation
```
"create navigation using Navigator.push and MaterialPageRoute"
```

#### State Management
```
"create StatefulWidget with setState"
"use Provider for dependency injection"
```

### React Native Patterns

#### Form Handling
```
"create controlled form components with useState"
```

#### Navigation
```
"implement React Navigation with stack navigator"
```

#### Data Fetching
```
"fetch data with useEffect and display loading state"
```

## Iteration and Refinement

### Start Simple
```
1. "create a basic button component"
2. Review output
3. "create a button component with loading state and icon"
4. Review output
5. "create a button component with loading, icon, and haptic feedback"
```

### Iterative Improvements

If output isn't perfect:
1. Regenerate with more specific description
2. Adjust temperature (lower for consistency)
3. Try different wording
4. Add technical constraints

### Example Iteration

**First Try:**
```
"create a card widget"
```

**Second Try:**
```
"create a Material Design card widget with image, title, and description"
```

**Final:**
```
"create a Flutter Card widget with NetworkImage at top, title in bold, description text, and action buttons at bottom, with proper padding and elevation"
```

## Language-Specific Tips

### Flutter/Dart

- Mention "Material Design" or "Cupertino" style
- Specify widget types clearly
- Include layout structure (Column, Row, Stack)
- Mention state management approach
- Request proper disposal of controllers

### React Native

- Specify "functional component with hooks"
- Mention "SafeAreaView" for modern devices
- Include "StyleSheet.create" for styling
- Request "Platform.select" for platform differences
- Specify navigation library if needed

## Tools and Workflows

### IDE Integration

Generate and open directly:
```bash
python aibase.py -d "description" -l flutter-widget -o widget.dart && code widget.dart
```

### Git Workflow

```bash
# Generate code
python aibase.py -d "description" -l react-native-component -o Component.js

# Review
git diff Component.js

# Commit
git add Component.js
git commit -m "Add generated component"
```

### CI/CD Integration

```yaml
# .github/workflows/generate.yml
- name: Generate components
  run: |
    python aibase.py -d "${{ inputs.description }}" \
      -l flutter-widget -o generated.dart
```

## Summary Checklist

Before generating code, ensure your description includes:

- [ ] Specific widget/component type
- [ ] Main functionality clearly described
- [ ] UI structure and layout
- [ ] Styling requirements
- [ ] State management needs
- [ ] Interaction behavior
- [ ] Platform-specific requirements (if any)
- [ ] Performance considerations (for lists, images, etc.)

## Next Steps

- Review [Flutter Getting Started](flutter-getting-started.md)
- Review [React Native Getting Started](react-native-getting-started.md)
- Check [Configuration Guide](configuration-guide.md)
- Try [Tutorials](tutorials/)

---

**Questions? Open an issue on [GitHub](https://github.com/highskills123/Aibase/issues)**
