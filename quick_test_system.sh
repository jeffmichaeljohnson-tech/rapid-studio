#!/bin/bash
# Quick Test System - Verify GitHub Integration Works
# Run this to test the complete system

echo "🧪 TESTING GITHUB-INTEGRATED SHARED CONTEXT SYSTEM"
echo "================================================="

# Test 1: Check if we're in the right directory
if [ ! -f "package.json" ] && [ ! -d ".git" ]; then
    echo "❌ Error: Not in a valid project directory"
    exit 1
fi
echo "✅ Project directory confirmed"

# Test 2: Check if scripts exist and are executable
echo "🔍 Checking scripts..."
for script in CURSOR_END_OF_SESSION_GITHUB LOAD_SHARED_CONTEXT_GITHUB END_OF_SESSION_SHARED LOAD_SHARED_CONTEXT; do
    if [ -f "$script" ] && [ -x "$script" ]; then
        echo "✅ $script exists and is executable"
    else
        echo "❌ $script missing or not executable"
    fi
done

# Test 3: Check .ai-context directory
echo "📁 Checking .ai-context directory..."
if [ -d ".ai-context" ]; then
    echo "✅ .ai-context directory exists"
    ls -la .ai-context/ | head -5
else
    echo "❌ .ai-context directory missing"
fi

# Test 4: Check Python dependencies
echo "🐍 Checking Python dependencies..."
python3 -c "import psutil" 2>/dev/null && echo "✅ psutil available" || echo "❌ psutil missing"

# Test 5: Test LOAD_SHARED_CONTEXT_GITHUB
echo "🔄 Testing LOAD_SHARED_CONTEXT_GITHUB..."
if ./LOAD_SHARED_CONTEXT_GITHUB > /dev/null 2>&1; then
    echo "✅ LOAD_SHARED_CONTEXT_GITHUB works"
else
    echo "❌ LOAD_SHARED_CONTEXT_GITHUB failed"
fi

# Test 6: Check git status
echo "📊 Checking git status..."
git status --porcelain | wc -l | xargs -I {} echo "📝 {} uncommitted changes"

# Test 7: Check GitHub connectivity
echo "🌐 Checking GitHub connectivity..."
if git remote get-url origin > /dev/null 2>&1; then
    echo "✅ GitHub remote configured: $(git remote get-url origin)"
else
    echo "❌ No GitHub remote configured"
fi

echo ""
echo "🎯 TEST COMPLETE!"
echo "=================="
echo ""
echo "📋 System Status:"
echo "• GitHub integration: $(git remote get-url origin > /dev/null 2>&1 && echo '✅ Ready' || echo '❌ Not configured')"
echo "• Scripts: $(ls CURSOR_END_OF_SESSION_GITHUB LOAD_SHARED_CONTEXT_GITHUB END_OF_SESSION_SHARED LOAD_SHARED_CONTEXT 2>/dev/null | wc -l | xargs -I {} echo '{}/4 available')"
echo "• Context directory: $(test -d .ai-context && echo '✅ Present' || echo '❌ Missing')"
echo "• Python dependencies: $(python3 -c 'import psutil' 2>/dev/null && echo '✅ Ready' || echo '❌ Missing')"
echo ""
echo "🚀 Ready for zero-blindspot synchronization!"
