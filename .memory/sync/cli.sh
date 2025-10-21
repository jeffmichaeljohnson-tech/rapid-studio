#!/bin/bash

# Memory Sync CLI Tool
# Provides manual control over the memory synchronization system

MEMORY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DAEMON_SCRIPT="$MEMORY_DIR/sync/daemon.js"
PID_FILE="$MEMORY_DIR/.daemon.pid"

case "$1" in
  start)
    if [ -f "$PID_FILE" ]; then
      echo "❌ Daemon already running (PID: $(cat $PID_FILE))"
      exit 1
    fi
    
    echo "🚀 Starting Memory Sync Daemon..."
    node "$DAEMON_SCRIPT" > "$MEMORY_DIR/sync.log" 2>&1 &
    echo $! > "$PID_FILE"
    echo "✅ Daemon started (PID: $(cat $PID_FILE))"
    echo "   Logs: $MEMORY_DIR/sync.log"
    ;;

  stop)
    if [ ! -f "$PID_FILE" ]; then
      echo "❌ Daemon not running"
      exit 1
    fi
    
    PID=$(cat "$PID_FILE")
    echo "🛑 Stopping daemon (PID: $PID)..."
    kill -TERM "$PID" 2>/dev/null || kill -KILL "$PID" 2>/dev/null
    rm -f "$PID_FILE"
    echo "✅ Daemon stopped"
    ;;

  restart)
    $0 stop
    sleep 2
    $0 start
    ;;

  status)
    if [ -f "$PID_FILE" ]; then
      PID=$(cat "$PID_FILE")
      if ps -p "$PID" > /dev/null 2>&1; then
        echo "✅ Daemon running (PID: $PID)"
        echo ""
        echo "Recent activity:"
        tail -n 10 "$MEMORY_DIR/sync.log"
      else
        echo "❌ Daemon not running (stale PID file)"
        rm -f "$PID_FILE"
      fi
    else
      echo "❌ Daemon not running"
    fi
    ;;

  snapshot)
    echo "📸 Creating manual snapshot..."
    node -e "
      const daemon = require('$DAEMON_SCRIPT');
      (async () => {
        const d = new daemon.MemorySyncDaemon();
        await d.init();
        await d.saveSession();
        process.exit(0);
      })();
    "
    echo "✅ Snapshot created"
    ;;

  restore)
    if [ -z "$2" ]; then
      echo "Usage: $0 restore <session-file>"
      echo ""
      echo "Available sessions:"
      ls -1 "$MEMORY_DIR/sessions/" | tail -n 10
      exit 1
    fi
    
    SESSION_FILE="$MEMORY_DIR/sessions/$2"
    if [ ! -f "$SESSION_FILE" ]; then
      echo "❌ Session file not found: $SESSION_FILE"
      exit 1
    fi
    
    echo "🔄 Restoring session: $2"
    cat "$SESSION_FILE" | jq '.snapshot' > "$MEMORY_DIR/context/restored-context.json"
    echo "✅ Session restored to context/restored-context.json"
    ;;

  sync-now)
    echo "🔄 Forcing immediate sync..."
    
    # Pull from GitHub
    git fetch origin
    git pull origin main --no-rebase
    
    # Commit local changes
    git add .memory/ .cursor/context/ docs/context/
    git commit -m "[Memory] Manual sync" || true
    git push origin main
    
    echo "✅ Sync complete"
    ;;

  init)
    echo "🔧 Initializing memory sync system..."
    
    # Create directory structure
    mkdir -p "$MEMORY_DIR/sessions"
    mkdir -p "$MEMORY_DIR/context"
    mkdir -p "$MEMORY_DIR/decisions"
    mkdir -p "$MEMORY_DIR/progress"
    mkdir -p "$MEMORY_DIR/sync"
    mkdir -p "$MEMORY_DIR/../.cursor/context"
    mkdir -p "$MEMORY_DIR/../.claude/context"
    mkdir -p "$MEMORY_DIR/../docs/context"
    
    # Initialize state file
    echo '{"lastSessionSave":null,"lastGitHubPull":null,"lastGitHubPush":null,"sessionCount":0,"syncCount":0,"checksums":{}}' \
      > "$MEMORY_DIR/.sync-state.json"
    
    # Create initial context
    echo "# Active Context - $(date -Iseconds)" > "$MEMORY_DIR/context/active-context.md"
    echo "" >> "$MEMORY_DIR/context/active-context.md"
    echo "Initialized by memory sync system" >> "$MEMORY_DIR/context/active-context.md"
    
    # Install Node dependencies
    if [ ! -d "$MEMORY_DIR/../node_modules/chokidar" ]; then
      echo "📦 Installing dependencies..."
      cd "$MEMORY_DIR/.."
      npm install chokidar
    fi
    
    # Setup git hooks
    cat > "$MEMORY_DIR/../.git/hooks/post-commit" << 'EOF'
#!/bin/bash
# Auto-update memory context after each commit
cd "$(git rev-parse --show-toplevel)"
.memory/sync/cli.sh snapshot 2>/dev/null || true
EOF
    chmod +x "$MEMORY_DIR/../.git/hooks/post-commit"
    
    cat > "$MEMORY_DIR/../.git/hooks/post-merge" << 'EOF'
#!/bin/bash
# Reload context after pulling changes
echo "🔄 Reloading context from remote changes..."
EOF
    chmod +x "$MEMORY_DIR/../.git/hooks/post-merge"
    
    echo "✅ Memory sync system initialized"
    echo ""
    echo "Next steps:"
    echo "  1. Review config: .memory/config.json"
    echo "  2. Start daemon: .memory/sync/cli.sh start"
    echo "  3. Check status: .memory/sync/cli.sh status"
    ;;

  logs)
    if [ ! -f "$MEMORY_DIR/sync.log" ]; then
      echo "❌ No logs found"
      exit 1
    fi
    
    if [ "$2" = "follow" ] || [ "$2" = "-f" ]; then
      tail -f "$MEMORY_DIR/sync.log"
    else
      tail -n 50 "$MEMORY_DIR/sync.log"
    fi
    ;;

  clean)
    echo "🧹 Cleaning old sessions..."
    find "$MEMORY_DIR/sessions" -name "session-*.json" -mtime +30 -delete
    echo "✅ Cleanup complete"
    ;;

  *)
    echo "Memory Sync CLI"
    echo ""
    echo "Usage: $0 <command>"
    echo ""
    echo "Commands:"
    echo "  init         Initialize the memory sync system"
    echo "  start        Start the sync daemon"
    echo "  stop         Stop the sync daemon"
    echo "  restart      Restart the sync daemon"
    echo "  status       Check daemon status"
    echo "  snapshot     Create a manual snapshot"
    echo "  restore      Restore a previous session"
    echo "  sync-now     Force immediate GitHub sync"
    echo "  logs         View sync logs (-f to follow)"
    echo "  clean        Remove old session files"
    echo ""
    exit 1
    ;;
esac
