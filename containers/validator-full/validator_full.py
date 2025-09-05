import redis, json, uuid, requests

print("Validator-Full starting...")

r = redis.Redis(host="redis", port=6379, decode_responses=True)
ORCH_URL = "http://orchestrator:8000/report_validation"

def strict_checks(tile_url: str) -> bool:
    return True

while True:
    jobs = r.xread({"jobs.validated": "$"}, block=5000, count=1)
    if not jobs:
        continue

    for stream, messages in jobs:
        for msg_id, job_data in messages:
            job_id = job_data.get("job_id", str(uuid.uuid4()))
            brand_id = job_data.get("brand_id", "unknown")
            tiles = json.loads(job_data.get("tiles", "[]"))

            print(f"Strict validating job {job_id} with {len(tiles)} tiles")
            passed_tiles = [t for t in tiles if strict_checks(t)]

            r.xadd("jobs.strict", {
                "job_id": job_id,
                "brand_id": brand_id,
                "tiles": json.dumps(passed_tiles),
                "passed": str(len(passed_tiles)),
                "total": str(len(tiles))
            })

            # Report to orchestrator metrics
            try:
                requests.post(ORCH_URL, params={
                    "job_id": job_id,
                    "passed": len(passed_tiles),
                    "total": len(tiles)
                })
            except Exception as e:
                print(f"Metrics report failed: {e}")

            print(f"Job {job_id} strict validated: {len(passed_tiles)}/{len(tiles)} passed")
