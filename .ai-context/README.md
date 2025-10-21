# 🤖 AI Context - Shared Memory System

This directory contains shared context between Cursor and Claude AI agents for the Rapid Studio project.

## 📁 Directory Structure

```
.ai-context/
├── README.md                    # This file
├── MASTER_STATUS.md            # Single source of truth - both agents update
├── CURSOR_LAST_SESSION.md      # What Cursor did last session
├── CLAUDE_LAST_SESSION.md      # What Claude discussed last session
├── SHARED_STATE.json           # Machine-readable state for both agents
└── sessions/                   # Historical session data
    ├── cursor_YYYYMMDD_HHMMSS.json
    └── claude_YYYYMMDD_HHMMSS.json
```

## 🔄 How It Works

### End of Session (Both Agents)
1. **Cursor** writes to `CURSOR_LAST_SESSION.md` + `sessions/cursor_TIMESTAMP.json`
2. **Claude** writes to `CLAUDE_LAST_SESSION.md` + `sessions/claude_TIMESTAMP.json`
3. Both agents update `MASTER_STATUS.md` with their sections
4. Both agents update `SHARED_STATE.json` with current state

### Start of Session (Both Agents)
1. **Auto-load** `MASTER_STATUS.md` first
2. **Read** the other agent's last session file
3. **Display** synchronization status
4. **Continue** with full context

## 🎯 Benefits

- ✅ **Perfect Synchronization** - Both agents see each other's work
- ✅ **Automatic Loading** - No manual context switching
- ✅ **Historical Tracking** - Complete session history
- ✅ **Machine Readable** - JSON state for programmatic access
- ✅ **Single Source of Truth** - MASTER_STATUS.md for current state

## 🚀 Usage

### For Cursor:
```bash
# End session
./CURSOR_END_OF_SESSION

# Start session - auto-loads Claude's context
./LOAD_SHARED_CONTEXT
```

### For Claude:
```bash
# End session  
./END_OF_SESSION_SHARED

# Start session - auto-loads Cursor's context
./LOAD_SHARED_CONTEXT
```

---

**🎯 This system ensures both Cursor and Claude have perfect context synchronization for Rapid Studio! 🎯**
