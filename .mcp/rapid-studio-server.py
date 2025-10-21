#!/usr/bin/env python3
"""
Rapid Studio MCP Server
Complete development automation server for the world's fastest creative AI platform
"""

import asyncio
import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
import httpx
from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent, ImageContent, EmbeddedResource

# Initialize FastMCP server
mcp = FastMCP("rapid-studio-dev")

# Configuration
RAPID_STUDIO_ROOT = Path(os.getenv("RAPID_STUDIO_ROOT", "/Users/computer/rapid-studio-1"))
RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY", "rpa_1NNFJ0DJ15M6TSCW3D00FDO0QKS710LG0UKRSQ801rs5wv")
TAILSCALE_NETWORK = os.getenv("TAILSCALE_NETWORK", "100.73.118.34")

# Performance targets
TARGET_FIRST_TILE_MS = 800
TARGET_FULL_GRID_MS = 10000
TARGET_IMAGES_COUNT = 100

@mcp.tool()
def rapid_read_file(filepath: str) -> str:
    """
    Read any file in the Rapid Studio project
    
    Args:
        filepath: Path relative to project root or absolute path
    """
    try:
        if not os.path.isabs(filepath):
            filepath = RAPID_STUDIO_ROOT / filepath
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return f"File: {filepath}\nSize: {len(content)} characters\n\n{content}"
    except Exception as e:
        return f"Error reading file {filepath}: {e}"

@mcp.tool()
def rapid_write_file(filepath: str, content: str, create_dirs: bool = True) -> str:
    """
    Write content to any file in the Rapid Studio project
    
    Args:
        filepath: Path relative to project root or absolute path
        content: Content to write to the file
        create_dirs: Whether to create parent directories if they don't exist
    """
    try:
        if not os.path.isabs(filepath):
            filepath = RAPID_STUDIO_ROOT / filepath
        
        if create_dirs:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return f"Successfully wrote {len(content)} characters to {filepath}"
    except Exception as e:
        return f"Error writing file {filepath}: {e}"

@mcp.tool()
def rapid_list_directory(dirpath: str = ".") -> str:
    """
    List contents of a directory in the Rapid Studio project
    
    Args:
        dirpath: Directory path relative to project root
    """
    try:
        if not os.path.isabs(dirpath):
            dirpath = RAPID_STUDIO_ROOT / dirpath
        
        items = []
        for item in sorted(os.listdir(dirpath)):
            item_path = os.path.join(dirpath, item)
            if os.path.isdir(item_path):
                items.append(f"📁 {item}/")
            else:
                size = os.path.getsize(item_path)
                items.append(f"📄 {item} ({size} bytes)")
        
        return f"Directory: {dirpath}\n\n" + "\n".join(items)
    except Exception as e:
        return f"Error listing directory {dirpath}: {e}"

@mcp.tool()
def rapid_execute_script(script_name: str, args: List[str] = None) -> str:
    """
    Execute a Rapid Studio script with arguments
    
    Args:
        script_name: Name of script in scripts/ directory (e.g., 'deploy-runpod.sh')
        args: Optional arguments to pass to the script
    """
    try:
        script_path = RAPID_STUDIO_ROOT / "scripts" / script_name
        if not script_path.exists():
            return f"Script not found: {script_path}"
        
        cmd = [str(script_path)]
        if args:
            cmd.extend(args)
        
        # Make script executable if not already
        os.chmod(script_path, 0o755)
        
        result = subprocess.run(
            cmd,
            cwd=RAPID_STUDIO_ROOT,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        output = f"Script: {script_name}\nExit code: {result.returncode}\n"
        output += f"\nSTDOUT:\n{result.stdout}"
        if result.stderr:
            output += f"\nSTDERR:\n{result.stderr}"
        
        return output
    except subprocess.TimeoutExpired:
        return f"Script {script_name} timed out after 5 minutes"
    except Exception as e:
        return f"Error executing script {script_name}: {e}"

@mcp.tool()
async def rapid_deploy_gpu_fleet(gpu_count: int = 8, gpu_type: str = "RTX 4000 Ada") -> str:
    """
    Deploy Runpod GPU fleet for Rapid Studio image generation
    
    Args:
        gpu_count: Number of GPU instances to deploy (default: 8)
        gpu_type: Type of GPU to use (default: RTX 4000 Ada)
    """
    try:
        headers = {
            "Authorization": f"Bearer {RUNPOD_API_KEY}",
            "Content-Type": "application/json"
        }
        
        deployed_pods = []
        
        async with httpx.AsyncClient() as client:
            for i in range(gpu_count):
                pod_name = f"rapid-studio-gpu-{i+1:02d}"
                
                mutation = f"""
                mutation {{
                    podRentInterruptable(input: {{
                        name: "{pod_name}",
                        imageName: "runpod/pytorch:2.0.1-py3.11-cuda11.8.0-devel-ubuntu22.04",
                        gpuTypeId: "NVIDIA {gpu_type}",
                        cloudType: COMMUNITY,
                        supportPublicIp: true,
                        startSsh: true,
                        volumeInGb: 50,
                        containerDiskInGb: 25,
                        minVcpuCount: 8,
                        minMemoryInGb: 32,
                        gpuCount: 1,
                        volumeMountPath: "/workspace",
                        ports: "8000/http,22/tcp",
                        env: [
                            {{key: "PYTHONPATH", value: "/workspace"}},
                            {{key: "HF_HOME", value: "/workspace/.cache"}},
                            {{key: "TORCH_HOME", value: "/workspace/.cache"}}
                        ]
                    }}) {{
                        id
                        imageName
                        machineId
                    }}
                }}
                """
                
                response = await client.post(
                    "https://api.runpod.ai/graphql",
                    headers=headers,
                    json={"query": mutation}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if "errors" not in result and result.get("data", {}).get("podRentInterruptable"):
                        pod_data = result["data"]["podRentInterruptable"]
                        deployed_pods.append({
                            "name": pod_name,
                            "id": pod_data["id"],
                            "status": "deploying"
                        })
                    else:
                        return f"Error deploying {pod_name}: {result.get('errors', 'Unknown error')}"
                
                # Rate limiting
                await asyncio.sleep(2)
        
        # Save deployment info
        deployment_file = RAPID_STUDIO_ROOT / ".rapid-studio" / "gpu-deployment.json"
        deployment_file.parent.mkdir(exist_ok=True)
        
        deployment_data = {
            "timestamp": time.time(),
            "pods": deployed_pods,
            "target_performance": "100 images in 10 seconds",
            "estimated_cost_per_hour": len(deployed_pods) * 0.22
        }
        
        with open(deployment_file, 'w') as f:
            json.dump(deployment_data, f, indent=2)
        
        return f"Successfully deployed {len(deployed_pods)} GPU instances!\nPods: {[p['name'] for p in deployed_pods]}\nEstimated cost: ${deployment_data['estimated_cost_per_hour']:.2f}/hour\nDeployment saved to: {deployment_file}"
        
    except Exception as e:
        return f"Error deploying GPU fleet: {e}"

@mcp.tool()
def rapid_monitor_system() -> str:
    """
    Get real-time status of all Rapid Studio services
    """
    try:
        status = {
            "timestamp": time.time(),
            "services": {},
            "performance": {},
            "deployment": {}
        }
        
        # Check service status
        services_to_check = [
            ("orchestrator", f"http://{TAILSCALE_NETWORK}:8000/health"),
            ("redis", f"http://{TAILSCALE_NETWORK}:6379"),
            ("grafana", f"http://{TAILSCALE_NETWORK}:3000"),
        ]
        
        for service_name, url in services_to_check:
            try:
                import requests
                response = requests.get(url, timeout=5)
                status["services"][service_name] = {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "response_time": response.elapsed.total_seconds()
                }
            except:
                status["services"][service_name] = {"status": "unreachable"}
        
        # Check GPU deployment status
        deployment_file = RAPID_STUDIO_ROOT / ".rapid-studio" / "gpu-deployment.json"
        if deployment_file.exists():
            with open(deployment_file, 'r') as f:
                deployment_data = json.load(f)
                status["deployment"] = {
                    "gpu_count": len(deployment_data.get("pods", [])),
                    "cost_per_hour": deployment_data.get("estimated_cost_per_hour", 0),
                    "deployed_at": deployment_data.get("timestamp", 0)
                }
        
        # Get latest performance test results
        results_dir = RAPID_STUDIO_ROOT / ".rapid-studio"
        if results_dir.exists():
            perf_files = list(results_dir.glob("performance_*.json"))
            if perf_files:
                latest_perf = max(perf_files, key=lambda x: x.stat().st_mtime)
                with open(latest_perf, 'r') as f:
                    status["performance"] = json.load(f)
        
        return json.dumps(status, indent=2)
        
    except Exception as e:
        return f"Error monitoring system: {e}"

if __name__ == "__main__":
    # Run the MCP server
    mcp.run()

