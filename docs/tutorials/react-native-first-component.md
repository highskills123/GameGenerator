# Tutorial: Generate Your First React Native Component

This step-by-step tutorial will guide you through generating your first React Native component using Aibase.

## What You'll Learn

- How to generate React Native components with Aibase
- How to run generated components
- How to customize generation
- Best practices for describing components

## Prerequisites

- Aibase installed ([Installation Guide](../README.md))
- OpenAI API key configured
- (Optional) React Native environment for running components

## Step 1: Verify Setup

```bash
# Check if aibase.py runs
python aibase.py --help
```

## Step 2: Generate a Simple Component

Let's create a "Hello World" component.

```bash
python aibase.py \
  -d "create a React Native functional component that displays 'Hello, React Native!' in the center" \
  -l react-native-component \
  -o HelloComponent.js
```

### View the Generated Code

```bash
cat HelloComponent.js
```

You'll see:

```javascript
import React from 'react';
import { SafeAreaView, View, Text, StyleSheet } from 'react-native';

const HelloComponent = () => {
  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
        <Text style={styles.text}>Hello, React Native!</Text>
      </View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  text: {
    fontSize: 24,
    fontWeight: 'bold',
  },
});

export default HelloComponent;
```

## Step 3: Run the Component

### Create React Native Project

```bash
npx react-native init MyFirstApp
cd MyFirstApp
```

### Add Generated Component

```bash
# Copy component
cp ../HelloComponent.js src/components/HelloComponent.js
```

Or create `src/components/` and copy there.

### Update App.js

```javascript
import React from 'react';
import HelloComponent from './src/components/HelloComponent';

const App = () => {
  return <HelloComponent />;
};

export default App;
```

### Run the App

```bash
# For iOS
npx react-native run-ios

# For Android
npx react-native run-android
```

🎉 You should see your component running!

## Step 4: Generate with State (Hooks)

Now let's generate an interactive component:

```bash
python aibase.py \
  -d "create a React Native counter component with useState hook, increment and decrement buttons" \
  -l react-native-component \
  -o CounterComponent.js
```

### View the Result

```bash
cat CounterComponent.js
```

You'll see a complete counter with hooks!

## Step 5: Generate a Styled Component

Add more styling details:

```bash
python aibase.py \
  -d "create a React Native button component with:
  - TouchableOpacity for touch handling
  - Custom background color prop
  - Text label prop
  - Icon support
  - Loading state with ActivityIndicator
  - Disabled state
  - StyleSheet for styling" \
  -l react-native-component \
  -o CustomButton.js
```

## Step 6: Generate a Form

```bash
python aibase.py \
  -d "create a React Native login form with:
  - TextInput for email with validation
  - TextInput for password with secure entry
  - Show/hide password button
  - Submit button
  - Error message display
  - useState for managing form state
  - Input validation" \
  -l react-native-component \
  -o LoginForm.js
```

## Step 7: Generate a List Component

```bash
python aibase.py \
  -d "create a React Native FlatList component displaying user profiles with:
  - Avatar image
  - Name and username
  - Follow button
  - Optimized rendering
  - Pull to refresh
  - keyExtractor" \
  -l react-native-component \
  -o UserList.js
```

## Step 8: Using the API

### Start API Server

```bash
python api_server.py
```

### Generate via API (JavaScript/Node.js)

```javascript
const axios = require('axios');
const fs = require('fs');

async function generateComponent() {
  const response = await axios.post('http://localhost:5000/api/translate', {
    description: 'create a React Native card component with image, title, and description',
    language: 'react-native-component'
  });

  if (response.data.success) {
    fs.writeFileSync('CardComponent.js', response.data.code);
    console.log('Component generated!');
  }
}

generateComponent();
```

### Generate via API (cURL)

```bash
curl -X POST http://localhost:5000/api/translate \
  -H "Content-Type: application/json" \
  -d '{
    "description": "create a React Native search bar component",
    "language": "react-native-component"
  }' | jq -r '.code' > SearchBar.js
```

## Step 9: Interactive Mode

```bash
python aibase.py
```

Then:
```
Enter your description: create a React Native profile screen
Target language: react-native-component
```

## Common Patterns

### Basic Display Component

```bash
python aibase.py \
  -d "create a React Native Text component displaying a welcome message" \
  -l react-native-component
```

### Layout Component

```bash
python aibase.py \
  -d "create a React Native View with flexbox layout containing three colored boxes" \
  -l react-native-component
```

### Interactive Component

```bash
python aibase.py \
  -d "create a React Native toggle switch that changes state with useState" \
  -l react-native-component
```

### API Integration

```bash
python aibase.py \
  -d "create a React Native component that fetches data from API using useEffect and displays loading state" \
  -l react-native-component
```

## Tips for Better Results

### 1. Specify Component Type

✅ Good:
```
"create a React Native functional component with useState"
```

❌ Too vague:
```
"create a component"
```

### 2. Mention Hooks

✅ Good:
```
"create a component using useState and useEffect hooks"
```

### 3. Include Styling Details

✅ Good:
```
"use StyleSheet.create with flexbox layout, blue background, and rounded corners"
```

### 4. Specify UI Components

✅ Good:
```
"use TouchableOpacity for button, TextInput for input fields, and FlatList for scrollable list"
```

### 5. Platform-Specific Features

```
"add shadow for iOS and elevation for Android using Platform.select"
```

## Customization Options

### Adjust Temperature

```bash
# More consistent
python aibase.py \
  -d "create a button component" \
  -l react-native-component \
  --temperature 0.3

# More creative
python aibase.py \
  -d "create a button component" \
  -l react-native-component \
  --temperature 0.8
```

### Increase Max Tokens

For complex components:

```bash
python aibase.py \
  -d "create a complex navigation component" \
  -l react-native-component \
  --max-tokens 3000
```

### Generate Without Comments

```bash
python aibase.py \
  -d "create a simple component" \
  -l react-native-component \
  --no-comments
```

## Troubleshooting

### Issue: Import Errors

**Solution:** Ensure dependencies are installed:
```bash
npm install react-native
```

### Issue: Component Won't Render

**Solution:** Check:
1. Export statement: `export default ComponentName`
2. Import in App.js is correct
3. Component name matches

### Issue: Styling Issues

**Solution:** Request StyleSheet explicitly:
```bash
python aibase.py \
  -d "create component with StyleSheet.create for styling" \
  -l react-native-component
```

### Issue: Hooks Not Working

**Solution:** Specify hooks in description:
```bash
python aibase.py \
  -d "create functional component using useState and useEffect hooks" \
  -l react-native-component
```

## Practice Exercises

Try generating these:

1. **Exercise 1**: Avatar component with image and fallback
2. **Exercise 2**: Rating component with stars
3. **Exercise 3**: Navigation header with back button
4. **Exercise 4**: Image gallery with horizontal scroll
5. **Exercise 5**: Chat input with send button

**Solutions:**

### Exercise 1: Avatar Component

```bash
python aibase.py \
  -d "create a React Native avatar component with circular image, fallback initials if no image, and size prop" \
  -l react-native-component \
  -o Avatar.js
```

### Exercise 2: Rating Component

```bash
python aibase.py \
  -d "create a React Native rating component with 5 stars, tap to rate, and display current rating" \
  -l react-native-component \
  -o Rating.js
```

## Next Steps

1. **Explore Examples**: Check `examples/react-native/` for more
2. **Try Advanced Features**: Navigation, animations, API calls
3. **Combine Components**: Build screens with multiple components
4. **Add Navigation**: Use React Navigation
5. **Read More**: Check [React Native Getting Started](../react-native-getting-started.md)

## Advanced Topics

### Generate with TypeScript

```bash
python aibase.py \
  -d "create a TypeScript React Native component with type definitions for props" \
  -l typescript \
  -o TypedComponent.tsx
```

### Generate with React Navigation

```bash
python aibase.py \
  -d "create a React Native screen component with React Navigation, stack navigator, and navigation props" \
  -l react-native-component \
  -o HomeScreen.js
```

### Generate with Styling Libraries

```bash
python aibase.py \
  -d "create a React Native component using styled-components for styling" \
  -l react-native-component \
  -o StyledComponent.js
```

## Best Practices

1. **Use Functional Components**: Always specify functional components
2. **Include Hooks**: Mention useState, useEffect, etc.
3. **Add SafeAreaView**: For modern devices
4. **Use StyleSheet**: Always use StyleSheet.create
5. **Platform-Specific**: Add Platform.select when needed
6. **Export Default**: Ensure export default is included
7. **PropTypes**: Request PropTypes for prop validation

## Conclusion

Congratulations! You've learned:
- How to generate React Native components
- How to run components in apps
- How to customize generation
- Best practices for descriptions

Keep practicing!

## Resources

- [React Native Documentation](https://reactnative.dev/)
- [React Hooks](https://reactjs.org/docs/hooks-intro.html)
- [React Navigation](https://reactnavigation.org/)
- [Aibase Examples](../../examples/react-native/)
- [Best Practices](../best-practices.md)

---

**Questions? Check the [Troubleshooting Guide](troubleshooting.md) or open an issue on [GitHub](https://github.com/highskills123/Aibase/issues)**
