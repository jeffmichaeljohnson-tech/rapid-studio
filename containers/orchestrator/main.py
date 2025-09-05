from fastapi import FastAPI
from pydantic import BaseModel
from starlette.responses import Response
import redis
import uuid
import json
import time

from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

app = FastAPI(title="Rapid Studio Orchestrator")

# Redis
r = redis.Redis(host="redis", port=6379, decode_responses=True)

# --- Prometheus Metrics ---
jobs_queued = Counter("jobs_queued_total", "Total jobs queued")
jobs_validated = Counter("jobs_validated_total", "Total jobs validated (lite/full)")
jobs_passed = Counter("jobs_passed_total", "Total tiles passed validation")
jobs_failed = Counter("jobs_failed_total", "Total tiles failed validation")
job_latency = Histogram("job_latency_seconds", "Job latency from queued -> strict validation")

# Track start times in Redis for latency measurement
# We store job_id -> start_time
JOB_START_KEY = "job_start_times"

# --- Models ---
class JobRequest(BaseModel):
    brand_id: str
    prompt: str
    tiles: int = 24

class Rating(BaseModel):
    job_id: str
    tile_id: str
    decision: str  # yes|no


# --- Routes ---
@app.post("/jobs")
def create_job(req: JobRequest):
    job_id = str(uuid.uuid4())
    job = {
        "job_id": job_id,
        "brand_id": req.brand_id,
        "prompt": req.prompt,
        "tiles": req.tiles,
    }

    # Push into Redis
    r.xadd("jobs.in", job)
    jobs_queued.inc()

    # Save start time for latency
    r.hset(JOB_START_KEY, job_id, time.time())

    return {"job_id": job_id, "status": "queued"}


@app.get("/status/{job_id}")
def job_status(job_id: str):
    # Look for final results in jobs.strict
    results = r.xrevrange("jobs.strict", count=50)
    for msg_id, data in results:
        if data.get("job_id") == job_id:
            return {
                "job_id": job_id,
                "status": "complete",
                "brand_id": data.get("brand_id"),
                "tiles": json.loads(data.get("tiles", "[]")),
                "passed": int(data.get("passed", 0)),
                "total": int(data.get("total", 0)),
            }
    return {"job_id": job_id, "status": "pending"}


@app.post("/ratings")
def submit_rating(rating: Rating):
    r.xadd("ratings.in", rating.dict())
    return {"ok": True}


@app.post("/report_validation")
def report_validation(job_id: str, passed: int, total: int):
    # Increment validation counters
    jobs_validated.inc()
    jobs_passed.inc(passed)
    jobs_failed.inc(total - passed)

    # Latency measurement
    start = r.hget(JOB_START_KEY, job_id)
    if start:
        elapsed = time.time() - float(start)
        job_latency.observe(elapsed)
        r.hdel(JOB_START_KEY, job_id)

    return {"status": "recorded"}


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
