import React from 'react';
import { View, StyleSheet } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import SafeSwipeDeck from './components/SafeSwipeDeck';

export default function App() {
  return (
    <View style={styles.container}>
      <StatusBar style="light" backgroundColor="#000000" />
      <SafeSwipeDeck />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000000',
  },
});
