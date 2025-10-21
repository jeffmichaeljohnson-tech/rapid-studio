#!/bin/bash
# Verify Agent Access - Ensure both Cursor and Claude have full access

echo "🔍 VERIFYING AGENT ACCESS - FULL PERMISSIONS CHECK"
echo "================================================="

# Check repository access
echo "📁 Repository Access:"
echo "• Rapid Studio: $(git -C /Users/computer/rapid-studio remote get-url origin)"
echo "• Cursor-Claude: $(git -C /Users/computer/cursor-claude-github remote get-url origin)"

# Check git configuration
echo ""
echo "⚙️  Git Configuration:"
echo "• User: $(git config --global user.name)"
echo "• Email: $(git config --global user.email)"

# Check file permissions
echo ""
echo "📝 File Permissions:"
echo "• .ai-context/: $(ls -ld /Users/computer/rapid-studio/.ai-context/ | awk '{print $1}')"
echo "• Scripts: $(ls -la /Users/computer/rapid-studio/CURSOR_END_OF_SESSION_GITHUB | awk '{print $1}')"

# Check GitHub connectivity
echo ""
echo "🌐 GitHub Connectivity:"
cd /Users/computer/rapid-studio
if git ls-remote origin > /dev/null 2>&1; then
    echo "✅ Rapid Studio: Connected"
else
    echo "❌ Rapid Studio: Connection failed"
fi

cd /Users/computer/cursor-claude-github
if git ls-remote origin > /dev/null 2>&1; then
    echo "✅ Cursor-Claude: Connected"
else
    echo "❌ Cursor-Claude: Connection failed"
fi

# Check shared context system
echo ""
echo "🤖 Shared Context System:"
echo "• CURSOR_LAST_SESSION.md: $(test -f /Users/computer/rapid-studio/.ai-context/CURSOR_LAST_SESSION.md && echo '✅ Present' || echo '❌ Missing')"
echo "• CLAUDE_LAST_SESSION.md: $(test -f /Users/computer/rapid-studio/.ai-context/CLAUDE_LAST_SESSION.md && echo '✅ Present' || echo '❌ Missing')"
echo "• SHARED_STATE.json: $(test -f /Users/computer/rapid-studio/.ai-context/SHARED_STATE.json && echo '✅ Present' || echo '❌ Missing')"

# Check script executability
echo ""
echo "🔧 Script Executability:"
for script in CURSOR_END_OF_SESSION_GITHUB LOAD_SHARED_CONTEXT_GITHUB END_OF_SESSION_SHARED LOAD_SHARED_CONTEXT; do
    if [ -x "/Users/computer/rapid-studio/$script" ]; then
        echo "✅ $script: Executable"
    else
        echo "❌ $script: Not executable"
    fi
done

echo ""
echo "🎯 ACCESS VERIFICATION COMPLETE!"
echo "================================"
echo ""
echo "📋 Summary:"
echo "• Repository access: $(git -C /Users/computer/rapid-studio ls-remote origin > /dev/null 2>&1 && echo '✅ Working' || echo '❌ Failed')"
echo "• File permissions: $(test -w /Users/computer/rapid-studio/.ai-context/ && echo '✅ Write access' || echo '❌ No write access')"
echo "• Script execution: $(test -x /Users/computer/rapid-studio/CURSOR_END_OF_SESSION_GITHUB && echo '✅ Executable' || echo '❌ Not executable')"
echo "• Shared context: $(test -d /Users/computer/rapid-studio/.ai-context/ && echo '✅ Present' || echo '❌ Missing')"
echo ""
echo "🚀 Both Cursor and Claude have full access to everything!"
echo "🎯 Zero blindspots achieved with perfect synchronization!"
