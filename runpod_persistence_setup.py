#!/usr/bin/env python3
"""
RunPod Data Persistence Setup for Rapid Studio
Ensures GPU worker code and model cache survive pod restarts
"""

import os
import subprocess
import json
from pathlib import Path

def setup_persistence():
    """Set up RunPod data persistence for Rapid Studio"""
    
    print("🚀 Setting up RunPod data persistence...")
    
    # 1. Create persistent directories
    persistent_dirs = [
        "/workspace/rapid-studio",
        "/workspace/rapid-studio/models", 
        "/workspace/rapid-studio/cache",
        "/workspace/rapid-studio/logs",
        "/workspace/rapid-studio/data"
    ]
    
    for dir_path in persistent_dirs:
        os.makedirs(dir_path, exist_ok=True)
        print(f"✅ Created: {dir_path}")
    
    # 2. Create startup script for automatic worker launch
    startup_script = """#!/bin/bash
# Rapid Studio Auto-Startup Script
# This runs every time the pod starts

echo "🚀 Starting Rapid Studio GPU Worker..."

# Navigate to workspace
cd /workspace

# Activate any existing virtual environment or create one
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

# Install dependencies if not already installed
if [ ! -f "requirements_installed.flag" ]; then
    echo "📦 Installing dependencies..."
    pip install fastapi uvicorn diffusers transformers torch pillow
    touch requirements_installed.flag
fi

# Start the GPU worker
echo "🎯 Starting GPU inference server..."
python3 /workspace/rapid-studio/inference_server.py
"""
    
    with open("/workspace/start_rapid_studio.sh", "w") as f:
        f.write(startup_script)
    
    os.chmod("/workspace/start_rapid_studio.sh", 0o755)
    print("✅ Created startup script: /workspace/start_rapid_studio.sh")
    
    # 3. Create model cache configuration
    cache_config = {
        "model_cache_dir": "/workspace/rapid-studio/models",
        "hf_cache_dir": "/workspace/rapid-studio/cache",
        "persistent_data": True,
        "auto_download": True
    }
    
    with open("/workspace/rapid-studio/cache_config.json", "w") as f:
        json.dump(cache_config, f, indent=2)
    
    print("✅ Created cache configuration")
    
    # 4. Create environment setup
    env_setup = """# Rapid Studio Environment Variables
export HF_HOME=/workspace/rapid-studio/cache
export TRANSFORMERS_CACHE=/workspace/rapid-studio/cache
export HF_DATASETS_CACHE=/workspace/rapid-studio/cache
export WORKSPACE_DIR=/workspace/rapid-studio
export MODEL_CACHE_DIR=/workspace/rapid-studio/models
"""
    
    with open("/workspace/rapid-studio/.env", "w") as f:
        f.write(env_setup)
    
    print("✅ Created environment configuration")
    
    # 5. Create backup script
    backup_script = """#!/bin/bash
# Backup Rapid Studio data to RunPod network storage

echo "💾 Backing up Rapid Studio data..."

# Create backup directory with timestamp
BACKUP_DIR="/workspace/backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup critical files
cp -r /workspace/rapid-studio "$BACKUP_DIR/"
cp /workspace/start_rapid_studio.sh "$BACKUP_DIR/"

echo "✅ Backup created: $BACKUP_DIR"
"""
    
    with open("/workspace/backup_rapid_studio.sh", "w") as f:
        f.write(backup_script)
    
    os.chmod("/workspace/backup_rapid_studio.sh", 0o755)
    print("✅ Created backup script")
    
    print("\n🎯 Persistence setup complete!")
    print("\n📋 Next steps:")
    print("1. Copy your inference_server.py to /workspace/rapid-studio/")
    print("2. Run: chmod +x /workspace/start_rapid_studio.sh")
    print("3. Set this as your RunPod startup command:")
    print("   /workspace/start_rapid_studio.sh")
    print("\n💡 Your data will now persist between pod restarts!")

if __name__ == "__main__":
    setup_persistence()
