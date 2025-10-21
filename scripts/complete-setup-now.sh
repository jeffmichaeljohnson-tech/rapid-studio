#!/bin/bash

echo "🎯 FINAL RAPID STUDIO SETUP COMPLETION"
echo "====================================="

# Install mobile dependencies
echo "📱 Installing mobile app dependencies..."
cd rapid-mobile
npm install

# Add missing dependencies for enhanced SwipeDeck
npm install react-native-gesture-handler react-native-reanimated expo-image expo-haptics

echo "✅ Mobile dependencies installed"
cd ..

# Build containers
echo "🐳 Building Docker containers..."
chmod +x scripts/build-containers.sh
./scripts/build-containers.sh

echo "✅ Containers built"

# Start development environment
echo "🚀 Starting development environment..."
docker-compose -f deploy/compose/docker-compose.yml up -d

echo "✅ Development environment started"

echo ""
echo "🎉 RAPID STUDIO SETUP COMPLETE!"
echo "==============================="
echo ""
echo "Next steps:"
echo "1. Start mobile app: cd rapid-mobile && expo start"
echo "2. Deploy GPU fleet: npm run deploy:runpod"
echo "3. Test performance: npm run test:100images"
echo ""
echo "Services running:"
echo "- Orchestrator: http://100.103.213.111:8000"
echo "- Redis: http://100.103.213.111:6379"
echo "- Grafana: http://100.103.213.111:3000"
echo ""
echo "Ready to build the world's fastest creative AI platform!"
