#!/bin/bash

# Rapid Studio MCP Server Startup Script
cd "$(dirname "$0")"

echo "Starting Rapid Studio MCP Server..."
echo "Project root: $RAPID_STUDIO_ROOT"

# Activate virtual environment
source venv/bin/activate

# Run the server
python3 rapid-studio-server.py
