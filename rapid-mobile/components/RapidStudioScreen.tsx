import React, { useState, useEffect, useCallback } from 'react';
import { View, StyleSheet, Alert, Text } from 'react-native';
import SwipeDeck from '@/components/SwipeDeck';

const ORCHESTRATOR_URL = 'http://localhost:8000';

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

export default function RapidStudioScreen() {
  const [images, setImages] = useState<ImageData[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'error'>('connecting');

  // Test orchestrator connection
  const testConnection = async () => {
    try {
      const response = await fetch(`${ORCHESTRATOR_URL}/health`);
      if (response.ok) {
        setConnectionStatus('connected');
        return true;
      } else {
        setConnectionStatus('error');
        return false;
      }
    } catch (error) {
      console.error('Connection test failed:', error);
      setConnectionStatus('error');
      return false;
    }
  };

  // Fetch images from orchestrator
  const fetchImages = async (count: number = 25) => {
    try {
      setIsLoading(true);
      
      const response = await fetch(`${ORCHESTRATOR_URL}/images/universal?count=${count}`);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      console.log(`Fetched ${data.images?.length || 0} images from orchestrator`);
      
      if (data.images && Array.isArray(data.images)) {
        const formattedImages: ImageData[] = data.images.map((img: any) => ({
          id: img.id,
          url: img.url,
          prompt: img.prompt,
          tier: img.tier || 'universal',
          metadata: img.metadata || {}
        }));
        
        setImages(prevImages => [...prevImages, ...formattedImages]);
        return formattedImages;
      } else {
        throw new Error('Invalid response format');
      }
    } catch (error) {
      console.error('Failed to fetch images:', error);
      Alert.alert(
        'Connection Error', 
        `Failed to load images from Rapid Studio orchestrator. Make sure the server is running on ${ORCHESTRATOR_URL}`
      );
      return [];
    } finally {
      setIsLoading(false);
    }
  };

  // Handle swipe from SwipeDeck
  const handleSwipe = useCallback(async (rating: SwipeRating) => {
    console.log(`Swiped ${rating.direction} on image ${rating.imageId}`);
  }, []);

  // Handle request for more images
  const handleNeedMoreImages = useCallback(async () => {
    console.log('SwipeDeck requesting more images...');
    await fetchImages(25);
  }, []);

  // Initialize on mount
  useEffect(() => {
    const initialize = async () => {
      console.log('Initializing Rapid Studio connection...');
      
      const isConnected = await testConnection();
      if (isConnected) {
        await fetchImages(25);
      }
    };

    initialize();
  }, []);

  // Loading screen
  if (isLoading && images.length === 0) {
    return (
      <View style={styles.loadingContainer}>
        <Text style={styles.loadingTitle}>Rapid Studio</Text>
        <Text style={styles.loadingText}>
          {connectionStatus === 'connecting' && 'Connecting to orchestrator...'}
          {connectionStatus === 'connected' && 'Loading creative assets...'}
          {connectionStatus === 'error' && 'Connection failed. Check orchestrator.'}
        </Text>
        <Text style={styles.urlText}>{ORCHESTRATOR_URL}</Text>
      </View>
    );
  }

  // Error screen
  if (connectionStatus === 'error' && images.length === 0) {
    return (
      <View style={styles.errorContainer}>
        <Text style={styles.errorTitle}>Connection Error</Text>
        <Text style={styles.errorText}>
          Cannot connect to Rapid Studio orchestrator.
          {'\n\n'}Make sure the FastAPI server is running at:
          {'\n'}{ORCHESTRATOR_URL}
        </Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <SwipeDeck
        images={images}
        onSwipe={handleSwipe}
        onNeedMoreImages={handleNeedMoreImages}
        isLoading={isLoading}
        prefetchBuffer={50}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
  },
  loadingContainer: {
    flex: 1,
    backgroundColor: '#000',
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 40,
  },
  loadingTitle: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 20,
  },
  loadingText: {
    fontSize: 18,
    color: '#888',
    textAlign: 'center',
    marginBottom: 10,
  },
  urlText: {
    fontSize: 14,
    color: '#666',
    fontFamily: 'monospace',
  },
  errorContainer: {
    flex: 1,
    backgroundColor: '#000',
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 40,
  },
  errorTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#ff4444',
    marginBottom: 20,
  },
  errorText: {
    fontSize: 16,
    color: '#ccc',
    textAlign: 'center',
    lineHeight: 24,
    marginBottom: 20,
  },
});
