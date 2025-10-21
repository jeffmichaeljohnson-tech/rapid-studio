from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import redis
import json
import asyncio
from typing import List, Dict, Optional
import httpx
import os
from datetime import datetime

app = FastAPI(title="Rapid Studio Orchestrator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis connection
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "redis"),
    port=6379,
    decode_responses=True
)

# GPU worker pool - will be populated from environment or Redis
GPU_WORKERS = os.getenv("GPU_WORKERS", "").split(",") if os.getenv("GPU_WORKERS") else []

# For development: use placeholder images until GPU workers are deployed
USE_PLACEHOLDER = len(GPU_WORKERS) == 0

class ImageRequest:
    def __init__(self, prompt: str, count: int, tier: str, user_id: str):
        self.prompt = prompt
        self.count = count
        self.tier = tier
        self.user_id = user_id

@app.get("/")
async def root():
    return {
        "message": "Rapid Studio Orchestrator",
        "status": "running",
        "gpu_workers": len(GPU_WORKERS),
        "mode": "placeholder" if USE_PLACEHOLDER else "gpu"
    }

@app.get("/health")
async def health():
    try:
        redis_client.ping()
        redis_status = "connected"
    except:
        redis_status = "disconnected"
    
    return {
        "status": "healthy",
        "redis": redis_status,
        "gpu_workers": len(GPU_WORKERS),
        "mode": "placeholder" if USE_PLACEHOLDER else "gpu"
    }

async def generate_with_gpu(prompt: str, worker_url: str, count: int = 1) -> List[Dict]:
    """Generate images using real GPU worker"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            if count == 1:
                # Single image generation
                response = await client.post(
                    f"{worker_url}/generate",
                    json={
                        "prompt": prompt,
                        "num_inference_steps": 1,
                        "guidance_scale": 0.0,
                        "width": 1024,
                        "height": 1024
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                return [{
                    "image_base64": data["image_base64"],
                    "prompt": prompt,
                    "generation_time": data["generation_time"]
                }]
            else:
                # Bulk generation
                prompts = [prompt] * count
                response = await client.post(
                    f"{worker_url}/generate/bulk",
                    json={
                        "prompts": prompts,
                        "num_inference_steps": 1,
                        "guidance_scale": 0.0,
                        "width": 1024,
                        "height": 1024
                    }
                )
                response.raise_for_status()
                data = response.json()
                return data["images"]
                
    except Exception as e:
        print(f"GPU generation failed: {e}")
        return []

@app.get("/images/universal")
async def get_universal_images(count: int = 25):
    """Tier 1: Universal base images"""
    
    if USE_PLACEHOLDER:
        # Development mode: use placeholder images
        images = []
        for i in range(count):
            images.append({
                "id": f"universal_{i}_{datetime.now().timestamp()}",
                "url": f"https://picsum.photos/1024/1024?random={i}",
                "tier": "universal",
                "prompt": "high quality professional photography",
                "mode": "placeholder"
            })
        return {"images": images, "tier": "universal", "mode": "placeholder"}
    
    # Production mode: use GPU workers
    images = []
    prompts = [
        "professional product photography on white background",
        "minimalist design aesthetic clean lines",
        "vibrant colorful abstract composition",
        "modern architecture sleek design",
        "natural lighting lifestyle photography"
    ]
    
    # Distribute work across GPU workers
    images_per_worker = count // len(GPU_WORKERS) if GPU_WORKERS else count
    tasks = []
    
    for i, worker_url in enumerate(GPU_WORKERS):
        prompt = prompts[i % len(prompts)]
        tasks.append(generate_with_gpu(prompt, worker_url, images_per_worker))
    
    # Gather results from all workers
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    for result in results:
        if isinstance(result, list):
            for img_data in result:
                images.append({
                    "id": f"universal_{len(images)}_{datetime.now().timestamp()}",
                    "url": f"data:image/png;base64,{img_data['image_base64']}",
                    "tier": "universal",
                    "prompt": img_data["prompt"],
                    "generation_time": img_data.get("generation_time"),
                    "mode": "gpu"
                })
    
    return {"images": images, "tier": "universal", "mode": "gpu", "count": len(images)}

@app.get("/images/demographic")
async def get_demographic_images(age: str = "25-34", location: str = "US", count: int = 25):
    """Tier 2: Demographic clustering"""
    
    if USE_PLACEHOLDER:
        images = []
        for i in range(count):
            images.append({
                "id": f"demo_{age}_{location}_{i}",
                "url": f"https://picsum.photos/1024/1024?random={100+i}",
                "tier": "demographic",
                "prompt": f"content for {age} year olds in {location}",
                "mode": "placeholder"
            })
        return {"images": images, "tier": "demographic", "mode": "placeholder"}
    
    # TODO: Implement demographic-specific generation
    return {"images": [], "tier": "demographic", "mode": "gpu", "note": "Not yet implemented"}

@app.post("/images/personal")
async def get_personal_images(request: Dict):
    """Tier 3: Personal model"""
    count = request.get("count", 25)
    user_prefs = request.get("user_preferences", "default")
    
    if USE_PLACEHOLDER:
        images = []
        for i in range(count):
            images.append({
                "id": f"personal_{user_prefs}_{i}",
                "url": f"https://picsum.photos/1024/1024?random={200+i}",
                "tier": "personal",
                "prompt": f"personalized for {user_prefs}",
                "mode": "placeholder"
            })
        return {"images": images, "tier": "personal", "mode": "placeholder"}
    
    # TODO: Implement personalized generation
    return {"images": [], "tier": "personal", "mode": "gpu", "note": "Not yet implemented"}

@app.post("/ratings")
async def submit_ratings(ratings: List[Dict]):
    """Receive batch of swipe ratings from mobile app"""
    try:
        # Store ratings in Redis for training
        for rating in ratings:
            rating_data = {
                "image_id": rating.get("imageId"),
                "direction": rating.get("direction"),
                "timestamp": rating.get("timestamp"),
                "velocity": rating.get("swipeVelocity"),
                "confidence": rating.get("confidence"),
                "tier": rating.get("tier")
            }
            
            # Add to user's rating stream
            user_id = rating.get("userId", "default")
            redis_client.xadd(
                f"ratings:{user_id}",
                rating_data,
                maxlen=1000  # Keep last 1000 ratings
            )
        
        print(f"Received {len(ratings)} ratings")
        return {"received": len(ratings), "status": "stored"}
        
    except Exception as e:
        print(f"Failed to store ratings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/jobs/bulk")
async def create_bulk_job(request: Dict):
    """Create bulk generation job for 100 images in 15 seconds"""
    count = request.get("count", 100)
    prompt = request.get("prompt", "professional photography")
    user_id = request.get("user_id", "default")
    
    job_id = f"bulk_{user_id}_{count}_{datetime.now().timestamp()}"
    
    # Store job in Redis
    job_data = {
        "id": job_id,
        "count": count,
        "prompt": prompt,
        "user_id": user_id,
        "status": "processing",
        "created_at": datetime.now().isoformat()
    }
    
    try:
        redis_client.hset(f"job:{job_id}", mapping=job_data)
        
        # Add to processing queue
        redis_client.xadd("jobs.in", {
            "job_id": job_id,
            "count": count,
            "prompt": prompt,
            "user_id": user_id
        })
        
        return {
            "job_id": job_id,
            "status": "queued",
            "estimated_completion": "10-15 seconds",
            "workers": len(GPU_WORKERS)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/report_validation")
async def report_validation(job_id: str, passed: int, total: int):
    """Report validation results from validators"""
    try:
        validation_data = {
            "job_id": job_id,
            "passed": passed,
            "total": total,
            "timestamp": datetime.now().isoformat()
        }
        redis_client.hset(f"validation:{job_id}", mapping=validation_data)
        return {"status": "reported", "job_id": job_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            await websocket.send_json({
                "type": "status",
                "message": "Connected to Rapid Studio",
                "timestamp": datetime.now().isoformat(),
                "workers": len(GPU_WORKERS),
                "mode": "placeholder" if USE_PLACEHOLDER else "gpu"
            })
            await asyncio.sleep(1)
    except:
        pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
