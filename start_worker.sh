#!/bin/bash
echo "🚀 Starting Rapid Studio GPU Worker..."

# Set environment variables
export TAILSCALE_AUTHKEY="tskey-auth-kKhEMoHqif11CNTRL-fWNSCj3DRwBepzWeehYQxBGpsRa44315"
export WORKER_ID=1
export ORCHESTRATOR_URL="http://100.103.213.111:8000"

# Start Tailscale
echo "🔗 Starting Tailscale..."
tailscale up --authkey=$TAILSCALE_AUTHKEY --hostname=rapid-gpu-worker-$WORKER_ID

# Start the inference server
echo "🎯 Starting inference server on port 8000..."
python3 -m uvicorn inference_server:app --host 0.0.0.0 --port 8000 --workers 1
