// Flutter ListView Example - Display list of items
// Generated using: python aibase.py -d "create a Flutter app with a scrollable list of items with titles and subtitles" -l flutter-widget

import 'package:flutter/material.dart';

void main() {
  runApp(ListViewApp());
}

class ListViewApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'ListView Example',
      theme: ThemeData(
        primarySwatch: Colors.teal,
      ),
      home: ListViewScreen(),
    );
  }
}

class ListViewScreen extends StatelessWidget {
  // Sample data
  final List<Map<String, String>> items = [
    {'title': 'Item 1', 'subtitle': 'Description for item 1'},
    {'title': 'Item 2', 'subtitle': 'Description for item 2'},
    {'title': 'Item 3', 'subtitle': 'Description for item 3'},
    {'title': 'Item 4', 'subtitle': 'Description for item 4'},
    {'title': 'Item 5', 'subtitle': 'Description for item 5'},
    {'title': 'Item 6', 'subtitle': 'Description for item 6'},
    {'title': 'Item 7', 'subtitle': 'Description for item 7'},
    {'title': 'Item 8', 'subtitle': 'Description for item 8'},
    {'title': 'Item 9', 'subtitle': 'Description for item 9'},
    {'title': 'Item 10', 'subtitle': 'Description for item 10'},
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('List View Example'),
      ),
      body: ListView.builder(
        itemCount: items.length,
        itemBuilder: (context, index) {
          return Card(
            margin: EdgeInsets.symmetric(horizontal: 10, vertical: 5),
            elevation: 2,
            child: ListTile(
              leading: CircleAvatar(
                backgroundColor: Colors.teal,
                child: Text(
                  '${index + 1}',
                  style: TextStyle(color: Colors.white),
                ),
              ),
              title: Text(
                items[index]['title']!,
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
              subtitle: Text(items[index]['subtitle']!),
              trailing: Icon(Icons.arrow_forward_ios),
              onTap: () {
                // Handle item tap
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content: Text('Tapped on ${items[index]['title']}'),
                    duration: Duration(seconds: 1),
                  ),
                );
              },
            ),
          );
        },
      ),
    );
  }
}
