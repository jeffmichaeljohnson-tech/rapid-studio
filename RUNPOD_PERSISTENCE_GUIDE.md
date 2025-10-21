# RunPod Data Persistence Guide for Rapid Studio

## 🎯 **Problem Solved**
RunPod pods are ephemeral by default. When you stop/start a pod, all data is lost. This guide ensures your GPU worker code, models, and cache persist between sessions.

## 💾 **What Gets Persisted**

### **✅ Always Persisted (RunPod Network Storage)**
- `/workspace/` directory contents
- Model downloads and cache
- Code and configuration files
- Logs and generated data

### **❌ Lost on Pod Restart**
- Running processes
- Memory state
- Temporary files outside `/workspace/`

## 🚀 **Quick Setup (5 Minutes)**

### **Step 1: Run Setup Script on RunPod**
```bash
# On your RunPod pod, run:
curl -o setup_persistence.sh https://raw.githubusercontent.com/your-repo/rapid-studio/main/setup_runpod_persistence.sh
chmod +x setup_persistence.sh
./setup_persistence.sh
```

### **Step 2: Copy Your Code**
```bash
# Copy the persistent inference server
cp /path/to/persistent_inference_server.py /workspace/rapid-studio/
```

### **Step 3: Set RunPod Startup Command**
In your RunPod pod settings, set the startup command to:
```bash
/workspace/start_rapid_studio.sh
```

## 🔧 **Manual Setup (If Script Fails)**

### **1. Create Persistent Directories**
```bash
mkdir -p /workspace/rapid-studio/{models,cache,logs,data}
mkdir -p /workspace/backups
```

### **2. Set Environment Variables**
```bash
cat > /workspace/rapid-studio/.env << 'EOF'
export HF_HOME=/workspace/rapid-studio/cache
export TRANSFORMERS_CACHE=/workspace/rapid-studio/cache
export HF_DATASETS_CACHE=/workspace/rapid-studio/cache
export WORKSPACE_DIR=/workspace/rapid-studio
export MODEL_CACHE_DIR=/workspace/rapid-studio/models
EOF
```

### **3. Create Startup Script**
```bash
cat > /workspace/start_rapid_studio.sh << 'EOF'
#!/bin/bash
cd /workspace
source /workspace/rapid-studio/.env

# Create venv if needed
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

# Install dependencies if needed
if [ ! -f "requirements_installed.flag" ]; then
    pip install fastapi uvicorn diffusers==0.25.0 transformers==4.36.0 huggingface_hub==0.20.3 torch pillow
    touch requirements_installed.flag
fi

# Start worker
python3 /workspace/rapid-studio/persistent_inference_server.py
EOF

chmod +x /workspace/start_rapid_studio.sh
```

## 📊 **Monitoring & Management**

### **Check Status**
```bash
/workspace/monitor_rapid_studio.sh
```

### **Backup Data**
```bash
/workspace/backup_rapid_studio.sh
```

### **Restore from Backup**
```bash
/workspace/restore_rapid_studio.sh /workspace/backups/20250101_120000
```

### **View Logs**
```bash
tail -f /workspace/rapid-studio/logs/worker.log
```

## 🎯 **Key Benefits**

### **✅ Model Persistence**
- SDXL-Turbo model downloaded once
- Cached in `/workspace/rapid-studio/models/`
- No re-download on pod restart

### **✅ Code Persistence**
- Your inference server code saved
- Configuration files preserved
- Startup scripts maintained

### **✅ Cache Persistence**
- HuggingFace cache preserved
- Transformers cache maintained
- No re-download of dependencies

### **✅ Log Persistence**
- All generation logs saved
- Performance metrics tracked
- Debug information preserved

## 🔄 **Workflow with Persistence**

### **Starting a Session**
1. Start your RunPod pod
2. Pod automatically runs `/workspace/start_rapid_studio.sh`
3. Worker loads from persistent cache (fast startup)
4. Ready for image generation

### **Stopping a Session**
1. Stop the pod (data automatically saved)
2. All models, code, and cache preserved
3. Next startup will be fast (no re-download)

### **Updating Code**
1. Copy new code to `/workspace/rapid-studio/`
2. Restart pod to load new code
3. Models and cache remain unchanged

## 🚨 **Troubleshooting**

### **Worker Won't Start**
```bash
# Check logs
tail -20 /workspace/rapid-studio/logs/worker.log

# Check if dependencies installed
ls -la /workspace/requirements_installed.flag

# Reinstall if needed
rm /workspace/requirements_installed.flag
/workspace/start_rapid_studio.sh
```

### **Model Not Loading**
```bash
# Check if model exists
ls -la /workspace/rapid-studio/models/

# Check cache
ls -la /workspace/rapid-studio/cache/

# Force re-download
rm -rf /workspace/rapid-studio/models/sdxl-turbo
```

### **Storage Full**
```bash
# Check usage
du -sh /workspace/rapid-studio/*

# Clean old logs
find /workspace/rapid-studio/logs -name "*.log" -mtime +7 -delete

# Clean old backups
find /workspace/backups -mtime +30 -delete
```

## 📈 **Performance Benefits**

### **First Run**
- Downloads model (~2GB)
- Installs dependencies
- Takes 5-10 minutes

### **Subsequent Runs**
- Loads from cache
- No downloads needed
- Starts in 30-60 seconds

### **Storage Usage**
- Model: ~2GB
- Cache: ~1GB
- Logs: ~100MB
- Total: ~3-4GB

## 🎉 **Success Indicators**

✅ **Pod starts automatically**  
✅ **Worker loads in <60 seconds**  
✅ **No model re-download**  
✅ **Logs show "Model loaded from cache"**  
✅ **Generation works immediately**  

## 🔗 **Integration with Local Orchestrator**

Your local orchestrator can now reliably connect to the persistent RunPod worker:

```python
# In your orchestrator config
GPU_WORKERS = ["http://your-runpod-ip:8000"]
```

The worker will be available immediately after pod startup, with all models pre-loaded and ready for generation.

---

**🎯 Result: Zero data loss, fast startup, production-ready persistence!**
