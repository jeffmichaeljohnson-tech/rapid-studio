const { getDefaultConfig } = require('expo/metro-config');

const config = getDefaultConfig(__dirname);

// Ensure proper handling of worklets and reanimated
config.resolver.platforms = ['ios', 'android', 'native', 'web'];

module.exports = config;
