#!/bin/bash
# Setup RunPod Persistence for Rapid Studio
# Run this script on your RunPod pod to enable data persistence

echo "🚀 Setting up RunPod persistence for Rapid Studio..."

# 1. Create persistent directories
echo "📁 Creating persistent directories..."
mkdir -p /workspace/rapid-studio/{models,cache,logs,data}
mkdir -p /workspace/backups

# 2. Set up environment variables
echo "🔧 Setting up environment variables..."
cat > /workspace/rapid-studio/.env << 'EOF'
# Rapid Studio Environment Variables
export HF_HOME=/workspace/rapid-studio/cache
export TRANSFORMERS_CACHE=/workspace/rapid-studio/cache
export HF_DATASETS_CACHE=/workspace/rapid-studio/cache
export WORKSPACE_DIR=/workspace/rapid-studio
export MODEL_CACHE_DIR=/workspace/rapid-studio/models
EOF

# 3. Create startup script
echo "📝 Creating startup script..."
cat > /workspace/start_rapid_studio.sh << 'EOF'
#!/bin/bash
# Rapid Studio Auto-Startup Script
# This runs every time the pod starts

echo "🚀 Starting Rapid Studio GPU Worker..."

# Navigate to workspace
cd /workspace

# Source environment variables
source /workspace/rapid-studio/.env

# Activate virtual environment or create one
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

# Install dependencies if not already installed
if [ ! -f "requirements_installed.flag" ]; then
    echo "📦 Installing dependencies..."
    pip install fastapi uvicorn diffusers==0.25.0 transformers==4.36.0 huggingface_hub==0.20.3 torch pillow
    touch requirements_installed.flag
fi

# Start the persistent GPU worker
echo "🎯 Starting persistent GPU inference server..."
python3 /workspace/rapid-studio/persistent_inference_server.py
EOF

chmod +x /workspace/start_rapid_studio.sh

# 4. Create backup script
echo "💾 Creating backup script..."
cat > /workspace/backup_rapid_studio.sh << 'EOF'
#!/bin/bash
# Backup Rapid Studio data

echo "💾 Backing up Rapid Studio data..."

# Create backup directory with timestamp
BACKUP_DIR="/workspace/backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup critical files
cp -r /workspace/rapid-studio "$BACKUP_DIR/"
cp /workspace/start_rapid_studio.sh "$BACKUP_DIR/"

echo "✅ Backup created: $BACKUP_DIR"
EOF

chmod +x /workspace/backup_rapid_studio.sh

# 5. Create restore script
echo "🔄 Creating restore script..."
cat > /workspace/restore_rapid_studio.sh << 'EOF'
#!/bin/bash
# Restore Rapid Studio from backup

if [ -z "$1" ]; then
    echo "Usage: $0 <backup_directory>"
    echo "Available backups:"
    ls -la /workspace/backups/
    exit 1
fi

BACKUP_DIR="$1"

if [ ! -d "$BACKUP_DIR" ]; then
    echo "❌ Backup directory not found: $BACKUP_DIR"
    exit 1
fi

echo "🔄 Restoring from: $BACKUP_DIR"

# Restore rapid-studio directory
cp -r "$BACKUP_DIR/rapid-studio" /workspace/

# Restore startup script
cp "$BACKUP_DIR/start_rapid_studio.sh" /workspace/

echo "✅ Restore complete!"
EOF

chmod +x /workspace/restore_rapid_studio.sh

# 6. Create monitoring script
echo "📊 Creating monitoring script..."
cat > /workspace/monitor_rapid_studio.sh << 'EOF'
#!/bin/bash
# Monitor Rapid Studio status

echo "📊 Rapid Studio Status Monitor"
echo "================================"

# Check if worker is running
if pgrep -f "persistent_inference_server.py" > /dev/null; then
    echo "✅ GPU Worker: Running"
else
    echo "❌ GPU Worker: Not running"
fi

# Check storage usage
echo ""
echo "💾 Storage Usage:"
echo "Workspace: $(du -sh /workspace/rapid-studio 2>/dev/null | cut -f1)"
echo "Models: $(du -sh /workspace/rapid-studio/models 2>/dev/null | cut -f1)"
echo "Cache: $(du -sh /workspace/rapid-studio/cache 2>/dev/null | cut -f1)"
echo "Logs: $(du -sh /workspace/rapid-studio/logs 2>/dev/null | cut -f1)"

# Check recent logs
echo ""
echo "📝 Recent Logs:"
tail -5 /workspace/rapid-studio/logs/worker.log 2>/dev/null || echo "No logs found"

# Check GPU status
echo ""
echo "🎯 GPU Status:"
nvidia-smi --query-gpu=name,memory.used,memory.total --format=csv,noheader,nounits 2>/dev/null || echo "GPU not available"
EOF

chmod +x /workspace/monitor_rapid_studio.sh

echo ""
echo "🎉 RunPod persistence setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Copy persistent_inference_server.py to /workspace/rapid-studio/"
echo "2. Set RunPod startup command to: /workspace/start_rapid_studio.sh"
echo "3. Your data will now persist between pod restarts!"
echo ""
echo "🔧 Available commands:"
echo "- /workspace/start_rapid_studio.sh    # Start the worker"
echo "- /workspace/backup_rapid_studio.sh   # Backup data"
echo "- /workspace/restore_rapid_studio.sh  # Restore from backup"
echo "- /workspace/monitor_rapid_studio.sh  # Check status"
