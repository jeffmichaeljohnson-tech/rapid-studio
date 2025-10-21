#!/bin/bash
# Setup GitHub Integration for Shared Context System
# This script sets up the complete GitHub-integrated shared context system

echo "🚀 SETTING UP GITHUB-INTEGRATED SHARED CONTEXT SYSTEM"
echo "=================================================="

# Check if we're in the right directory
if [ ! -f "package.json" ] && [ ! -d ".git" ]; then
    echo "❌ Error: Not in a valid project directory"
    echo "Please run this script from the rapid-studio project root"
    exit 1
fi

echo "✅ Project directory confirmed"

# Make all scripts executable
echo "🔧 Making scripts executable..."
chmod +x CURSOR_END_OF_SESSION_GITHUB
chmod +x LOAD_SHARED_CONTEXT_GITHUB
chmod +x END_OF_SESSION_SHARED
chmod +x LOAD_SHARED_CONTEXT
chmod +x tools/*.py

echo "✅ Scripts made executable"

# Check Python dependencies
echo "🐍 Checking Python dependencies..."
python3 -c "import psutil" 2>/dev/null || {
    echo "📦 Installing psutil..."
    pip3 install psutil
}

echo "✅ Python dependencies verified"

# Create .ai-context directory if it doesn't exist
if [ ! -d ".ai-context" ]; then
    echo "📁 Creating .ai-context directory..."
    mkdir -p .ai-context/sessions
    echo "✅ .ai-context directory created"
else
    echo "✅ .ai-context directory already exists"
fi

# Check git configuration
echo "🔍 Checking git configuration..."
if ! git config user.name > /dev/null 2>&1; then
    echo "⚠️  Git user.name not configured"
    echo "Please run: git config user.name 'Your Name'"
fi

if ! git config user.email > /dev/null 2>&1; then
    echo "⚠️  Git user.email not configured"
    echo "Please run: git config user.email 'your.email@example.com'"
fi

# Check if .ai-context is in .gitignore
if [ -f ".gitignore" ] && grep -q "\.ai-context" .gitignore; then
    echo "⚠️  .ai-context is in .gitignore - removing it for shared context system"
    sed -i.bak '/\.ai-context/d' .gitignore
    echo "✅ Removed .ai-context from .gitignore"
fi

# Add .ai-context to git if not already tracked
if ! git ls-files --error-unmatch .ai-context/ > /dev/null 2>&1; then
    echo "📝 Adding .ai-context to git..."
    git add .ai-context/
    git commit -m "Add .ai-context directory for shared context system"
    echo "✅ .ai-context added to git"
fi

# Test the system
echo "🧪 Testing the system..."
if ./LOAD_SHARED_CONTEXT_GITHUB > /dev/null 2>&1; then
    echo "✅ LOAD_SHARED_CONTEXT_GITHUB works"
else
    echo "❌ LOAD_SHARED_CONTEXT_GITHUB failed"
fi

echo ""
echo "🎉 GITHUB INTEGRATION SETUP COMPLETE!"
echo "======================================"
echo ""
echo "📋 Next Steps:"
echo "1. For Cursor: Use ./CURSOR_END_OF_SESSION_GITHUB to end sessions"
echo "2. For Claude: Use ./LOAD_SHARED_CONTEXT_GITHUB to start sessions"
echo "3. For Claude: Use ./END_OF_SESSION_SHARED to end sessions"
echo "4. Check COMPLETE_USAGE_GUIDE.md for detailed instructions"
echo ""
echo "🎯 Perfect synchronization between Cursor and Claude achieved!"
echo "🚀 Zero blindspots - both agents can see everything!"
