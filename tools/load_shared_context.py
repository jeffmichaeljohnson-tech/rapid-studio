#!/usr/bin/env python3
"""
LOAD SHARED CONTEXT - Auto-loading system for both Cursor and Claude
Automatically loads shared context at session start
"""

import os
import json
from datetime import datetime
from pathlib import Path
import sys

# Paths
RAPID_STUDIO = Path.home() / "rapid-studio"
SHARED_CONTEXT_DIR = RAPID_STUDIO / ".ai-context"

def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def load_shared_context():
    """Load and display shared context for both agents"""
    print_section("🔄 LOADING SHARED CONTEXT")
    
    if not SHARED_CONTEXT_DIR.exists():
        print("❌ No shared context directory found. This is the first session.")
        return None
    
    context_info = {
        "master_status_exists": False,
        "cursor_session_exists": False,
        "claude_session_exists": False,
        "shared_state_exists": False,
        "last_updated": None,
        "cursor_session_id": None,
        "claude_session_id": None
    }
    
    # Check for master status
    master_status_file = SHARED_CONTEXT_DIR / "MASTER_STATUS.md"
    if master_status_file.exists():
        context_info["master_status_exists"] = True
        print("✅ MASTER_STATUS.md found")
    else:
        print("❌ MASTER_STATUS.md not found")
    
    # Check for Cursor session
    cursor_session_file = SHARED_CONTEXT_DIR / "CURSOR_LAST_SESSION.md"
    if cursor_session_file.exists():
        context_info["cursor_session_exists"] = True
        print("✅ CURSOR_LAST_SESSION.md found")
    else:
        print("❌ CURSOR_LAST_SESSION.md not found")
    
    # Check for Claude session
    claude_session_file = SHARED_CONTEXT_DIR / "CLAUDE_LAST_SESSION.md"
    if claude_session_file.exists():
        context_info["claude_session_exists"] = True
        print("✅ CLAUDE_LAST_SESSION.md found")
    else:
        print("❌ CLAUDE_LAST_SESSION.md not found")
    
    # Check for shared state
    shared_state_file = SHARED_CONTEXT_DIR / "SHARED_STATE.json"
    if shared_state_file.exists():
        context_info["shared_state_exists"] = True
        try:
            with open(shared_state_file, 'r') as f:
                shared_state = json.load(f)
                context_info["last_updated"] = shared_state.get("last_updated")
                context_info["cursor_session_id"] = shared_state.get("cursor_session")
                context_info["claude_session_id"] = shared_state.get("claude_session")
            print("✅ SHARED_STATE.json found")
        except Exception as e:
            print(f"❌ Error reading SHARED_STATE.json: {e}")
    else:
        print("❌ SHARED_STATE.json not found")
    
    return context_info

def display_synchronization_status(context_info):
    """Display synchronization status"""
    print_section("📊 SYNCHRONIZATION STATUS")
    
    if not context_info:
        print("🆕 This appears to be the first session with shared context.")
        return
    
    print(f"**Last Updated:** {context_info.get('last_updated', 'Unknown')}")
    print(f"**Cursor Session:** {context_info.get('cursor_session_id', 'None')}")
    print(f"**Claude Session:** {context_info.get('claude_session_id', 'None')}")
    
    if context_info.get('cursor_session_exists') and context_info.get('claude_session_exists'):
        print("\n🎯 **PERFECT SYNCHRONIZATION** - Both agents have recent session data!")
    elif context_info.get('cursor_session_exists'):
        print("\n💻 **CURSOR DATA AVAILABLE** - Claude can see what Cursor implemented")
    elif context_info.get('claude_session_exists'):
        print("\n🧠 **CLAUDE DATA AVAILABLE** - Cursor can see what Claude discussed")
    else:
        print("\n🆕 **FRESH START** - No previous session data found")

def display_quick_summary():
    """Display quick summary of what each agent did"""
    print_section("📋 QUICK SESSION SUMMARY")
    
    # Try to read Cursor's last session
    cursor_file = SHARED_CONTEXT_DIR / "CURSOR_LAST_SESSION.md"
    if cursor_file.exists():
        print("💻 **CURSOR'S LAST SESSION:**")
        try:
            with open(cursor_file, 'r') as f:
                content = f.read()
                # Extract key info
                lines = content.split('\n')
                for line in lines[:20]:  # First 20 lines
                    if line.strip() and not line.startswith('#'):
                        print(f"   {line}")
        except Exception as e:
            print(f"   Error reading Cursor session: {e}")
    
    # Try to read Claude's last session
    claude_file = SHARED_CONTEXT_DIR / "CLAUDE_LAST_SESSION.md"
    if claude_file.exists():
        print("\n🧠 **CLAUDE'S LAST SESSION:**")
        try:
            with open(claude_file, 'r') as f:
                content = f.read()
                # Extract key info
                lines = content.split('\n')
                for line in lines[:20]:  # First 20 lines
                    if line.strip() and not line.startswith('#'):
                        print(f"   {line}")
        except Exception as e:
            print(f"   Error reading Claude session: {e}")

def create_session_start_marker():
    """Create a marker for this session start"""
    timestamp = datetime.now()
    session_start_id = f"session_start_{timestamp.strftime('%Y%m%d_%H%M%S')}"
    
    marker_file = SHARED_CONTEXT_DIR / f"{session_start_id}.marker"
    with open(marker_file, 'w') as f:
        f.write(f"Session started: {timestamp.isoformat()}\n")
        f.write(f"Session ID: {session_start_id}\n")
        f.write(f"Agent: {'cursor' if 'cursor' in sys.argv[0].lower() else 'claude'}\n")
    
    print(f"✅ Session start marker created: {session_start_id}")

def main():
    """Main execution"""
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║              LOAD SHARED CONTEXT - AUTO-LOADING             ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    try:
        # Load shared context
        context_info = load_shared_context()
        
        # Display synchronization status
        display_synchronization_status(context_info)
        
        # Display quick summary
        display_quick_summary()
        
        # Create session start marker
        create_session_start_marker()
        
        print_section("✅ SHARED CONTEXT LOADED")
        print("""
🎯 Shared context loaded successfully!

📁 Available files:
   • MASTER_STATUS.md (unified project status)
   • CURSOR_LAST_SESSION.md (what Cursor did)
   • CLAUDE_LAST_SESSION.md (what Claude discussed)
   • SHARED_STATE.json (machine-readable state)

🔄 Both agents now have synchronized context!

💡 Next steps:
   • Read the relevant session files for full context
   • Continue with synchronized knowledge
   • Update shared context at session end
        """)
        
    except Exception as e:
        print(f"\n❌ Error loading shared context: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
