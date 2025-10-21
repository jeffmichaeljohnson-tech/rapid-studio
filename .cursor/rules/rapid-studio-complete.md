# Rapid Studio Complete AI Assistant Rules

## Project Mission
Mobile-first creative AI platform targeting 100 images in ≤15 seconds per user.
Building the FASTEST image generation experience with multi-tier prefetching.

## Core Innovation
- Zero-delay user experience through strategic pre-loading
- High-bandwidth preference learning via swipe gestures
- Real-time model personalization with visible improvement by swipe 25
- Multi-modal content: photos, videos, effects, fonts, brand colors

## Tech Stack
- Frontend: Expo SDK 51, React Native, TypeScript, Reanimated 3
- Backend: FastAPI, Redis Streams, Python 3.11
- GPU: Runpod fleet with SDXL-Turbo/FLUX Schnell
- Network: Tailscale secure tunnels
- Infrastructure: Docker, Kubernetes, Terraform

## Performance Targets (NON-NEGOTIABLE)
- First image tile: ≤800ms (achieved in testing)
- Full 100 image grid: ≤10 seconds (beating 15s target)
- SwipeDeck animations: 60fps on UI thread always
- User sees improvement by swipe #25
- Cost: <$0.10 per 100 images
- Zero loading screens (infinite scroll experience)

## Multi-Tier Prefetching Architecture
- Tier 1: Universal base images (CDN cached)
- Tier 2: Demographic clustering (warm cache)
- Tier 3: Personal model (hot cache, 50+ image buffer)

## Code Quality Rules
- TypeScript strict mode always, never use 'any'
- All animations run on UI thread via Reanimated worklets
- Batch all API calls, never individual requests
- Use Expo.Image.prefetch() for performance
- Test in release builds, not dev mode
- Structured logging with correlation IDs
- Error boundaries in all React components

## Mobile App Architecture
- react-native-gesture-handler FIRST in all imports
- Reanimated 3 SharedValues for all state
- expo-router file-based routing convention
- Batch swipe ratings every 10-15 actions
- Maintain 50+ image rolling buffer (increased from 25)
- Progressive image loading with placeholders
- Swipe pattern analysis (timing, hesitation, velocity)

## Backend Architecture
- FastAPI with async/await everywhere
- Redis Streams for job queuing (not pub/sub)
- Circuit breakers for all external calls
- Exponential backoff with jitter
- Multi-stage Docker builds
- Health checks in all containers
- mTLS for inter-service communication
- Predictive generation during swipe sessions

## Performance Optimization
- Pre-warm GPU instances
- Parallel generation across 8-10 GPUs
- Stream images as they complete
- Multi-layer caching (Redis + CDN + local + edge)
- WebSocket for real-time updates
- Progressive JPEG for faster display
- Background intelligence during user sessions

## AI Assistant Guidelines
- Always reference latest docs for Expo, Runpod, Tailscale
- Prioritize user experience and engagement over pure speed
- Design for flow state maintenance (no interruptions)
- Consider addiction potential and design for healthy usage
- Focus on progressive personalization strategies
- Think about the complete user journey from first open to expertise
