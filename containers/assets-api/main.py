from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
import os
import uuid

app = FastAPI(title="Assets API")

# Directory inside container (mapped to host volume)
STORAGE_DIR = "/app/assets"
os.makedirs(STORAGE_DIR, exist_ok=True)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/upload")
async def upload_image(
    file: UploadFile = File(...),
    job_id: str = None,
    brand_id: str = None
):
    # Use UUID to avoid collisions
    tile_id = str(uuid.uuid4())
    ext = os.path.splitext(file.filename)[-1] or ".png"

    # Organize by brand/job
    folder = os.path.join(STORAGE_DIR, brand_id or "generic", job_id or "misc")
    os.makedirs(folder, exist_ok=True)

    path = os.path.join(folder, f"{tile_id}{ext}")
    with open(path, "wb") as f:
        f.write(await file.read())

    return {
        "tile_id": tile_id,
        "brand_id": brand_id,
        "job_id": job_id,
        "filename": f"{tile_id}{ext}",
        "url": f"/assets/{brand_id}/{job_id}/{tile_id}{ext}"
    }

@app.get("/assets/{brand_id}/{job_id}/{filename}")
def get_image(brand_id: str, job_id: str, filename: str):
    path = os.path.join(STORAGE_DIR, brand_id, job_id, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path)

@app.get("/assets/{brand_id}/{job_id}")
def list_images(brand_id: str, job_id: str):
    folder = os.path.join(STORAGE_DIR, brand_id, job_id)
    if not os.path.exists(folder):
        raise HTTPException(status_code=404, detail="Job folder not found")
    
    files = os.listdir(folder)
    urls = [f"/assets/{brand_id}/{job_id}/{filename}" for filename in files]
    
    return {
        "brand_id": brand_id,
        "job_id": job_id,
        "count": len(files),
        "files": files,
        "urls": urls
    }
