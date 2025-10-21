import React, { useState, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Dimensions,
  PanResponder,
  Animated,
  Alert,
} from 'react-native';
import { Image } from 'expo-image';

const { width: screenWidth, height: screenHeight } = Dimensions.get('window');

interface ImageData {
  id: string;
  url: string;
  title: string;
}

const SafeSwipeDeck: React.FC = () => {
  const [images] = useState<ImageData[]>([
    { id: '1', url: 'https://picsum.photos/400/600?random=1', title: 'Sample Image 1' },
    { id: '2', url: 'https://picsum.photos/400/600?random=2', title: 'Sample Image 2' },
    { id: '3', url: 'https://picsum.photos/400/600?random=3', title: 'Sample Image 3' },
    { id: '4', url: 'https://picsum.photos/400/600?random=4', title: 'Sample Image 4' },
    { id: '5', url: 'https://picsum.photos/400/600?random=5', title: 'Sample Image 5' },
  ]);
  
  const [currentIndex, setCurrentIndex] = useState(0);
  const pan = useRef(new Animated.ValueXY()).current;
  const scale = useRef(new Animated.Value(1)).current;

  const panResponder = PanResponder.create({
    onStartShouldSetPanResponder: () => true,
    onMoveShouldSetPanResponder: () => true,
    onPanResponderGrant: () => {
      pan.setOffset({
        x: pan.x._value,
        y: pan.y._value,
      });
      Animated.spring(scale, {
        toValue: 0.95,
        useNativeDriver: false,
      }).start();
    },
    onPanResponderMove: Animated.event(
      [null, { dx: pan.x, dy: pan.y }],
      { useNativeDriver: false }
    ),
    onPanResponderRelease: (_, gesture) => {
      pan.flattenOffset();
      
      const swipeThreshold = screenWidth * 0.3;
      const shouldSwipe = Math.abs(gesture.dx) > swipeThreshold;
      
      if (shouldSwipe) {
        const direction = gesture.dx > 0 ? 'right' : 'left';
        const rating = direction === 'right' ? 'like' : 'dislike';
        
        console.log(`Swiped ${direction} on image ${images[currentIndex]?.id} - Rating: ${rating}`);
        
        // Animate card off screen
        Animated.parallel([
          Animated.timing(pan, {
            toValue: { 
              x: direction === 'right' ? screenWidth * 1.5 : -screenWidth * 1.5, 
              y: gesture.dy 
            },
            duration: 300,
            useNativeDriver: false,
          }),
          Animated.timing(scale, {
            toValue: 0.8,
            duration: 300,
            useNativeDriver: false,
          }),
        ]).start(() => {
          // Move to next image
          if (currentIndex < images.length - 1) {
            setCurrentIndex(currentIndex + 1);
          } else {
            Alert.alert('End of deck', 'You\'ve seen all images!');
            setCurrentIndex(0);
          }
          
          // Reset animation values
          pan.setValue({ x: 0, y: 0 });
          scale.setValue(1);
        });
      } else {
        // Snap back to center
        Animated.parallel([
          Animated.spring(pan, {
            toValue: { x: 0, y: 0 },
            useNativeDriver: false,
          }),
          Animated.spring(scale, {
            toValue: 1,
            useNativeDriver: false,
          }),
        ]).start();
      }
    },
  });

  const currentImage = images[currentIndex];
  const nextImage = images[currentIndex + 1];

  const cardStyle = {
    transform: [
      { translateX: pan.x },
      { translateY: pan.y },
      { scale: scale },
    ],
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Rapid Studio</Text>
        <Text style={styles.subtitle}>Swipe to train your preferences</Text>
      </View>

      <View style={styles.cardContainer}>
        {/* Next card preview */}
        {nextImage && (
          <View style={[styles.card, styles.nextCard]}>
            <Image
              source={{ uri: nextImage.url }}
              style={styles.image}
              contentFit="cover"
            />
          </View>
        )}

        {/* Current card */}
        <Animated.View
          style={[styles.card, cardStyle]}
          {...panResponder.panHandlers}
        >
          <Image
            source={{ uri: currentImage?.url }}
            style={styles.image}
            contentFit="cover"
            transition={200}
          />
          <View style={styles.cardOverlay}>
            <Text style={styles.imageTitle}>{currentImage?.title}</Text>
          </View>
        </Animated.View>
      </View>

      <View style={styles.instructions}>
        <Text style={styles.instructionText}>
          👈 Swipe left to dislike • Swipe right to like 👉
        </Text>
        <Text style={styles.counterText}>
          {currentIndex + 1} / {images.length}
        </Text>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000000',
  },
  header: {
    paddingTop: 60,
    paddingHorizontal: 20,
    paddingBottom: 20,
    alignItems: 'center',
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
  },
  cardContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    position: 'relative',
  },
  card: {
    width: screenWidth * 0.85,
    height: screenHeight * 0.6,
    borderRadius: 20,
    backgroundColor: '#1A1A1A',
    shadowColor: '#000000',
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.3,
    shadowRadius: 20,
    elevation: 10,
    position: 'absolute',
  },
  nextCard: {
    opacity: 0.5,
    transform: [{ scale: 0.95 }],
    zIndex: -1,
  },
  image: {
    width: '100%',
    height: '100%',
    borderRadius: 20,
  },
  cardOverlay: {
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
    paddingHorizontal: 20,
    paddingBottom: 40,
    alignItems: 'center',
  },
  instructionText: {
    color: '#888888',
    fontSize: 16,
    textAlign: 'center',
    marginBottom: 10,
  },
  counterText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '600',
  },
});

export default SafeSwipeDeck;
