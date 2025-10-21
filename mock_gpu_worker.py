#!/usr/bin/env python3
"""
Mock GPU Worker for Rapid Studio Testing
Simulates GPU worker responses for development
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import io
import base64
from PIL import Image, ImageDraw, ImageFont
import time
import random
from typing import Optional, List

app = FastAPI(title="Rapid Studio Mock GPU Worker")

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

@app.get("/")
async def root():
    return {
        "service": "Rapid Studio Mock GPU Worker",
        "model": "Mock-SDXL-Turbo",
        "device": "mock",
        "status": "ready"
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "device": "mock",
        "gpu_available": True,
        "memory_allocated": 8192
    }

def generate_mock_image(prompt: str, width: int = 1024, height: int = 1024) -> str:
    """Generate a mock image with the prompt text"""
    # Create a colorful mock image
    colors = [
        (255, 100, 100),  # Red
        (100, 255, 100),  # Green
        (100, 100, 255),  # Blue
        (255, 255, 100),  # Yellow
        (255, 100, 255),  # Magenta
        (100, 255, 255),  # Cyan
    ]
    
    # Create image with random background color
    bg_color = random.choice(colors)
    image = Image.new('RGB', (width, height), bg_color)
    draw = ImageDraw.Draw(image)
    
    # Add some geometric shapes
    for _ in range(5):
        x1 = random.randint(0, width//2)
        y1 = random.randint(0, height//2)
        x2 = random.randint(width//2, width)
        y2 = random.randint(height//2, height)
        color = random.choice(colors)
        draw.ellipse([x1, y1, x2, y2], fill=color)
    
    # Add prompt text
    try:
        font = ImageFont.load_default()
    except:
        font = None
    
    # Split prompt into lines
    words = prompt.split()
    lines = []
    current_line = ""
    for word in words:
        if len(current_line + " " + word) > 30:
            lines.append(current_line)
            current_line = word
        else:
            current_line += " " + word if current_line else word
    if current_line:
        lines.append(current_line)
    
    # Draw text
    y_offset = height // 2 - (len(lines) * 20) // 2
    for line in lines[:5]:  # Max 5 lines
        draw.text((50, y_offset), line, fill=(255, 255, 255), font=font)
        y_offset += 25
    
    # Convert to base64
    buffered = io.BytesIO()
    image.save(buffered, format="PNG", optimize=True)
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return img_str

@app.post("/generate")
async def generate_image(request: GenerationRequest):
    """Generate a mock image - simulates <1.5s generation"""
    start_time = time.time()
    
    # Simulate generation time
    time.sleep(0.5 + random.random() * 0.5)  # 0.5-1.0 seconds
    
    try:
        img_str = generate_mock_image(request.prompt, request.width, request.height)
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
    """Generate multiple mock images"""
    start_time = time.time()
    results = []
    
    for i, prompt in enumerate(request.prompts):
        gen_start = time.time()
        
        # Simulate generation time
        time.sleep(0.3 + random.random() * 0.4)  # 0.3-0.7 seconds per image
        
        img_str = generate_mock_image(prompt, request.width, request.height)
        gen_time = time.time() - gen_start
        
        results.append({
            "index": i,
            "image_base64": img_str,
            "prompt": prompt,
            "generation_time": f"{gen_time:.3f}s"
        })
    
    total_time = time.time() - start_time
    
    return {
        "images": results,
        "total_images": len(results),
        "total_time": f"{total_time:.3f}s",
        "avg_time_per_image": f"{total_time/len(results):.3f}s"
    }

@app.post("/generate/stream")
async def generate_stream(request: GenerationRequest):
    """Generate and return image as PNG stream"""
    try:
        img_str = generate_mock_image(request.prompt, request.width, request.height)
        img_bytes = base64.b64decode(img_str)
        
        return StreamingResponse(io.BytesIO(img_bytes), media_type="image/png")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8890)
