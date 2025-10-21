#!/bin/bash

# Build script for runner-gpu container
# This script optimizes the build process to prevent stalls

set -e

echo "🚀 Building runner-gpu container..."

# Navigate to the container directory
cd "$(dirname "$0")/../containers/runner-gpu"

# Set build arguments for better performance
export DOCKER_BUILDKIT=1
export BUILDKIT_PROGRESS=plain

# Build without push first (local build)
echo "📦 Building image locally..."
docker build \
    --platform linux/amd64 \
    --tag rapid-studio/runner-gpu:latest \
    --tag rapid-studio/runner-gpu:$(date +%Y%m%d-%H%M%S) \
    --progress=plain \
    .

echo "✅ Local build complete!"

# Ask if user wants to push
read -p "Do you want to push to registry? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📤 Pushing to registry..."
    docker push rapid-studio/runner-gpu:latest
    echo "✅ Push complete!"
else
    echo "⏭️  Skipping push"
fi

echo "🎉 Build process complete!"
