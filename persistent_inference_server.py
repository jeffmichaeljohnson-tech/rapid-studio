"""
Persistent SDXL-Turbo GPU Inference Server for Rapid Studio
- Uses persistent storage for models and cache
- Survives pod restarts
- Auto-loads from cache on startup
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
import os
import json
from typing import Optional, List
from pathlib import Path

app = FastAPI(title="Rapid Studio Persistent GPU Worker")

# Persistent storage configuration
WORKSPACE_DIR = "/workspace/rapid-studio"
MODEL_CACHE_DIR = f"{WORKSPACE_DIR}/models"
HF_CACHE_DIR = f"{WORKSPACE_DIR}/cache"
LOGS_DIR = f"{WORKSPACE_DIR}/logs"

# Ensure directories exist
for dir_path in [WORKSPACE_DIR, MODEL_CACHE_DIR, HF_CACHE_DIR, LOGS_DIR]:
    Path(dir_path).mkdir(parents=True, exist_ok=True)

# Set environment variables for persistent caching
os.environ["HF_HOME"] = HF_CACHE_DIR
os.environ["TRANSFORMERS_CACHE"] = HF_CACHE_DIR
os.environ["HF_DATASETS_CACHE"] = HF_CACHE_DIR

# Global pipeline - loaded once on startup
pipeline = None
device = "cuda" if torch.cuda.is_available() else "cpu"

class GenerationRequest(BaseModel):
    prompt: str
    negative_prompt: Optional[str] = "blurry, low quality, distorted"
    num_inference_steps: int = 1
    guidance_scale: float = 0.0
    width: int = 1024
    height: int = 1024
    seed: Optional[int] = None
    count: int = 1

class BulkGenerationRequest(BaseModel):
    prompts: List[str]
    negative_prompt: Optional[str] = "blurry, low quality, distorted"
    num_inference_steps: int = 1
    guidance_scale: float = 0.0
    width: int = 1024
    height: int = 1024

def log_message(message: str):
    """Log message to persistent log file"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}\n"
    
    with open(f"{LOGS_DIR}/worker.log", "a") as f:
        f.write(log_entry)
    
    print(message)  # Also print to console

@app.on_event("startup")
async def load_model():
    """Load SDXL-Turbo model with persistent caching"""
    global pipeline
    
    log_message("🚀 Starting Rapid Studio Persistent GPU Worker...")
    log_message(f"💾 Using persistent storage: {WORKSPACE_DIR}")
    log_message(f"🎯 Model cache: {MODEL_CACHE_DIR}")
    log_message(f"📦 HF cache: {HF_CACHE_DIR}")
    
    start_time = time.time()
    
    try:
        # Check if model is already cached
        model_path = f"{MODEL_CACHE_DIR}/sdxl-turbo"
        if os.path.exists(model_path):
            log_message("📦 Loading model from persistent cache...")
            pipeline = AutoPipelineForText2Image.from_pretrained(
                model_path,
                torch_dtype=torch.float16,
                variant="fp16"
            )
        else:
            log_message("⬇️ Downloading model (first time only)...")
            pipeline = AutoPipelineForText2Image.from_pretrained(
                "stabilityai/sdxl-turbo",
                torch_dtype=torch.float16,
                variant="fp16",
                cache_dir=HF_CACHE_DIR
            )
            
            # Save model to persistent storage
            log_message("💾 Saving model to persistent storage...")
            pipeline.save_pretrained(model_path)
        
        pipeline = pipeline.to(device)
        
        # Optimize for speed
        if device == "cuda":
            pipeline.enable_model_cpu_offload()
        
        load_time = time.time() - start_time
        log_message(f"✅ Model loaded in {load_time:.2f}s")
        log_message(f"💾 Device: {device}")
        log_message(f"🎯 Target: <1.5s per image")
        
        # Warm up the pipeline
        log_message("🔥 Warming up pipeline...")
        warmup_start = time.time()
        _ = pipeline(
            prompt="test",
            num_inference_steps=1,
            guidance_scale=0.0
        ).images[0]
        warmup_time = time.time() - warmup_start
        log_message(f"✅ Warmup complete in {warmup_time:.2f}s")
        
        # Save startup info
        startup_info = {
            "startup_time": time.time(),
            "load_time": load_time,
            "warmup_time": warmup_time,
            "device": device,
            "model_path": model_path,
            "cache_dirs": {
                "workspace": WORKSPACE_DIR,
                "models": MODEL_CACHE_DIR,
                "hf_cache": HF_CACHE_DIR,
                "logs": LOGS_DIR
            }
        }
        
        with open(f"{WORKSPACE_DIR}/startup_info.json", "w") as f:
            json.dump(startup_info, f, indent=2)
        
        log_message("🎉 Persistent GPU worker ready!")
        
    except Exception as e:
        log_message(f"❌ Failed to load model: {e}")
        raise

@app.get("/")
async def root():
    return {
        "service": "Rapid Studio Persistent GPU Worker",
        "model": "SDXL-Turbo",
        "device": device,
        "status": "ready" if pipeline else "loading",
        "persistent_storage": {
            "workspace": WORKSPACE_DIR,
            "models": MODEL_CACHE_DIR,
            "cache": HF_CACHE_DIR,
            "logs": LOGS_DIR
        }
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy" if pipeline else "initializing",
        "device": device,
        "gpu_available": torch.cuda.is_available(),
        "memory_allocated": torch.cuda.memory_allocated() if torch.cuda.is_available() else 0,
        "persistent_storage": {
            "workspace_exists": os.path.exists(WORKSPACE_DIR),
            "model_cache_exists": os.path.exists(MODEL_CACHE_DIR),
            "hf_cache_exists": os.path.exists(HF_CACHE_DIR)
        }
    }

@app.get("/storage/status")
async def storage_status():
    """Check persistent storage status"""
    status = {
        "workspace": {
            "path": WORKSPACE_DIR,
            "exists": os.path.exists(WORKSPACE_DIR),
            "size": sum(os.path.getsize(os.path.join(dirpath, filename))
                       for dirpath, dirnames, filenames in os.walk(WORKSPACE_DIR)
                       for filename in filenames) if os.path.exists(WORKSPACE_DIR) else 0
        },
        "model_cache": {
            "path": MODEL_CACHE_DIR,
            "exists": os.path.exists(MODEL_CACHE_DIR),
            "size": sum(os.path.getsize(os.path.join(dirpath, filename))
                       for dirpath, dirnames, filenames in os.walk(MODEL_CACHE_DIR)
                       for filename in filenames) if os.path.exists(MODEL_CACHE_DIR) else 0
        },
        "hf_cache": {
            "path": HF_CACHE_DIR,
            "exists": os.path.exists(HF_CACHE_DIR),
            "size": sum(os.path.getsize(os.path.join(dirpath, filename))
                       for dirpath, dirnames, filenames in os.walk(HF_CACHE_DIR)
                       for filename in filenames) if os.path.exists(HF_CACHE_DIR) else 0
        }
    }
    
    return status

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
        log_message(f"🎨 Generated image in {generation_time:.3f}s")
        
        return {
            "image_base64": img_str,
            "generation_time": f"{generation_time:.3f}s",
            "prompt": request.prompt,
            "width": request.width,
            "height": request.height
        }
        
    except Exception as e:
        log_message(f"❌ Generation failed: {str(e)}")
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
            
            log_message(f"🎨 Generated image {i+1}/{len(request.prompts)} in {gen_time:.3f}s")
        
        total_time = time.time() - start_time
        log_message(f"🎉 Bulk generation complete: {len(results)} images in {total_time:.3f}s")
        
        return {
            "images": results,
            "total_images": len(results),
            "total_time": f"{total_time:.3f}s",
            "avg_time_per_image": f"{total_time/len(results):.3f}s"
        }
        
    except Exception as e:
        log_message(f"❌ Bulk generation failed: {str(e)}")
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
        log_message(f"❌ Stream generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    log_message("🚀 Starting persistent inference server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
