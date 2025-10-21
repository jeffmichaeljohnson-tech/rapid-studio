#!/usr/bin/env python3
"""
Rapid Studio RunPod Setup Script
Run this in your RunPod Jupyter Lab to set up the GPU worker
"""

import subprocess
import sys
import os

def run_command(cmd, description):
    """Run a command and print the result"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} completed")
            if result.stdout:
                print(result.stdout)
        else:
            print(f"❌ {description} failed: {result.stderr}")
        return result.returncode == 0
    except Exception as e:
        print(f"❌ {description} failed: {e}")
        return False

def main():
    print("🚀 Setting up Rapid Studio GPU Worker on RunPod...")
    print("=" * 50)
    
    # Install Python dependencies
    deps = [
        "fastapi==0.104.1",
        "uvicorn[standard]==0.24.0", 
        "pillow==10.1.0",
        "diffusers==0.25.0",
        "transformers==4.36.0",
        "accelerate==0.25.0",
        "safetensors==0.4.1"
    ]
    
    for dep in deps:
        if not run_command(f"pip install {dep}", f"Installing {dep}"):
            print(f"⚠️  Failed to install {dep}, continuing...")
    
    # Install Tailscale
    print("\n🔗 Setting up Tailscale...")
    run_command("curl -fsSL https://tailscale.com/install.sh | sh", "Installing Tailscale")
    
    # Create the inference server file
    print("\n📝 Creating inference server...")
    
    inference_code = '''"""
SDXL-Turbo GPU Inference Server for Rapid Studio
Targets: <1.5s per image, 100 images in <15s with 8 GPUs
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import torch
from diffusers import AutoPipelineForText2Image
import io
import base64
from PIL import Image
import time
from typing import Optional, List
import os

app = FastAPI(title="Rapid Studio GPU Worker")

# Global pipeline - loaded once on startup
pipeline = None
device = "cuda" if torch.cuda.is_available() else "cpu"

class GenerationRequest(BaseModel):
    prompt: str
    negative_prompt: Optional[str] = "blurry, low quality, distorted"
    num_inference_steps: int = 1  # SDXL-Turbo optimized for 1-4 steps
    guidance_scale: float = 0.0  # Turbo doesn't need guidance
    width: int = 1024
    height: int = 1024
    seed: Optional[int] = None
    count: int = 1  # How many images to generate

class BulkGenerationRequest(BaseModel):
    prompts: List[str]
    negative_prompt: Optional[str] = "blurry, low quality, distorted"
    num_inference_steps: int = 1
    guidance_scale: float = 0.0
    width: int = 1024
    height: int = 1024

@app.on_event("startup")
async def load_model():
    """Load SDXL-Turbo model on startup - takes ~30 seconds"""
    global pipeline
    
    print("🚀 Loading SDXL-Turbo model...")
    start_time = time.time()
    
    try:
        pipeline = AutoPipelineForText2Image.from_pretrained(
            "stabilityai/sdxl-turbo",
            torch_dtype=torch.float16,
            variant="fp16",
            cache_dir=os.getenv("HF_HOME", "/workspace/.cache")
        )
        pipeline = pipeline.to(device)
        
        # Optimize for speed
        if device == "cuda":
            pipeline.enable_model_cpu_offload()
            
        load_time = time.time() - start_time
        print(f"✅ Model loaded in {load_time:.2f}s")
        print(f"💾 Device: {device}")
        print(f"🎯 Target: <1.5s per image")
        
        # Warm up the pipeline
        print("🔥 Warming up pipeline...")
        warmup_start = time.time()
        _ = pipeline(
            prompt="test",
            num_inference_steps=1,
            guidance_scale=0.0
        ).images[0]
        warmup_time = time.time() - warmup_start
        print(f"✅ Warmup complete in {warmup_time:.2f}s")
        
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        raise

@app.get("/")
async def root():
    return {
        "service": "Rapid Studio GPU Worker",
        "model": "SDXL-Turbo",
        "device": device,
        "status": "ready" if pipeline else "loading"
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy" if pipeline else "initializing",
        "device": device,
        "gpu_available": torch.cuda.is_available(),
        "memory_allocated": torch.cuda.memory_allocated() if torch.cuda.is_available() else 0
    }

@app.post("/generate")
async def generate_image(request: GenerationRequest):
    """Generate a single image - target <1.5s"""
    if not pipeline:
        raise HTTPException(status_code=503, detail="Model still loading")
    
    start_time = time.time()
    
    try:
        # Set seed if provided
        generator = None
        if request.seed:
            generator = torch.Generator(device=device).manual_seed(request.seed)
        
        # Generate image
        image = pipeline(
            prompt=request.prompt,
            negative_prompt=request.negative_prompt,
            num_inference_steps=request.num_inference_steps,
            guidance_scale=request.guidance_scale,
            width=request.width,
            height=request.height,
            generator=generator
        ).images[0]
        
        # Convert to base64
        buffered = io.BytesIO()
        image.save(buffered, format="PNG", optimize=True)
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        generation_time = time.time() - start_time
        
        return {
            "image_base64": img_str,
            "generation_time": f"{generation_time:.3f}s",
            "prompt": request.prompt,
            "width": request.width,
            "height": request.height
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

@app.post("/generate/bulk")
async def generate_bulk(request: BulkGenerationRequest):
    """Generate multiple images - target ~12-13 images in parallel per GPU"""
    if not pipeline:
        raise HTTPException(status_code=503, detail="Model still loading")
    
    start_time = time.time()
    results = []
    
    try:
        for i, prompt in enumerate(request.prompts):
            gen_start = time.time()
            
            image = pipeline(
                prompt=prompt,
                negative_prompt=request.negative_prompt,
                num_inference_steps=request.num_inference_steps,
                guidance_scale=request.guidance_scale,
                width=request.width,
                height=request.height
            ).images[0]
            
            # Convert to base64
            buffered = io.BytesIO()
            image.save(buffered, format="PNG", optimize=True)
            img_str = base64.b64encode(buffered.getvalue()).decode()
            
            gen_time = time.time() - gen_start
            
            results.append({
                "index": i,
                "image_base64": img_str,
                "prompt": prompt,
                "generation_time": f"{gen_time:.3f}s"
            })
            
            print(f"Generated image {i+1}/{len(request.prompts)} in {gen_time:.3f}s")
        
        total_time = time.time() - start_time
        
        return {
            "images": results,
            "total_images": len(results),
            "total_time": f"{total_time:.3f}s",
            "avg_time_per_image": f"{total_time/len(results):.3f}s"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bulk generation failed: {str(e)}")

@app.post("/generate/stream")
async def generate_stream(request: GenerationRequest):
    """Generate and return image as PNG stream"""
    if not pipeline:
        raise HTTPException(status_code=503, detail="Model still loading")
    
    try:
        generator = None
        if request.seed:
            generator = torch.Generator(device=device).manual_seed(request.seed)
        
        image = pipeline(
            prompt=request.prompt,
            negative_prompt=request.negative_prompt,
            num_inference_steps=request.num_inference_steps,
            guidance_scale=request.guidance_scale,
            width=request.width,
            height=request.height,
            generator=generator
        ).images[0]
        
        # Return as PNG stream
        buffered = io.BytesIO()
        image.save(buffered, format="PNG", optimize=True)
        buffered.seek(0)
        
        return StreamingResponse(buffered, media_type="image/png")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
'''
    
    with open("inference_server.py", "w") as f:
        f.write(inference_code)
    
    print("✅ Inference server code created")
    
    # Create startup script
    startup_script = '''#!/bin/bash
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
'''
    
    with open("start_worker.sh", "w") as f:
        f.write(startup_script)
    
    run_command("chmod +x start_worker.sh", "Making startup script executable")
    
    print("\n🎉 Setup complete!")
    print("=" * 50)
    print("Next steps:")
    print("1. Run: ./start_worker.sh")
    print("2. Or start manually: python3 -m uvicorn inference_server:app --host 0.0.0.0 --port 8000")
    print("3. Test: curl http://localhost:8000/health")
    print("4. Your worker will be available at: http://your-pod-ip:8000")

if __name__ == "__main__":
    main()
