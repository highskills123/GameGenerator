// React Native Navigation Example - Using React Navigation
// Generated using: python aibase.py -d "create a React Native app with navigation between screens using React Navigation" -l react-native-component

import React from 'react';
import {
  SafeAreaView,
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  StatusBar,
  FlatList,
} from 'react-native';

// Note: This example assumes React Navigation is installed
// Install with: npm install @react-navigation/native @react-navigation/native-stack
// For full setup, see: https://reactnavigation.org/docs/getting-started

import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';

const Stack = createNativeStackNavigator();

// Menu items data
const MENU_ITEMS = [
  { id: '1', title: 'Profile', icon: '👤' },
  { id: '2', title: 'Settings', icon: '⚙️' },
  { id: '3', title: 'About', icon: 'ℹ️' },
  { id: '4', title: 'Help', icon: '❓' },
  { id: '5', title: 'Feedback', icon: '💬' },
];

// Home Screen Component
const HomeScreen = ({ navigation }) => {
  const renderItem = ({ item }) => (
    <TouchableOpacity
      style={styles.menuItem}
      onPress={() => navigation.navigate('Details', { itemTitle: item.title })}
      activeOpacity={0.7}>
      <View style={styles.menuIcon}>
        <Text style={styles.iconText}>{item.icon}</Text>
      </View>
      <Text style={styles.menuTitle}>{item.title}</Text>
      <Text style={styles.arrow}>›</Text>
    </TouchableOpacity>
  );

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
        <Text style={styles.welcomeTitle}>Welcome!</Text>
        <Text style={styles.welcomeSubtitle}>
          Select an option below to navigate
        </Text>
        <FlatList
          data={MENU_ITEMS}
          renderItem={renderItem}
          keyExtractor={(item) => item.id}
          contentContainerStyle={styles.listContainer}
        />
      </View>
    </SafeAreaView>
  );
};

// Detail Screen Component
const DetailScreen = ({ route, navigation }) => {
  const { itemTitle } = route.params;

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.detailContent}>
        <Text style={styles.detailTitle}>{itemTitle}</Text>
        <Text style={styles.detailDescription}>
          This is the {itemTitle} screen. Here you would display detailed
          information or perform actions related to {itemTitle}.
        </Text>

        <View style={styles.buttonContainer}>
          <TouchableOpacity
            style={styles.backButton}
            onPress={() => navigation.goBack()}
            activeOpacity={0.8}>
            <Text style={styles.backButtonText}>← Go Back</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.homeButton}
            onPress={() => navigation.navigate('Home')}
            activeOpacity={0.8}>
            <Text style={styles.homeButtonText}>🏠 Home</Text>
          </TouchableOpacity>
        </View>
      </View>
    </SafeAreaView>
  );
};

// Main App Component
const NavigationApp = () => {
  return (
    <NavigationContainer>
      <Stack.Navigator
        initialRouteName="Home"
        screenOptions={{
          headerStyle: {
            backgroundColor: '#FF9800',
          },
          headerTintColor: '#fff',
          headerTitleStyle: {
            fontWeight: 'bold',
          },
        }}>
        <Stack.Screen
          name="Home"
          component={HomeScreen}
          options={{ title: 'Home Screen' }}
        />
        <Stack.Screen
          name="Details"
          component={DetailScreen}
          options={({ route }) => ({ title: route.params.itemTitle })}
        />
      </Stack.Navigator>
    </NavigationContainer>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  content: {
    flex: 1,
    padding: 20,
  },
  welcomeTitle: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#333',
    textAlign: 'center',
    marginTop: 20,
  },
  welcomeSubtitle: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    marginTop: 10,
    marginBottom: 30,
  },
  listContainer: {
    paddingBottom: 20,
  },
  menuItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    borderRadius: 10,
    padding: 16,
    marginVertical: 8,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.2,
    shadowRadius: 1.41,
  },
  menuIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#FFF3E0',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 15,
  },
  iconText: {
    fontSize: 20,
  },
  menuTitle: {
    flex: 1,
    fontSize: 18,
    color: '#333',
    fontWeight: '500',
  },
  arrow: {
    fontSize: 24,
    color: '#999',
  },
  detailContent: {
    flex: 1,
    padding: 20,
  },
  detailTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 20,
  },
  detailDescription: {
    fontSize: 16,
    color: '#666',
    lineHeight: 24,
    marginBottom: 40,
  },
  buttonContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  backButton: {
    flex: 1,
    backgroundColor: '#FF9800',
    borderRadius: 8,
    padding: 15,
    marginRight: 10,
    alignItems: 'center',
  },
  backButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  homeButton: {
    flex: 1,
    backgroundColor: '#4CAF50',
    borderRadius: 8,
    padding: 15,
    marginLeft: 10,
    alignItems: 'center',
  },
  homeButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
});

export default NavigationApp;
