import redis
import time
import json
import uuid
import io
import requests

print("Runner-GPU starting...")

# Connect to Redis
r = redis.Redis(host="redis", port=6379, decode_responses=True)

ASSETS_API = "http://assets-api:8080/upload"  # internal docker network

while True:
    # Block until a job arrives
    jobs = r.xread({"jobs.in": "$"}, block=5000, count=1)
    if not jobs:
        continue

    for stream, messages in jobs:
        for msg_id, job_data in messages:
            print(f"Processing job {msg_id}: {job_data}")
            job_id = job_data.get("job_id", str(uuid.uuid4()))
            brand_id = job_data.get("brand_id", "unknown")
            tiles = int(job_data.get("tiles", 24))

            # Simulate generation time
            time.sleep(2)

            uploaded_urls = []
            for i in range(tiles):
                # Instead of generating real images, we make fake binary content for now
                fake_png = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"  # PNG header
                files = {"file": (f"tile_{i}.png", io.BytesIO(fake_png), "image/png")}
                params = {"job_id": job_id, "brand_id": brand_id}

                try:
                    resp = requests.post(ASSETS_API, files=files, params=params)
                    resp.raise_for_status()
                    data = resp.json()
                    uploaded_urls.append(data["url"])
                except Exception as e:
                    print(f"Upload failed for tile {i}: {e}")

            r.xadd("jobs.out", {
                "job_id": job_id,
                "brand_id": brand_id,
                "tiles": json.dumps(uploaded_urls)
            })
            print(f"Job {job_id} complete, uploaded {len(uploaded_urls)} tiles")

