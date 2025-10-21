"""
Rapid Studio Orchestrator
Routes generation jobs to GPU workers via Redis Streams
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import redis.asyncio as redis
import json
import uuid
import time

app = FastAPI(title="Rapid Studio Orchestrator")

# CORS for Expo mobile app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Lock down in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis connection
redis_client = None

@app.on_event("startup")
async def startup():
    global redis_client
    redis_client = await redis.from_url("redis://localhost:6379", decode_responses=True)

@app.on_event("shutdown")
async def shutdown():
    await redis_client.close()

# Request models
class GenerationRequest(BaseModel):
    prompt: str
    num_images: int = 4
    user_id: Optional[str] = None
    style_params: Optional[dict] = None

class RatingBatch(BaseModel):
    user_id: str
    ratings: List[dict]  # [{image_id, score, timestamp}, ...]

# Health check
@app.get("/health")
async def health():
    return {"status": "healthy", "service": "orchestrator"}

# Submit generation job
@app.post("/jobs")
async def create_job(request: GenerationRequest):
    job_id = str(uuid.uuid4())
    job_data = {
        "job_id": job_id,
        "prompt": request.prompt,
        "num_images": request.num_images,
        "user_id": request.user_id or "anonymous",
        "style_params": request.style_params or {},
        "status": "queued",
        "created_at": time.time()
    }
    
    # Push to Redis stream for GPU workers to consume
    await redis_client.xadd(
        "generation_queue",
        {"job": json.dumps(job_data)}
    )
    
    return {"job_id": job_id, "status": "queued"}

# Get job status
@app.get("/jobs/{job_id}")
async def get_job(job_id: str):
    # Check Redis for job status
    job_key = f"job:{job_id}"
    job_data = await redis_client.get(job_key)
    
    if not job_data:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return json.loads(job_data)

# Submit rating batch
@app.post("/ratings")
async def submit_ratings(batch: RatingBatch):
    # Store ratings for preference learning
    rating_key = f"ratings:{batch.user_id}:{int(time.time())}"
    await redis_client.set(
        rating_key,
        json.dumps(batch.ratings),
        ex=86400 * 30  # 30 days TTL
    )
    
    # Trigger preference update job (async background task)
    preference_job = {
        "user_id": batch.user_id,
        "rating_count": len(batch.ratings),
        "timestamp": time.time()
    }
    await redis_client.xadd(
        "preference_updates",
        {"update": json.dumps(preference_job)}
    )
    
    return {
        "status": "accepted",
        "ratings_processed": len(batch.ratings)
    }

# Get user's latest generated images
@app.get("/images/{user_id}")
async def get_user_images(user_id: str, limit: int = 25):
    # Fetch from Redis sorted set (sorted by timestamp)
    image_keys = await redis_client.zrevrange(
        f"user_images:{user_id}",
        0,
        limit - 1
    )
    
    images = []
    for key in image_keys:
        image_data = await redis_client.get(key)
        if image_data:
            images.append(json.loads(image_data))
    
    return {"images": images, "count": len(images)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
