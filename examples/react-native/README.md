# React Native Examples

This directory contains comprehensive React Native component examples demonstrating various UI patterns and features that can be generated using Aibase.

## Examples Overview

### 1. Hello World (`01_hello_world.js`)
**Type:** Functional Component  
**Description:** A simple React Native app with centered text using modern functional components.

**Generate with:**
```bash
python aibase.py -d "create a simple React Native hello world app with centered text" -l react-native-component
```

**Features:**
- Functional component with hooks
- SafeAreaView for safe display areas
- StyleSheet for styling
- StatusBar configuration

---

### 2. Counter App (`02_counter_app.js`)
**Type:** Functional Component with useState Hook  
**Description:** Interactive counter app with increment, decrement, and reset functionality.

**Generate with:**
```bash
python aibase.py -d "create a React Native counter app with increment and decrement buttons using hooks" -l react-native-component
```

**Features:**
- useState hook for state management
- TouchableOpacity for buttons
- Styled components with elevation/shadow
- Event handling

---

### 3. FlatList (`03_flatlist.js`)
**Type:** Functional Component with FlatList  
**Description:** Scrollable list displaying items efficiently using FlatList.

**Generate with:**
```bash
python aibase.py -d "create a React Native app with a scrollable list using FlatList" -l react-native-component
```

**Features:**
- FlatList for optimized list rendering
- Custom item rendering
- TouchableOpacity for interactions
- Alert for user feedback
- Item separators

---

### 4. Form with Validation (`04_form_validation.js`)
**Type:** Functional Component with Form Validation  
**Description:** Registration form with comprehensive input validation.

**Generate with:**
```bash
python aibase.py -d "create a React Native form with input validation for name, email, and password" -l react-native-component
```

**Features:**
- Multiple TextInput components
- Real-time validation
- Error message display
- Password visibility toggle
- KeyboardAvoidingView for keyboard handling
- ScrollView for small screens
- Regex validation for email

---

### 5. Navigation (`05_navigation.js`)
**Type:** Multi-screen app with React Navigation  
**Description:** App demonstrating navigation between screens using React Navigation.

**Generate with:**
```bash
python aibase.py -d "create a React Native app with navigation between screens using React Navigation" -l react-native-component
```

**Features:**
- React Navigation setup
- Stack Navigator
- Screen transitions
- Passing parameters between screens
- Navigation actions (push, goBack, navigate)
- Custom header styling

**Note:** Requires React Navigation installation:
```bash
npm install @react-navigation/native @react-navigation/native-stack
npm install react-native-screens react-native-safe-area-context
```

---

## How to Use These Examples

### 1. Using Aibase to Generate Similar Code

```bash
# Generate a component
python aibase.py -d "your description here" -l react-native-component -o Component.js

# Generate general React Native code
python aibase.py -d "your description here" -l react-native -o App.js

# Save to file
python aibase.py -d "create a profile screen" -l react-native-component -o ProfileScreen.js
```

### 2. Running These Examples

1. Create a new React Native project:
```bash
npx react-native init MyApp
cd MyApp
```

2. Replace `App.js` with the example code:
```bash
cp examples/react-native/01_hello_world.js App.js
```

3. Run the app:
```bash
# For iOS
npx react-native run-ios

# For Android
npx react-native run-android
```

### 3. Using the API

```python
import requests

url = "http://localhost:5000/api/translate"
data = {
    "description": "create a React Native profile screen with avatar and user info",
    "language": "react-native-component"
}

response = requests.post(url, json=data)
result = response.json()

if result["success"]:
    with open("ProfileScreen.js", "w") as f:
        f.write(result["code"])
```

### 4. Using cURL

```bash
curl -X POST http://localhost:5000/api/translate \
  -H "Content-Type: application/json" \
  -d '{
    "description": "create a React Native login screen",
    "language": "react-native-component"
  }' | jq -r '.code' > LoginScreen.js
```

### 5. Using JavaScript/Node.js

```javascript
const axios = require('axios');
const fs = require('fs');

const generateComponent = async () => {
  const response = await axios.post('http://localhost:5000/api/translate', {
    description: 'create a React Native settings screen with toggle switches',
    language: 'react-native-component'
  });

  if (response.data.success) {
    fs.writeFileSync('SettingsScreen.js', response.data.code);
    console.log('Component generated successfully!');
  }
};

generateComponent();
```

## Component Patterns

### Functional Components (Recommended)
Modern React Native uses functional components with hooks:
- Cleaner syntax
- Better performance
- Easier to test
- Hooks for state and lifecycle

### Hooks Used in Examples

- **useState**: For managing component state
- **useEffect**: For side effects (not shown but commonly used)
- **useNavigation**: For navigation (in navigation example)

## Styling Patterns

All examples use StyleSheet.create() for styling:

```javascript
const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  // ... more styles
});
```

### Common Style Properties

- **flex**: Flexbox layout
- **flexDirection**: 'row' | 'column'
- **justifyContent**: Alignment along main axis
- **alignItems**: Alignment along cross axis
- **padding/margin**: Spacing
- **backgroundColor**: Background color
- **borderRadius**: Rounded corners
- **elevation** (Android): Shadow effect
- **shadow*** (iOS): Shadow properties

## Best Practices Demonstrated

1. **SafeAreaView**: Respects device safe areas (notches, etc.)
2. **StatusBar**: Proper status bar configuration
3. **KeyboardAvoidingView**: Handle keyboard properly
4. **TouchableOpacity**: Better than TouchableHighlight for most cases
5. **FlatList**: Use instead of ScrollView for long lists
6. **State Management**: useState for component-level state
7. **Validation**: Client-side validation before submission
8. **Error Handling**: Display errors to users
9. **Accessibility**: Use proper labels and hints

## Common Components

| Component | Use Case |
|-----------|----------|
| View | Container (like div in web) |
| Text | Display text |
| TextInput | User input |
| TouchableOpacity | Buttons and touchable areas |
| FlatList | Efficient scrollable lists |
| ScrollView | Scrollable content |
| Image | Display images |
| SafeAreaView | Safe area boundaries |
| Modal | Overlay dialogs |

## Dependencies

### Basic Setup
These examples work with a fresh React Native installation.

### For Navigation Example
```bash
npm install @react-navigation/native @react-navigation/native-stack
npm install react-native-screens react-native-safe-area-context
```

### Common Production Dependencies

```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-native": "^0.72.0",
    "@react-navigation/native": "^6.1.0",
    "@react-navigation/native-stack": "^6.9.0",
    "axios": "^1.4.0",
    "@react-native-async-storage/async-storage": "^1.19.0",
    "react-native-vector-icons": "^10.0.0"
  }
}
```

## Platform Differences

### iOS vs Android
Examples handle platform differences where necessary:

```javascript
import { Platform } from 'react-native';

const styles = StyleSheet.create({
  shadow: Platform.select({
    ios: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 2 },
      shadowOpacity: 0.25,
      shadowRadius: 3.84,
    },
    android: {
      elevation: 5,
    },
  }),
});
```

## Debugging Tips

1. **Enable Remote Debugging**:
   - Shake device → "Debug"
   - Or Cmd+D (iOS) / Cmd+M (Android)

2. **Console Logs**:
```javascript
console.log('Debug:', value);
console.warn('Warning:', message);
console.error('Error:', error);
```

3. **React DevTools**:
```bash
npm install -g react-devtools
react-devtools
```

## Next Steps

1. Modify these examples to fit your needs
2. Combine patterns from multiple examples  
3. Use Aibase to generate custom components
4. Add state management (Redux, MobX, Context)
5. Integrate with APIs
6. Add testing (Jest, React Native Testing Library)
7. Check out the documentation in `docs/` directory

## Resources

- [React Native Documentation](https://reactnative.dev/docs/getting-started)
- [React Navigation](https://reactnavigation.org/)
- [React Hooks](https://reactjs.org/docs/hooks-intro.html)
- [StyleSheet API](https://reactnative.dev/docs/stylesheet)
- [Aibase Documentation](../../docs/)

## Testing Components

```bash
# Run tests
npm test

# With coverage
npm test -- --coverage
```

## Contributing

Want to add more examples? See [Contributing Guidelines](../../docs/contributing-mobile.md)
