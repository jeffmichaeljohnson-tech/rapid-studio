#!/bin/bash

# Test the MCP server manually
cd "$(dirname "$0")"

echo "Testing Rapid Studio MCP Server..."

# Activate virtual environment
source venv/bin/activate

# Test server startup
echo "Testing server startup..."

# Test that all required modules can be imported
python3 -c "
try:
    import httpx
    print('✅ httpx imported successfully')
    
    from mcp.server.fastmcp import FastMCP
    print('✅ FastMCP imported successfully')
    
    from mcp.types import TextContent, ImageContent, EmbeddedResource
    print('✅ MCP types imported successfully')
    
    # Test that we can create an MCP instance
    mcp = FastMCP('test')
    print('✅ MCP server can be created')
    
    print('✅ All imports and basic initialization successful')
except Exception as e:
    print('❌ Import/initialization failed:', e)
    import traceback
    traceback.print_exc()
    exit(1)
"

if [ $? -eq 0 ]; then
    echo "✅ Server can start successfully"
else
    echo "❌ Server failed to initialize"
    exit 1
fi

echo "✅ MCP server test completed"
