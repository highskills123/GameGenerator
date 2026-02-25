// React Native Counter App Example - Using useState Hook
// Generated using: python aibase.py -d "create a React Native counter app with increment and decrement buttons using hooks" -l react-native-component

import React, { useState } from 'react';
import {
  SafeAreaView,
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  StatusBar,
} from 'react-native';

const CounterApp = () => {
  const [count, setCount] = useState(0);

  const increment = () => setCount(count + 1);
  const decrement = () => setCount(count - 1);
  const reset = () => setCount(0);

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#9C27B0" />
      <View style={styles.header}>
        <Text style={styles.headerText}>Counter App</Text>
      </View>
      <View style={styles.content}>
        <Text style={styles.label}>Counter Value:</Text>
        <Text style={styles.counter}>{count}</Text>
        
        <View style={styles.buttonContainer}>
          <TouchableOpacity
            style={[styles.button, styles.decrementButton]}
            onPress={decrement}
            activeOpacity={0.7}>
            <Text style={styles.buttonText}>-</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.button, styles.resetButton]}
            onPress={reset}
            activeOpacity={0.7}>
            <Text style={styles.buttonText}>Reset</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.button, styles.incrementButton]}
            onPress={increment}
            activeOpacity={0.7}>
            <Text style={styles.buttonText}>+</Text>
          </TouchableOpacity>
        </View>
      </View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    backgroundColor: '#9C27B0',
    padding: 20,
    alignItems: 'center',
  },
  headerText: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  label: {
    fontSize: 20,
    color: '#333',
    marginBottom: 10,
  },
  counter: {
    fontSize: 72,
    fontWeight: 'bold',
    color: '#9C27B0',
    marginBottom: 40,
  },
  buttonContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
  },
  button: {
    paddingVertical: 15,
    paddingHorizontal: 25,
    borderRadius: 10,
    marginHorizontal: 10,
    minWidth: 80,
    alignItems: 'center',
    elevation: 3,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
  },
  decrementButton: {
    backgroundColor: '#f44336',
  },
  resetButton: {
    backgroundColor: '#757575',
  },
  incrementButton: {
    backgroundColor: '#4CAF50',
  },
  buttonText: {
    color: '#fff',
    fontSize: 20,
    fontWeight: 'bold',
  },
});

export default CounterApp;
