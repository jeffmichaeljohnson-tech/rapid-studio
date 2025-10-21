#!/bin/bash
set -e

# Rapid Studio - RunPod GPU Fleet Deployment
# Deploys docker image to RunPod GPUs with Tailscale networking

GPU_TYPE="${1:-RTX 4000 Ada}"
GPU_COUNT="${2:-8}"
IMAGE_NAME="johnson77777/rapid-gpu-worker:latest"

echo "🚀 Deploying Rapid Studio GPU Fleet"
echo "   GPU Type: $GPU_TYPE"
echo "   Count: $GPU_COUNT"
echo "   Image: $IMAGE_NAME"

# Check for RunPod API key
if [ -z "$RUNPOD_API_KEY" ]; then
    echo "❌ Error: RUNPOD_API_KEY environment variable not set"
    echo "   Get your API key from: https://runpod.io/console/user/settings"
    exit 1
fi

# Check for Tailscale auth key
if [ -z "$TAILSCALE_AUTHKEY" ]; then
    echo "❌ Error: TAILSCALE_AUTHKEY environment variable not set"
    echo "   Generate an auth key from: https://login.tailscale.com/admin/settings/keys"
    exit 1
fi

# Create RunPod template
TEMPLATE_PAYLOAD=$(cat <<EOF
{
  "name": "rapid-studio-gpu-worker",
  "imageName": "$IMAGE_NAME",
  "dockerArgs": "",
  "containerDiskInGb": 50,
  "volumeInGb": 0,
  "volumeMountPath": "",
  "ports": "8000/http",
  "env": [
    {
      "key": "TAILSCALE_AUTHKEY",
      "value": "$TAILSCALE_AUTHKEY"
    },
    {
      "key": "ORCHESTRATOR_URL",
      "value": "http://orchestrator.tail-scale.ts.net:8001"
    }
  ],
  "isServerless": false
}
EOF
)

echo "📝 Creating RunPod template..."
TEMPLATE_RESPONSE=$(curl -s -X POST \
  "https://api.runpod.io/graphql" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $RUNPOD_API_KEY" \
  -d "{\"query\":\"mutation { saveTemplate(input: $TEMPLATE_PAYLOAD) { id name } }\"}")

TEMPLATE_ID=$(echo "$TEMPLATE_RESPONSE" | jq -r '.data.saveTemplate.id')

if [ "$TEMPLATE_ID" == "null" ]; then
    echo "❌ Failed to create template"
    echo "$TEMPLATE_RESPONSE" | jq .
    exit 1
fi

echo "✅ Template created: $TEMPLATE_ID"

# Deploy pods
echo "🖥️  Deploying $GPU_COUNT GPU pods..."

for i in $(seq 1 $GPU_COUNT); do
    POD_NAME="rapid-gpu-worker-$i"
    
    POD_PAYLOAD=$(cat <<EOF
{
  "cloudType": "SECURE",
  "gpuTypeId": "$GPU_TYPE",
  "name": "$POD_NAME",
  "templateId": "$TEMPLATE_ID",
  "gpuCount": 1,
  "volumeInGb": 0,
  "containerDiskInGb": 50,
  "minVcpuCount": 4,
  "minMemoryInGb": 16,
  "dockerArgs": "",
  "ports": "8000/http",
  "volumeMountPath": "",
  "env": [
    {
      "key": "WORKER_ID",
      "value": "$i"
    }
  ]
}
EOF
)
    
    POD_RESPONSE=$(curl -s -X POST \
      "https://api.runpod.io/graphql" \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer $RUNPOD_API_KEY" \
      -d "{\"query\":\"mutation { podFindAndDeployOnDemand(input: $POD_PAYLOAD) { id desiredStatus imageName } }\"}")
    
    POD_ID=$(echo "$POD_RESPONSE" | jq -r '.data.podFindAndDeployOnDemand.id')
    
    if [ "$POD_ID" == "null" ]; then
        echo "⚠️  Failed to deploy pod $i"
        echo "$POD_RESPONSE" | jq .
    else
        echo "✅ Deployed pod $i: $POD_ID"
    fi
    
    # Rate limit API calls
    sleep 2
done

echo ""
echo "🎉 Deployment complete!"
echo ""
echo "Next steps:"
echo "1. Wait 2-3 minutes for pods to start and connect to Tailscale"
echo "2. Check Tailscale admin console: https://login.tailscale.com/admin/machines"
echo "3. Verify workers appear with hostnames: rapid-gpu-worker-1, rapid-gpu-worker-2, etc."
echo "4. Test orchestrator connection: curl http://orchestrator.tail-scale.ts.net:8001/health"
echo ""
echo "Monitor pods: https://runpod.io/console/pods"
