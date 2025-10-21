import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Dimensions,
  Alert,
} from 'react-native';
import { StatusBar } from 'expo-status-bar';
import {
  GestureHandlerRootView,
  PanGestureHandler,
  PanGestureHandlerGestureEvent,
} from 'react-native-gesture-handler';
import Animated, {
  useAnimatedGestureHandler,
  useAnimatedStyle,
  useSharedValue,
  withSpring,
  withTiming,
  runOnJS,
  interpolate,
  Extrapolate,
} from 'react-native-reanimated';
import { Image } from 'expo-image';

const { width: screenWidth, height: screenHeight } = Dimensions.get('window');

interface ImageData {
  id: string;
  url: string;
  title: string;
}

const SwipeDeck: React.FC = () => {
  const [images, setImages] = useState<ImageData[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isLoading, setIsLoading] = useState(true);

  // Animation values
  const translateX = useSharedValue(0);
  const translateY = useSharedValue(0);
  const rotate = useSharedValue(0);
  const scale = useSharedValue(1);

  // Load sample images
  useEffect(() => {
    loadSampleImages();
  }, []);

  const loadSampleImages = async () => {
    try {
      // Sample images for testing - replace with real API calls
      const sampleImages: ImageData[] = [
        {
          id: '1',
          url: 'https://picsum.photos/400/600?random=1',
          title: 'Sample Image 1'
        },
        {
          id: '2', 
          url: 'https://picsum.photos/400/600?random=2',
          title: 'Sample Image 2'
        },
        {
          id: '3',
          url: 'https://picsum.photos/400/600?random=3', 
          title: 'Sample Image 3'
        },
        {
          id: '4',
          url: 'https://picsum.photos/400/600?random=4',
          title: 'Sample Image 4'
        },
        {
          id: '5',
          url: 'https://picsum.photos/400/600?random=5',
          title: 'Sample Image 5'
        },
      ];
      
      setImages(sampleImages);
      setIsLoading(false);
    } catch (error) {
      console.error('Error loading images:', error);
      setIsLoading(false);
    }
  };

  const onSwipeComplete = (direction: 'left' | 'right') => {
    const rating = direction === 'right' ? 'like' : 'dislike';
    console.log(`Swiped ${direction} on image ${images[currentIndex]?.id} - Rating: ${rating}`);
    
    // Move to next image
    if (currentIndex < images.length - 1) {
      setCurrentIndex(currentIndex + 1);
    } else {
      // Load more images or show completion
      Alert.alert('End of deck', 'Loading more images...');
      loadSampleImages();
      setCurrentIndex(0);
    }
    
    // Reset animation values
    translateX.value = 0;
    translateY.value = 0;
    rotate.value = 0;
    scale.value = 1;
  };

  const gestureHandler = useAnimatedGestureHandler<PanGestureHandlerGestureEvent>({
    onStart: () => {
      scale.value = withSpring(0.95);
    },
    onActive: (event) => {
      translateX.value = event.translationX;
      translateY.value = event.translationY;
      rotate.value = interpolate(
        event.translationX,
        [-screenWidth, screenWidth],
        [-30, 30],
        Extrapolate.CLAMP
      );
    },
    onEnd: (event) => {
      const shouldSwipe = Math.abs(event.translationX) > screenWidth * 0.3;
      
      if (shouldSwipe) {
        const direction = event.translationX > 0 ? 'right' : 'left';
        translateX.value = withTiming(
          event.translationX > 0 ? screenWidth * 1.5 : -screenWidth * 1.5,
          { duration: 300 }
        );
        translateY.value = withTiming(event.translationY, { duration: 300 });
        scale.value = withTiming(0.8, { duration: 300 });
        
        // Call swipe complete after animation
        runOnJS(onSwipeComplete)(direction);
      } else {
        // Snap back to center
        translateX.value = withSpring(0);
        translateY.value = withSpring(0);
        rotate.value = withSpring(0);
        scale.value = withSpring(1);
      }
    },
  });

  const animatedStyle = useAnimatedStyle(() => {
    return {
      transform: [
        { translateX: translateX.value },
        { translateY: translateY.value },
        { rotate: `${rotate.value}deg` },
        { scale: scale.value },
      ],
    };
  });

  if (isLoading) {
    return (
      <View style={styles.loadingContainer}>
        <Text style={styles.loadingText}>Loading images...</Text>
      </View>
    );
  }

  const currentImage = images[currentIndex];

  if (!currentImage) {
    return (
      <View style={styles.loadingContainer}>
        <Text style={styles.loadingText}>No more images</Text>
      </View>
    );
  }

  return (
    <GestureHandlerRootView style={styles.container}>
      <StatusBar style="light" />
      
      <View style={styles.header}>
        <Text style={styles.title}>Rapid Studio</Text>
        <Text style={styles.subtitle}>Swipe to train your preferences</Text>
      </View>

      <View style={styles.cardContainer}>
        <PanGestureHandler onGestureEvent={gestureHandler}>
          <Animated.View style={[styles.card, animatedStyle]}>
            <Image
              source={{ uri: currentImage.url }}
              style={styles.image}
              contentFit="cover"
              transition={200}
            />
            <View style={styles.cardOverlay}>
              <Text style={styles.imageTitle}>{currentImage.title}</Text>
            </View>
          </Animated.View>
        </PanGestureHandler>

        {/* Next card preview */}
        {images[currentIndex + 1] && (
          <View style={[styles.card, styles.nextCard]}>
            <Image
              source={{ uri: images[currentIndex + 1].url }}
              style={styles.image}
              contentFit="cover"
            />
          </View>
        )}
      </View>

      <View style={styles.instructions}>
        <Text style={styles.instructionText}>
          👈 Swipe left to dislike • Swipe right to like 👉
        </Text>
        <Text style={styles.counterText}>
          {currentIndex + 1} / {images.length}
        </Text>
      </View>
    </GestureHandlerRootView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000000',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#000000',
  },
  loadingText: {
    color: '#FFFFFF',
    fontSize: 18,
    fontWeight: '600',
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

export default SwipeDeck;
