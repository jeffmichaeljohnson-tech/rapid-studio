#!/bin/bash

echo "🚀 Rapid Studio - Phase 2 GPU Deployment"
echo "========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker Desktop.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker is running${NC}"
echo ""

# Get Docker Hub username
echo "📦 Docker Hub Setup"
echo "-------------------"
read -p "Enter your Docker Hub username (or press Enter to skip push): " DOCKERHUB_USERNAME

# Build GPU worker image
echo ""
echo "🔨 Building GPU worker Docker image..."
cd containers/runner-gpu

docker build -t rapid-gpu-worker:latest . || {
    echo -e "${RED}❌ Build failed${NC}"
    exit 1
}

echo -e "${GREEN}✅ GPU worker image built successfully${NC}"

# Optional: Push to Docker Hub
if [ ! -z "$DOCKERHUB_USERNAME" ]; then
    echo ""
    echo "📤 Pushing to Docker Hub..."
    
    docker tag rapid-gpu-worker:latest $DOCKERHUB_USERNAME/rapid-gpu-worker:latest
    
    echo "Please login to Docker Hub:"
    docker login
    
    docker push $DOCKERHUB_USERNAME/rapid-gpu-worker:latest || {
        echo -e "${YELLOW}⚠️  Push failed. You can deploy manually later.${NC}"
    }
    
    echo -e "${GREEN}✅ Image pushed: $DOCKERHUB_USERNAME/rapid-gpu-worker:latest${NC}"
    echo ""
    echo "📋 RunPod Deployment Instructions:"
    echo "   1. Go to https://runpod.io/console/pods"
    echo "   2. Click 'Deploy'"
    echo "   3. Select GPU: RTX 4000 Ada Generation"
    echo "   4. Container Image: $DOCKERHUB_USERNAME/rapid-gpu-worker:latest"
    echo "   5. Expose HTTP Port: 8000"
    echo "   6. Click 'Deploy'"
else
    echo ""
    echo -e "${YELLOW}⚠️  Skipping Docker Hub push${NC}"
    echo "   You can test locally or push manually later."
fi

# Test locally option
echo ""
read -p "Do you want to test the GPU worker locally? (y/n): " TEST_LOCAL

if [ "$TEST_LOCAL" = "y" ] || [ "$TEST_LOCAL" = "Y" ]; then
    echo ""
    echo "🧪 Starting GPU worker locally on port 8001..."
    echo "   (This will use CPU and be slower, but confirms the code works)"
    
    docker run -d -p 8001:8000 --name rapid-gpu-test rapid-gpu-worker:latest
    
    echo ""
    echo "⏳ Waiting for model to load (60 seconds)..."
    sleep 60
    
    echo ""
    echo "🏥 Checking health..."
    curl -s http://localhost:8001/health | jq '.' || echo "Health check response"
    
    echo ""
    echo -e "${GREEN}✅ GPU worker is running locally on http://localhost:8001${NC}"
    echo ""
    echo "📋 Test commands:"
    echo "   curl http://localhost:8001/health"
    echo "   curl -X POST http://localhost:8001/generate \\"
    echo "     -H 'Content-Type: application/json' \\"
    echo "     -d '{\"prompt\": \"professional product photography\"}'"
    echo ""
    echo "To stop: docker stop rapid-gpu-test && docker rm rapid-gpu-test"
fi

# Update orchestrator
echo ""
read -p "Do you have a RunPod GPU endpoint URL to add? (y/n): " HAS_ENDPOINT

if [ "$HAS_ENDPOINT" = "y" ] || [ "$HAS_ENDPOINT" = "Y" ]; then
    echo ""
    read -p "Enter RunPod endpoint URL (e.g., https://abc123-8000.proxy.runpod.net): " GPU_ENDPOINT
    
    cd ../../containers/orchestrator
    
    # Backup current docker-compose
    cp docker-compose.yml docker-compose.yml.backup
    
    # Update docker-compose with GPU endpoint
    cat > docker-compose.yml << EOF
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    container_name: rapid-redis
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  orchestrator:
    build: .
    container_name: rapid-orchestrator
    ports:
      - "8000:8000"
    environment:
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - ENVIRONMENT=development
      - GPU_WORKERS=${GPU_ENDPOINT}
    depends_on:
      redis:
        condition: service_healthy
    volumes:
      - ./main.py:/app/main.py
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload

volumes:
  redis-data:
EOF

    echo -e "${GREEN}✅ Updated orchestrator with GPU endpoint${NC}"
    
    # Restart orchestrator
    echo ""
    echo "🔄 Restarting orchestrator..."
    docker-compose down
    docker-compose up -d
    
    echo ""
    echo "⏳ Waiting for services to start..."
    sleep 5
    
    echo ""
    echo "🏥 Checking orchestrator health..."
    curl -s http://localhost:8000/health | jq '.' || echo "Health check response"
    
    echo ""
    echo -e "${GREEN}✅ Orchestrator updated and running${NC}"
    echo ""
    echo "📋 Test it:"
    echo "   curl http://localhost:8000/images/universal?count=5"
fi

echo ""
echo "🎉 Phase 2 GPU Deployment Complete!"
echo ""
echo "📊 Summary:"
echo "   ✅ GPU worker Docker image built"
if [ ! -z "$DOCKERHUB_USERNAME" ]; then
    echo "   ✅ Image pushed to Docker Hub"
fi
if [ "$TEST_LOCAL" = "y" ] || [ "$TEST_LOCAL" = "Y" ]; then
    echo "   ✅ Local test instance running"
fi
if [ "$HAS_ENDPOINT" = "y" ] || [ "$HAS_ENDPOINT" = "Y" ]; then
    echo "   ✅ Orchestrator connected to GPU worker"
fi
echo ""
echo "📖 Next Steps:"
echo "   1. Test mobile app: cd rapid-mobile && npm start"
echo "   2. Deploy more GPUs for 100 images in 15s target"
echo "   3. Implement training loop (Phase 3)"
echo ""
echo "📚 See Phase 2 GPU Deployment Guide for full instructions"
