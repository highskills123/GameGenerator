// React Native FlatList Example - Display list of items
// Generated using: python aibase.py -d "create a React Native app with a scrollable list using FlatList" -l react-native-component

import React from 'react';
import {
  SafeAreaView,
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  StatusBar,
  Alert,
} from 'react-native';

const DATA = [
  { id: '1', title: 'Item 1', description: 'Description for item 1' },
  { id: '2', title: 'Item 2', description: 'Description for item 2' },
  { id: '3', title: 'Item 3', description: 'Description for item 3' },
  { id: '4', title: 'Item 4', description: 'Description for item 4' },
  { id: '5', title: 'Item 5', description: 'Description for item 5' },
  { id: '6', title: 'Item 6', description: 'Description for item 6' },
  { id: '7', title: 'Item 7', description: 'Description for item 7' },
  { id: '8', title: 'Item 8', description: 'Description for item 8' },
  { id: '9', title: 'Item 9', description: 'Description for item 9' },
  { id: '10', title: 'Item 10', description: 'Description for item 10' },
];

const ListApp = () => {
  const handleItemPress = (item) => {
    Alert.alert('Item Selected', `You tapped on ${item.title}`);
  };

  const renderItem = ({ item, index }) => (
    <TouchableOpacity
      style={styles.itemContainer}
      onPress={() => handleItemPress(item)}
      activeOpacity={0.7}>
      <View style={styles.itemNumber}>
        <Text style={styles.itemNumberText}>{index + 1}</Text>
      </View>
      <View style={styles.itemContent}>
        <Text style={styles.itemTitle}>{item.title}</Text>
        <Text style={styles.itemDescription}>{item.description}</Text>
      </View>
      <View style={styles.itemArrow}>
        <Text style={styles.arrowText}>›</Text>
      </View>
    </TouchableOpacity>
  );

  const renderSeparator = () => <View style={styles.separator} />;

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#009688" />
      <View style={styles.header}>
        <Text style={styles.headerText}>List View Example</Text>
      </View>
      <FlatList
        data={DATA}
        renderItem={renderItem}
        keyExtractor={(item) => item.id}
        ItemSeparatorComponent={renderSeparator}
        contentContainerStyle={styles.listContent}
      />
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    backgroundColor: '#009688',
    padding: 20,
    alignItems: 'center',
  },
  headerText: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
  },
  listContent: {
    padding: 10,
  },
  itemContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    borderRadius: 10,
    padding: 15,
    marginVertical: 5,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.2,
    shadowRadius: 1.41,
  },
  itemNumber: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#009688',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 15,
  },
  itemNumberText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  itemContent: {
    flex: 1,
  },
  itemTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 4,
  },
  itemDescription: {
    fontSize: 14,
    color: '#666',
  },
  itemArrow: {
    marginLeft: 10,
  },
  arrowText: {
    fontSize: 24,
    color: '#999',
  },
  separator: {
    height: 0,
  },
});

export default ListApp;
