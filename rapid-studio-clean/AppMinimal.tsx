import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { StatusBar } from 'expo-status-bar';

export default function AppMinimal() {
  return (
    <View style={styles.container}>
      <StatusBar style="light" backgroundColor="#000000" />
      <Text style={styles.title}>Rapid Studio</Text>
      <Text style={styles.subtitle}>Minimal Test - No Animations</Text>
      <Text style={styles.text}>If you can see this, the basic app is working!</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000000',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  title: {
    color: '#FFFFFF',
    fontSize: 32,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  subtitle: {
    color: '#888888',
    fontSize: 16,
    textAlign: 'center',
    marginBottom: 20,
  },
  text: {
    color: '#FFFFFF',
    fontSize: 18,
    textAlign: 'center',
  },
});
