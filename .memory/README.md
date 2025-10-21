# Memory Synchronization System

Automatic bidirectional memory sync between Claude AI, Cursor IDE, and GitHub.

## 🎯 Purpose

This system ensures that Claude, Cursor, and your GitHub repository maintain perfect synchronization of:
- **Session Memory**: Auto-saved snapshots of Claude conversations
- **Active Context**: Real-time project state and decisions
- **Development Progress**: Milestone tracking and ADRs
- **Cross-Tool Updates**: Changes from Cursor sync back to Claude

## 🏗️ Architecture

```
┌─────────────┐     ┌──────────────┐     ┌────────────┐
│   Claude    │────▶│   .memory/   │◀────│   Cursor   │
│     AI      │     │   (GitHub)   │     │    IDE     │
└─────────────┘     └──────────────┘     └────────────┘
       │                    │                    │
       └────────────────────┴────────────────────┘
              Bidirectional Sync Every 5-10min
```

### Directory Structure

```
.memory/
├── sessions/           # Auto-saved Claude sessions
│   ├── session-2025-01-15-1430.json
│   ├── session-2025-01-15-1450.json
│   └── archive/        # Compressed old sessions
├── context/            # Active context snapshots
│   ├── active-context.md
│   └── latest-update.json
├── decisions/          # Architecture Decision Records
│   ├── ADR-001-docker-strategy.md
│   └── ADR-002-memory-sync.md
├── progress/           # Development milestones
│   └── sprint-current.md
├── sync/               # Synchronization scripts
│   ├── daemon.js       # Main sync daemon
│   └── cli.sh          # CLI interface
├── config.json         # Configuration
└── .sync-state.json    # Sync state tracking
```

## 🚀 Quick Start

### 1. Initialize the System

```bash
chmod +x .memory/sync/cli.sh
.memory/sync/cli.sh init
```

This will:
- Create all required directories
- Install Node dependencies (chokidar)
- Set up Git hooks for auto-sync
- Initialize state tracking

### 2. Start the Daemon

```bash
.memory/sync/cli.sh start
```

The daemon will:
- Auto-save Claude sessions every 10 minutes
- Watch for file changes and sync context
- Pull from GitHub every 5 minutes
- Push updates to GitHub automatically

### 3. Check Status

```bash
.memory/sync/cli.sh status
```

## 📋 How It Works

### Automatic Processes

#### 1. **Session Auto-Save** (Every 10 minutes)
```
Claude conversation → Capture state → Save to sessions/ → Commit to GitHub
```

Each session includes:
- Conversation snapshot
- Project state (Docker, Git, files)
- Recent decisions and topics
- Active files being worked on

#### 2. **Context Watching** (Real-time)
```
File changes → Update checksums → Sync to targets → Commit to GitHub
```

Watches these paths:
- `app/**/*.{ts,tsx}` - Mobile app code
- `components/**/*.{ts,tsx}` - React components
- `orchestrator/**/*.py` - Backend services
- `.cursor/rules/*.mdc` - Cursor context rules
- `docs/**/*.md` - Documentation

#### 3. **GitHub Sync** (Every 5 minutes)
```
GitHub ← Pull changes ← Check for updates ← Push local changes
```

Detects when:
- Cursor makes commits from another machine
- GitHub Actions updates memory files
- Manual commits affect memory paths

#### 4. **Cross-Tool Updates** (Every 5 minutes)
```
Claude → Read Cursor changes → Update context → Write for Cursor
```

Enables:
- Claude to see what Cursor is working on
- Cursor to see Claude's latest decisions
- Both tools to reference shared context

## 🎮 CLI Commands

```bash
# Daemon Management
.memory/sync/cli.sh start          # Start background daemon
.memory/sync/cli.sh stop           # Stop daemon
.memory/sync/cli.sh restart        # Restart daemon
.memory/sync/cli.sh status         # Check daemon status

# Manual Operations
.memory/sync/cli.sh snapshot       # Create immediate snapshot
.memory/sync/cli.sh sync-now       # Force GitHub sync
.memory/sync/cli.sh restore <file> # Restore previous session

# Maintenance
.memory/sync/cli.sh logs           # View sync logs
.memory/sync/cli.sh logs -f        # Follow logs in real-time
.memory/sync/cli.sh clean          # Remove old sessions
```

## ⚙️ Configuration

Edit `.memory/config.json` to customize:

```json
{
  "autoSave": {
    "intervalMinutes": 10,          // How often to save sessions
    "maxSessionFiles": 50           // Max sessions before cleanup
  },
  "github": {
    "autoPull": true,               // Auto-pull from GitHub
    "pullIntervalMinutes": 5,       // How often to check
    "autoCommit": true              // Auto-commit changes
  },
  "crossTool": {
    "claudeCheckGitHubInterval": 300,  // Claude checks (seconds)
    "cursorCheckGitHubInterval": 180   // Cursor checks (seconds)
  }
}
```

## 📊 GitHub Actions Integration

The system includes a GitHub Actions workflow that:
- Validates memory structure on every push
- Generates memory digests
- Archives old sessions (7+ days old)
- Runs cleanup every 15 minutes
- Syncs with Cursor context automatically

See: `.github/workflows/memory-sync.yml`

## 🔄 Workflow Examples

### Scenario 1: Claude Makes Progress
```
1. You chat with Claude for 20 minutes
2. Daemon auto-saves session at minute 10 and 20
3. Sessions committed to GitHub
4. Cursor can now see Claude's decisions
5. GitHub Actions validates and archives
```

### Scenario 2: Cursor Makes Changes
```
1. You edit files in Cursor
2. Cursor commits changes
3. GitHub Actions updates memory
4. Daemon pulls changes (next 5-min interval)
5. Claude sees Cursor's updates
```

### Scenario 3: Working Across Machines
```
1. Work on laptop, Claude saves sessions
2. Sessions pushed to GitHub
3. Switch to desktop
4. Daemon pulls latest sessions
5. Context restored automatically
```

## 🛡️ Safety Features

- **Conflict Resolution**: Latest timestamp wins
- **Checksums**: Prevents duplicate syncs
- **Atomic Commits**: All-or-nothing updates
- **Archive System**: Old sessions compressed and preserved
- **Rate Limiting**: Prevents excessive API calls
- **Error Recovery**: Continues on partial failures

## 📝 Memory Retention

| Type | Retention | Archival | Notes |
|------|-----------|----------|-------|
| Sessions | 30 days | After 7 days | Compressed to .gz |
| Context | 10 versions | Critical kept forever | Latest always active |
| Decisions | Forever | N/A | ADRs never deleted |
| Progress | 90 days | After 30 days | Milestones archived |

## 🔍 Monitoring

### Check Recent Activity
```bash
# View last 10 log entries
.memory/sync/cli.sh logs

# Follow live activity
.memory/sync/cli.sh logs -f
```

### View Memory Digest
```bash
cat .memory/digest.md
```

Shows:
- Total sessions count
- Recent activity (24h)
- Git status
- File statistics

## 🚨 Troubleshooting

### Daemon Won't Start
```bash
# Check if already running
.memory/sync/cli.sh status

# Kill stale process
rm .memory/.daemon.pid
.memory/sync/cli.sh start
```

### Missing Dependencies
```bash
cd /path/to/rapid-studio
npm install chokidar
```

### GitHub Sync Failing
```bash
# Check git status
git status

# Force manual sync
.memory/sync/cli.sh sync-now
```

### Sessions Not Saving
```bash
# Check daemon logs
.memory/sync/cli.sh logs

# Restart daemon
.memory/sync/cli.sh restart
```

## 🎯 Best Practices

1. **Let it run**: Keep daemon running during development
2. **Check status**: Verify daemon health periodically
3. **Review sessions**: Manually review important sessions
4. **Clean regularly**: Run cleanup to manage disk space
5. **Monitor logs**: Watch for sync errors or conflicts

## 🔗 Integration Points

### Claude
- Reads: `.memory/context/active-context.md`
- Writes: `.memory/sessions/*.json`
- Updates: `.memory/decisions/*.md`

### Cursor
- Reads: `.cursor/context/from-memory.md`
- Writes: `.cursor/context/*.md`
- Updates: `.cursor/rules/*.mdc`

### GitHub
- Stores: All `.memory/` content
- Actions: Validates and archives
- Webhooks: (Future) Real-time notifications

## 📚 Related Documentation

- [Project Overview](../docs/PROJECT_OVERVIEW.md)
- [Architecture Decisions](./decisions/)
- [Development Workflow](../docs/DEVELOPMENT.md)

## 🤝 Contributing

When adding new memory features:
1. Update `config.json` schema
2. Document in this README
3. Add tests for sync logic
4. Create ADR for significant changes

---

**Status**: ✅ Active and Running
**Last Updated**: Auto-generated by Memory Sync Daemon
**Version**: 1.0.0
