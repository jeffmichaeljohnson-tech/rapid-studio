// Rapid Studio Mobile API Configuration
export const API_CONFIG = {
  // Base API URL - Updated to use local orchestrator
  BASE_URL: 'http://localhost:8000',
  
  // WebSocket URL for real-time updates
  WS_URL: 'ws://localhost:8000/ws',
  
  // API Endpoints
  ENDPOINTS: {
    // Image generation endpoints
    UNIVERSAL_IMAGES: '/images/universal',
    DEMOGRAPHIC_IMAGES: '/images/demographic',
    PERSONAL_IMAGES: '/images/personal',
    
    // Job management
    BULK_JOBS: '/jobs/bulk',
    
    // Health check
    HEALTH: '/health',
    
    // WebSocket
    WEBSOCKET: '/ws',
  },
  
  // Performance settings
  PERFORMANCE: {
    PREFETCH_BUFFER_SIZE: 50,
    BATCH_SIZE: 10,
    REQUEST_TIMEOUT: 30000,
    RETRY_ATTEMPTS: 3,
  },
  
  // Tier configuration
  TIERS: {
    UNIVERSAL: 'universal',
    DEMOGRAPHIC: 'demographic', 
    PERSONAL: 'personal',
  },
} as const;

export default API_CONFIG;
