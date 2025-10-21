import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Dimensions,
  PanResponder,
  Animated,
} from 'react-native';
import { Image } from 'expo-image';

const { width: screenWidth, height: screenHeight } = Dimensions.get('window');

interface ImageData {
  id: string;
  url: string;
  title: string;
}

export default function SimpleSwipeDeck() {
  const [images] = useState<ImageData[]>([
    { id: '1', url: 'https://picsum.photos/400/600?random=1', title: 'Sample 1' },
    { id: '2', url: 'https://picsum.photos/400/600?random=2', title: 'Sample 2' },
    { id: '3', url: 'https://picsum.photos/400/600?random=3', title: 'Sample 3' },
  ]);
  
  const [currentIndex, setCurrentIndex] = useState(0);
  const pan = new Animated.ValueXY();

  const panResponder = PanResponder.create({
    onStartShouldSetPanResponder: () => true,
    onPanResponderMove: Animated.event([null, { dx: pan.x, dy: pan.y }], {
      useNativeDriver: false,
    }),
    onPanResponderRelease: (_, gesture) => {
      if (Math.abs(gesture.dx) > screenWidth * 0.3) {
        const direction = gesture.dx > 0 ? 'right' : 'left';
        console.log(`Swiped ${direction} on ${images[currentIndex]?.title}`);
        
        setCurrentIndex((prev) => (prev + 1) % images.length);
        pan.setValue({ x: 0, y: 0 });
      } else {
        Animated.spring(pan, {
          toValue: { x: 0, y: 0 },
          useNativeDriver: false,
        }).start();
      }
    },
  });

  const currentImage = images[currentIndex];

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Rapid Studio</Text>
      <Text style={styles.subtitle}>Simple Swipe Test</Text>
      
      <View style={styles.cardContainer}>
        <Animated.View
          style={[
            styles.card,
            {
              transform: [
                { translateX: pan.x },
                { translateY: pan.y },
              ],
            },
          ]}
          {...panResponder.panHandlers}
        >
          <Image
            source={{ uri: currentImage?.url }}
            style={styles.image}
            contentFit="cover"
          />
          <View style={styles.overlay}>
            <Text style={styles.imageTitle}>{currentImage?.title}</Text>
          </View>
        </Animated.View>
      </View>
      
      <Text style={styles.instructions}>
        Swipe left or right • {currentIndex + 1} / {images.length}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000000',
    paddingTop: 60,
  },
  title: {
    color: '#FFFFFF',
    fontSize: 32,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 8,
  },
  subtitle: {
    color: '#888888',
    fontSize: 16,
    textAlign: 'center',
    marginBottom: 40,
  },
  cardContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  card: {
    width: screenWidth * 0.85,
    height: screenHeight * 0.6,
    borderRadius: 20,
    backgroundColor: '#1A1A1A',
  },
  image: {
    width: '100%',
    height: '100%',
    borderRadius: 20,
  },
  overlay: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    borderBottomLeftRadius: 20,
    borderBottomRightRadius: 20,
    padding: 20,
  },
  imageTitle: {
    color: '#FFFFFF',
    fontSize: 18,
    fontWeight: '600',
  },
  instructions: {
    color: '#888888',
    fontSize: 16,
    textAlign: 'center',
    paddingBottom: 40,
  },
});
