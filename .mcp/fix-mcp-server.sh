#!/bin/bash

echo "🔧 Fixing Rapid Studio MCP Server"
echo "================================="

cd /Users/computer/rapid-studio-1/.mcp

# Remove old virtual environment
if [ -d "venv" ]; then
    rm -rf venv
    echo "Removed old virtual environment"
fi

# Create new virtual environment
python3 -m venv venv
source venv/bin/activate

# Install correct MCP dependencies
echo "Installing MCP dependencies..."
pip install --upgrade pip

# Install specific working versions
pip install mcp>=0.1.0
pip install httpx>=0.25.0
pip install requests>=2.31.0

echo "✅ Dependencies installed"

# Test the server
echo "Testing MCP server..."
timeout 5 python3 rapid-studio-server.py &
SERVER_PID=$!

sleep 2

if ps -p $SERVER_PID > /dev/null 2>&1; then
    echo "✅ Server started successfully"
    kill $SERVER_PID 2>/dev/null
else
    echo "❌ Server failed to start, checking errors..."
    python3 rapid-studio-server.py
fi

echo "🎉 MCP server fix completed!"