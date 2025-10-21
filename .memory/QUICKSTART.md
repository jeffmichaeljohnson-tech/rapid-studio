# Memory Sync Quick Start Guide

Get the memory synchronization system running in 2 minutes.

## Prerequisites

- Node.js installed (for `chokidar` dependency)
- Git repository initialized
- Terminal access

## Step 1: Make CLI Executable

```bash
chmod +x .memory/sync/cli.sh
```

## Step 2: Initialize System

```bash
npm run memory:init
```

This will:
- ✅ Create directory structure
- ✅ Install `chokidar` dependency
- ✅ Setup Git hooks
- ✅ Initialize state tracking

Expected output:
```
🔧 Initializing memory sync system...
📦 Installing dependencies...
✅ Memory sync system initialized

Next steps:
  1. Review config: .memory/config.json
  2. Start daemon: .memory/sync/cli.sh start
  3. Check status: .memory/sync/cli.sh status
```

## Step 3: Start the Daemon

```bash
npm run memory:start
```

Expected output:
```
🚀 Starting Memory Sync Daemon...
✅ Daemon started (PID: 12345)
   Logs: .memory/sync.log
```

## Step 4: Verify It's Running

```bash
npm run memory:status
```

Expected output:
```
✅ Daemon running (PID: 12345)

Recent activity:
🧠 Initializing Memory Sync Daemon...
✅ Configuration loaded
📝 Session auto-save enabled
👀 Context watcher enabled
⬇️  GitHub auto-pull enabled
🔄 Cross-tool sync enabled
🚀 Memory Sync Daemon started
```

## Step 5: Test It

### Create a manual snapshot
```bash
npm run memory:snapshot
```

### Check the logs
```bash
npm run memory:logs
```

### View sessions
```bash
ls -lh .memory/sessions/
```

You should see a `session-YYYY-MM-DD-HHmm.json` file!

## What Happens Now?

The daemon is now running in the background and will automatically:

1. **Every 10 minutes**: Save Claude conversation snapshot
2. **On file changes**: Update active context
3. **Every 5 minutes**: Pull from GitHub to catch Cursor updates
4. **Automatically**: Commit memory updates to GitHub

## Quick Commands

```bash
# See what's happening
npm run memory:logs:follow

# Force a sync right now
npm run memory:sync

# Stop the daemon
npm run memory:stop

# Restart daemon
npm run memory:restart
```

## Verify GitHub Integration

After a few minutes, check your GitHub repo:

```bash
git log --oneline -5
```

You should see commits like:
```
a1b2c3d [Memory] Auto-save session 1
e4f5g6h [Memory] Update context: SwipeDeck.tsx
```

## Troubleshooting

### Daemon won't start?
```bash
# Check if it's already running
npm run memory:status

# If stale, remove PID file
rm .memory/.daemon.pid
npm run memory:start
```

### No sessions being created?
```bash
# Check daemon logs for errors
npm run memory:logs

# Restart daemon
npm run memory:restart
```

### GitHub sync not working?
```bash
# Test git access
git status
git pull

# Force manual sync
npm run memory:sync
```

## Next Steps

1. **Review Configuration**: Edit `.memory/config.json` to tune intervals
2. **Read Full Docs**: See `.memory/README.md` for complete documentation
3. **Check ADR**: Read `.memory/decisions/ADR-002-memory-sync-system.md`

## Success Criteria

You'll know it's working when:
- ✅ `.memory/sessions/` contains JSON files
- ✅ `.memory/context/active-context.md` exists and updates
- ✅ GitHub shows `[Memory]` commits
- ✅ `npm run memory:status` shows "Daemon running"

---

**Time to setup**: ~2 minutes  
**Disk usage**: ~10MB per month (with auto-cleanup)  
**Performance impact**: Negligible (runs in background)

Questions? Check the full docs or ADR!
