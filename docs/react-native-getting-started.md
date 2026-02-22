# React Native Getting Started Guide

Welcome to generating React Native code with Aibase! This guide will help you start creating React Native components and applications using natural language descriptions.

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

Aibase can generate React Native components, screens, and complete applications from natural language descriptions. Whether you're building a simple button or a complex navigation system, Aibase helps you generate clean, modern React Native code with hooks.

## Prerequisites

Before you start, make sure you have:

1. **Aibase installed** - Follow the main [README](../README.md) for installation
2. **Ollama running** - Install from https://ollama.com and pull the model: `ollama pull qwen2.5-coder:7b`
3. **React Native environment** (optional, for running generated code) - [Set up React Native](https://reactnative.dev/docs/environment-setup)

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
# Edit .env to customize Ollama settings (optional)
```

## Basic Usage

### Command Line Interface

#### 1. Generate a Simple Component

```bash
python aibase.py -d "create a simple React Native button component" -l react-native-component
```

#### 2. Generate and Save to File

```bash
python aibase.py -d "create a React Native profile screen" -l react-native-component -o ProfileScreen.js
```

#### 3. Generate Without Comments

```bash
python aibase.py -d "create a login screen" -l react-native-component --no-comments -o LoginScreen.js
```

### Interactive Mode

Start interactive mode:

```bash
python aibase.py
```

Then:
1. Enter your description: "create a React Native counter component with hooks"
2. Choose language: "react-native-component"
3. View generated code

### Programmatic Usage

Use Aibase in your Python scripts:

```python
from aibase import AibaseTranslator

# Initialize
translator = AibaseTranslator()

# Generate React Native component
code = translator.translate(
    description="create a React Native card component with image and title",
    target_language="react-native-component",
    include_comments=True
)

print(code)

# Save to file
with open("CardComponent.js", "w") as f:
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
    "description": "create a React Native header component",
    "language": "react-native-component"
  }'
```

Or using JavaScript:

```javascript
const response = await fetch('http://localhost:5000/api/translate', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    description: 'create a React Native settings screen',
    language: 'react-native-component'
  })
});

const result = await response.json();
if (result.success) {
  console.log(result.code);
}
```

## Language Options

Aibase supports multiple React Native language options:

### 1. `react-native-component`
**Best for:** Individual components and screens

```bash
python aibase.py -d "create a functional component with useState" -l react-native-component
```

**Generates:** Complete component with imports, hooks, and StyleSheet

### 2. `react-native`
**Best for:** Full applications or complex features

```bash
python aibase.py -d "create a complete React Native todo app" -l react-native
```

**Generates:** Full app structure with navigation and multiple screens

### 3. `javascript` or `typescript`
**Best for:** Utilities, helpers, or non-UI code

```bash
python aibase.py -d "create a utility function for API calls" -l javascript
```

## Common Use Cases

### 1. Basic Components

#### Functional Component
```bash
python aibase.py -d "create a functional React Native component that displays a greeting message" -l react-native-component
```

#### Component with State
```bash
python aibase.py -d "create a React Native component with useState hook for managing a counter" -l react-native-component
```

### 2. UI Components

#### Custom Button
```bash
python aibase.py -d "create a custom button component with TouchableOpacity and gradient background" -l react-native-component
```

#### Card Component
```bash
python aibase.py -d "create a card component with image, title, description, and action buttons" -l react-native-component
```

### 3. Screens

#### Login Screen
```bash
python aibase.py -d "create a React Native login screen with email, password inputs, and submit button" -l react-native-component -o LoginScreen.js
```

#### Profile Screen
```bash
python aibase.py -d "create a profile screen with avatar, user info, and edit button" -l react-native-component -o ProfileScreen.js
```

### 4. Forms

#### Input Form
```bash
python aibase.py -d "create a form with text inputs for name, email, phone with validation" -l react-native-component
```

#### Search Bar
```bash
python aibase.py -d "create a search bar component with filtering functionality" -l react-native-component
```

### 5. Lists

#### FlatList
```bash
python aibase.py -d "create a component using FlatList to display a scrollable list of items" -l react-native-component
```

#### Sectioned List
```bash
python aibase.py -d "create a SectionList component with headers and grouped data" -l react-native-component
```

### 6. Navigation

#### Stack Navigation
```bash
python aibase.py -d "create a React Native app with stack navigation between home and detail screens" -l react-native
```

#### Tab Navigation
```bash
python aibase.py -d "create a bottom tab navigator with three tabs" -l react-native
```

### 7. Advanced Features

#### API Integration
```bash
python aibase.py -d "create a component that fetches data from an API using useEffect and displays it" -l react-native-component
```

#### State Management
```bash
python aibase.py -d "create a component using useContext and useReducer for state management" -l react-native-component
```

#### Custom Hooks
```bash
python aibase.py -d "create a custom hook for form validation in React Native" -l react-native-component
```

## Tips and Best Practices

### Writing Good Descriptions

#### ✅ Good Descriptions (Specific and Clear)

```
"create a React Native functional component with useState for a toggle switch"

"create a login screen with TextInput for email and password, validation, and TouchableOpacity submit button"

"create a FlatList component that displays product cards with images, titles, prices, and add to cart buttons"
```

#### ❌ Poor Descriptions (Too Vague)

```
"make an app"
"create a component"
"something with buttons"
```

### Best Practices

1. **Specify Modern React Patterns**
   - Mention "functional component" (not class component)
   - Use "useState", "useEffect", or other hooks
   - Specify "with hooks" for state management

2. **Describe the UI Structure**
   - Mention components: "View", "Text", "TouchableOpacity"
   - Describe layout: "flexDirection row", "centered"
   - Include styling details: "with shadow", "rounded corners", "blue background"

3. **Include Functionality**
   - Describe interactions: "onPress", "onChangeText"
   - Mention state updates: "updates counter", "toggles visibility"
   - Specify validation: "validate email", "check required fields"

4. **Specify Dependencies If Needed**
   - "using React Navigation"
   - "with axios for API calls"
   - "using AsyncStorage"

5. **Platform Considerations**
   - Mention if iOS/Android specific: "with iOS shadow styles"
   - Use "Platform.select" when needed
   - Consider "SafeAreaView" for modern devices

### Example: Evolving a Description

**Basic:**
```
"create a button"
```

**Better:**
```
"create a React Native button"
```

**Even Better:**
```
"create a TouchableOpacity button with text label"
```

**Best:**
```
"create a custom React Native button component using TouchableOpacity with gradient background, icon, loading state, and haptic feedback"
```

## Styling Tips

### Using StyleSheet

Generated components use StyleSheet.create():

```javascript
const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 20,
  },
});
```

### Common Style Patterns

Request specific styling in your descriptions:

- **Layout**: "use flexbox", "centered vertically", "row layout"
- **Spacing**: "with 20px padding", "margin between items"
- **Colors**: "blue background", "white text", "gradient from X to Y"
- **Borders**: "rounded corners", "border radius 10", "with border"
- **Shadows**: 
  - iOS: "with shadow"
  - Android: "with elevation"
  - Both: "with shadow for both platforms"

### Responsive Design

```bash
python aibase.py -d "create a component that adjusts layout based on screen dimensions using Dimensions API" -l react-native-component
```

## Troubleshooting

### Issue: Import errors or missing modules

**Solution:** Install required dependencies:

```bash
npm install react-native
npm install @react-navigation/native  # if using navigation
npm install axios  # if using API calls
```

### Issue: Component doesn't render correctly

**Solution:**
1. Check component is exported correctly: `export default ComponentName`
2. Verify all JSX is properly closed
3. Ensure styles are defined in StyleSheet
4. Check for typos in property names

### Issue: Platform-specific styling issues

**Solution:** Request platform-specific code:

```bash
python aibase.py -d "create a component with shadow that works on both iOS and Android using Platform.select" -l react-native-component
```

### Issue: State not updating

**Solution:**
1. Verify useState is imported: `import { useState } from 'react'`
2. Check state setter is called correctly: `setState(newValue)`
3. Ensure component is re-rendering

### Issue: Navigation not working

**Solution:**
1. Install React Navigation packages
2. Wrap app in NavigationContainer
3. Request specific navigation setup in description

### Issue: Generated code too complex or simple

**Solution:** Adjust your description:
- **For simpler:** "create a basic component with minimal styling"
- **For complex:** "create a comprehensive component with validation, error handling, and loading states"

### Issue: Want TypeScript instead of JavaScript

**Solution:** Specify in description:

```bash
python aibase.py -d "create a TypeScript React Native component with type definitions" -l typescript
```

## Testing Generated Components

### Running in Your App

1. Copy generated code to your project:
```bash
cp ComponentName.js YourProject/src/components/
```

2. Import and use:
```javascript
import ComponentName from './components/ComponentName';

function App() {
  return <ComponentName />;
}
```

### Quick Testing

Use Expo for quick testing:

```bash
npx create-expo-app TestApp
cd TestApp
# Add your generated component
npx expo start
```

## Next Steps

1. **Explore Examples** - Check out `examples/react-native/` directory
2. **Read Best Practices** - See [docs/best-practices.md](best-practices.md)
3. **Try Advanced Features** - Learn about [API usage](api-mobile-frameworks.md)
4. **Follow Tutorials** - Complete tutorials in [docs/tutorials/](tutorials/)
5. **Integrate with Your App** - Use generated components in your projects

## Additional Resources

- [React Native Documentation](https://reactnative.dev/docs/getting-started)
- [React Hooks](https://reactjs.org/docs/hooks-intro.html)
- [React Navigation](https://reactnavigation.org/)
- [StyleSheet API](https://reactnative.dev/docs/stylesheet)
- [Aibase API Documentation](api-mobile-frameworks.md)
- [Troubleshooting Guide](tutorials/troubleshooting.md)

## Common Hooks Reference

### useState
```javascript
const [state, setState] = useState(initialValue);
```

### useEffect
```javascript
useEffect(() => {
  // Side effect code
  return () => {
    // Cleanup
  };
}, [dependencies]);
```

### useContext
```javascript
const value = useContext(MyContext);
```

### useCallback
```javascript
const memoizedCallback = useCallback(() => {
  // Function code
}, [dependencies]);
```

### useMemo
```javascript
const memoizedValue = useMemo(() => computeValue(a, b), [a, b]);
```

## Need Help?

- Check [Troubleshooting Guide](tutorials/troubleshooting.md)
- Review [React Native Examples](../examples/react-native/)
- Read [React Native Docs](https://reactnative.dev/)
- Open an issue on [GitHub](https://github.com/highskills123/Aibase/issues)

---

**Happy React Native coding with Aibase! 🚀**
