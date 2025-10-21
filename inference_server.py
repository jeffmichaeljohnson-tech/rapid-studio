"""
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
