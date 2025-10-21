import React, { useEffect, useState, useCallback, useRef } from 'react';
import { View, Dimensions, StyleSheet, Text, Alert } from 'react-native';
import { Gesture, GestureDetector, GestureHandlerRootView } from 'react-native-gesture-handler';
import Animated, {
  useAnimatedStyle,
  useSharedValue,
  withSpring,
  withTiming,
  runOnJS,
  interpolate,
} from 'react-native-reanimated';
import { Image } from 'expo-image';
import * as Haptics from 'expo-haptics';

const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = Dimensions.get('window');
const CARD_WIDTH = SCREEN_WIDTH * 0.9;
const CARD_HEIGHT = SCREEN_HEIGHT * 0.7;
const SWIPE_THRESHOLD = SCREEN_WIDTH * 0.25;

interface ImageData {
  id: string;
  url: string;
  prompt?: string;
  tier: 'universal' | 'demographic' | 'personal';
  metadata?: Record<string, any>;
}

interface SwipeRating {
  imageId: string;
  direction: 'left' | 'right';
  timestamp: number;
  swipeVelocity: number;
  confidence: number;
  hesitationTime: number;
  tier: string;
}

interface SwipeDeckProps {
  images: ImageData[];
  onSwipe: (rating: SwipeRating) => void;
  onNeedMoreImages: () => void;
  isLoading?: boolean;
  prefetchBuffer?: number;
}

export default function SwipeDeck({ 
  images, 
  onSwipe, 
  onNeedMoreImages, 
  isLoading = false,
  prefetchBuffer = 50 
}: SwipeDeckProps) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [ratingBatch, setRatingBatch] = useState<SwipeRating[]>([]);
  const [improvementVisible, setImprovementVisible] = useState(false);
  
  // Performance tracking
  const swipeStartTime = useRef<number>(0);
  const totalSwipes = useRef<number>(0);
  
  // Animated values
  const translateX = useSharedValue(0);
  const translateY = useSharedValue(0);
  const rotation = useSharedValue(0);
  const scale = useSharedValue(1);
  const backgroundScale = useSharedValue(0.95);

  // Enhanced prefetching with multi-tier strategy
  useEffect(() => {
    const aggressivePrefetch = async () => {
      const start = Math.max(0, currentIndex);
      const end = Math.min(images.length, currentIndex + prefetchBuffer);
      
      // Prioritize by tier: personal > demographic > universal
      const imagesToPrefetch = images.slice(start, end)
        .sort((a, b) => {
          const tierPriority = { personal: 3, demographic: 2, universal: 1 };
          return tierPriority[b.tier] - tierPriority[a.tier];
        });
      
      // Prefetch in parallel for speed
      const prefetchPromises = imagesToPrefetch.map(async (img, index) => {
        try {
          await Image.prefetch(img.url);
          console.log(`Prefetched ${img.tier} image ${index + 1}/${imagesToPrefetch.length}`);
        } catch (error) {
          console.warn(`Failed to prefetch ${img.tier} image:`, error);
        }
      });
      
      await Promise.allSettled(prefetchPromises);
    };

    aggressivePrefetch();
  }, [currentIndex, images, prefetchBuffer]);

  // Request more images when buffer runs low
  useEffect(() => {
    if (images.length - currentIndex <= 10) {
      onNeedMoreImages();
    }
  }, [currentIndex, images.length, onNeedMoreImages]);

  // Track improvement visibility
  useEffect(() => {
    if (totalSwipes.current >= 25 && !improvementVisible) {
      setImprovementVisible(true);
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      Alert.alert("🎯 AI Learning!", "Your personal model is getting smarter with each swipe!");
    }
  }, [totalSwipes.current, improvementVisible]);

  const handleSwipeStart = useCallback(() => {
    swipeStartTime.current = Date.now();
  }, []);

  const handleSwipeComplete = useCallback((direction: 'left' | 'right', velocity: number) => {
    const currentImage = images[currentIndex];
    if (!currentImage) return;

    const swipeEndTime = Date.now();
    const hesitationTime = swipeEndTime - swipeStartTime.current;
    totalSwipes.current += 1;

    const rating: SwipeRating = {
      imageId: currentImage.id,
      direction,
      timestamp: swipeEndTime,
      swipeVelocity: Math.abs(velocity),
      confidence: Math.min(1, Math.abs(velocity) / 1000),
      hesitationTime,
      tier: currentImage.tier,
    };

    // Add to batch for performance
    setRatingBatch(prev => {
      const newBatch = [...prev, rating];
      
      // Submit batch every 10 ratings or every 30 seconds
      if (newBatch.length >= 10) {
        onSwipe(rating); // In production, this would be batch submission
        return [];
      }
      
      return newBatch;
    });

    // Enhanced haptic feedback based on tier
    const hapticIntensity = currentImage.tier === 'personal' 
      ? Haptics.ImpactFeedbackStyle.Heavy
      : direction === 'right' 
        ? Haptics.ImpactFeedbackStyle.Light 
        : Haptics.ImpactFeedbackStyle.Medium;
    
    Haptics.impactAsync(hapticIntensity);

    setCurrentIndex(prev => prev + 1);
    
    // Reset animations for next card
    translateX.value = 0;
    translateY.value = 0;
    rotation.value = 0;
    scale.value = 1;
    backgroundScale.value = 0.95;
  }, [currentIndex, images, onSwipe]);

  const panGesture = Gesture.Pan()
    .onBegin(() => {
      'worklet';
      runOnJS(handleSwipeStart)();
    })
    .onUpdate((event) => {
      'worklet';
      translateX.value = event.translationX;
      translateY.value = event.translationY * 0.3;
      
      rotation.value = interpolate(
        event.translationX,
        [-SCREEN_WIDTH, 0, SCREEN_WIDTH],
        [-30, 0, 30]
      );
      
      const progress = Math.abs(event.translationX) / SWIPE_THRESHOLD;
      scale.value = interpolate(progress, [0, 1], [1, 0.95]);
      backgroundScale.value = interpolate(progress, [0, 1], [0.95, 1]);
    })
    .onEnd((event) => {
      'worklet';
      const shouldSwipe = Math.abs(event.translationX) > SWIPE_THRESHOLD;
      
      if (shouldSwipe) {
        const direction = event.translationX > 0 ? 'right' : 'left';
        const targetX = direction === 'right' ? SCREEN_WIDTH * 1.5 : -SCREEN_WIDTH * 1.5;
        
        translateX.value = withTiming(targetX, { duration: 300 });
        translateY.value = withTiming(event.translationY * 2, { duration: 300 });
        rotation.value = withTiming(direction === 'right' ? 45 : -45, { duration: 300 });
        scale.value = withTiming(0.8, { duration: 300 });
        backgroundScale.value = withSpring(1);
        
        runOnJS(handleSwipeComplete)(direction, event.velocityX);
      } else {
        translateX.value = withSpring(0);
        translateY.value = withSpring(0);
        rotation.value = withSpring(0);
        scale.value = withSpring(1);
        backgroundScale.value = withSpring(0.95);
      }
    });

  const cardAnimatedStyle = useAnimatedStyle(() => ({
    transform: [
      { translateX: translateX.value },
      { translateY: translateY.value },
      { rotate: `${rotation.value}deg` },
      { scale: scale.value },
    ],
  }));

  const backgroundAnimatedStyle = useAnimatedStyle(() => ({
    transform: [{ scale: backgroundScale.value }],
    opacity: 0.8,
  }));

  const currentImage = images[currentIndex];
  const nextImage = images[currentIndex + 1];

  if (!currentImage) {
    return (
      <View style={styles.container}>
        <View style={styles.emptyState}>
          <Text style={styles.emptyText}>
            {isLoading ? 'Generating personalized content...' : 'Loading more amazing images...'}
          </Text>
        </View>
      </View>
    );
  }

  return (
    <GestureHandlerRootView style={styles.container}>
      <View style={styles.deckContainer}>
        {/* Background card for smooth transitions */}
        {nextImage && (
          <Animated.View style={[styles.card, styles.backgroundCard, backgroundAnimatedStyle]}>
            <Image
              source={{ uri: nextImage.url }}
              style={styles.cardImage}
              contentFit="cover"
              transition={200}
              placeholder="blur"
            />
          </Animated.View>
        )}

        {/* Current card with gesture */}
        <GestureDetector gesture={panGesture}>
          <Animated.View style={[styles.card, cardAnimatedStyle]}>
            <Image
              source={{ uri: currentImage.url }}
              style={styles.cardImage}
              contentFit="cover"
              transition={200}
              placeholder="blur"
            />
            
            {/* Tier indicator for debugging */}
            <View style={[styles.tierIndicator, 
              currentImage.tier === 'personal' && styles.personalTier,
              currentImage.tier === 'demographic' && styles.demographicTier,
              currentImage.tier === 'universal' && styles.universalTier
            ]}>
              <Text style={styles.tierText}>
                {currentImage.tier === 'personal' ? '🎯' : 
                 currentImage.tier === 'demographic' ? '👥' : '🌐'}
              </Text>
            </View>
          </Animated.View>
        </GestureDetector>

        {/* Progress and improvement indicators */}
        <View style={styles.progressContainer}>
          <Text style={styles.progressText}>
            {currentIndex + 1} / {images.length}
          </Text>
          {improvementVisible && (
            <Text style={styles.improvementText}>
              🧠 AI Learning Active
            </Text>
          )}
        </View>
      </View>
    </GestureHandlerRootView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#000' },
  deckContainer: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  card: {
    width: CARD_WIDTH,
    height: CARD_HEIGHT,
    borderRadius: 20,
    position: 'absolute',
    backgroundColor: '#fff',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 4.65,
    elevation: 8,
  },
  backgroundCard: { zIndex: 1 },
  cardImage: { width: '100%', height: '100%', borderRadius: 20 },
  tierIndicator: {
    position: 'absolute',
    top: 20,
    right: 20,
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
  },
  personalTier: { borderColor: '#4CAF50', borderWidth: 2 },
  demographicTier: { borderColor: '#FF9800', borderWidth: 2 },
  universalTier: { borderColor: '#2196F3', borderWidth: 2 },
  tierText: { fontSize: 16 },
  progressContainer: {
    position: 'absolute',
    bottom: 100,
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 10,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    borderRadius: 20,
  },
  progressText: { color: '#fff', fontSize: 16, fontWeight: '600' },
  improvementText: { color: '#4CAF50', fontSize: 14, fontWeight: '600', marginTop: 5 },
  emptyState: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  emptyText: { color: '#fff', fontSize: 18, textAlign: 'center' },
});
