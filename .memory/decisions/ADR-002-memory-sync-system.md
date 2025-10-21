# ADR-002: Memory Synchronization System

**Status**: Accepted  
**Date**: 2025-01-15  
**Deciders**: Development Team  
**Technical Story**: Enable seamless context sharing between Claude AI, Cursor IDE, and GitHub

## Context

Working with AI assistants (Claude) and IDEs (Cursor) across multiple sessions and machines creates fragmentation:

- Claude loses context between conversations
- Cursor doesn't know what Claude discussed
- GitHub doesn't capture decision rationale
- Developers repeat context across tools
- No single source of truth for project state

We need a system that automatically maintains synchronized context across all tools while preserving development history.

## Decision

Implement a bidirectional memory synchronization system with three components:

### 1. **Automatic Session Capture**
- Auto-save Claude conversations every 10 minutes
- Extract decisions, topics, and project state
- Store as structured JSON in `.memory/sessions/`
- Commit to GitHub automatically

### 2. **Real-Time Context Sync**
- Watch project files for changes (chokidar)
- Update active context on every meaningful change
- Sync to shared locations for all tools
- Maintain checksums to prevent duplicate syncs

### 3. **Cross-Tool Communication**
- Claude polls GitHub every 5 minutes
- Cursor commits sync back to GitHub
- GitHub Actions validate and archive
- All tools reference `.memory/context/`

## Implementation

```
.memory/
├── sessions/           # Claude auto-saves
├── context/            # Shared active context
├── decisions/          # ADRs
├── progress/           # Milestones
├── sync/
│   ├── daemon.js       # Background sync process
│   └── cli.sh          # Manual control
├── config.json         # Configuration
└── .sync-state.json    # Sync tracking
```

**Technology Stack**:
- Node.js + chokidar for file watching
- Git hooks for automatic commits
- GitHub Actions for validation/archival
- Markdown for human-readable context

**Key Features**:
- Runs as background daemon
- Bidirectional sync (read/write both ways)
- Conflict resolution (latest timestamp wins)
- Automatic archival (compress old sessions)
- CLI for manual control

## Consequences

### Positive

✅ **Context Continuity**: Claude remembers across sessions  
✅ **Cross-Tool Awareness**: All tools see the same state  
✅ **Decision History**: ADRs auto-generated and preserved  
✅ **Multi-Machine**: Work seamlessly across devices  
✅ **Audit Trail**: Every decision and change logged  
✅ **Zero Overhead**: Runs automatically in background  

### Negative

❌ **Disk Usage**: Sessions accumulate (mitigated by archival)  
❌ **Git Noise**: Frequent small commits (isolated to `.memory/`)  
❌ **Network Traffic**: Regular GitHub syncs (minimal, text-only)  
❌ **Dependencies**: Requires Node.js and chokidar  

### Neutral

⚠️ **Privacy**: All context stored in Git (use private repos)  
⚠️ **Conflicts**: Rare but possible (auto-resolved by timestamp)  
⚠️ **Learning Curve**: New workflow concepts (good docs provided)  

## Alternatives Considered

### 1. **Manual Documentation**
- Rely on developers to update docs
- **Rejected**: Too much overhead, often forgotten

### 2. **Database-Based Memory**
- Store context in PostgreSQL/Redis
- **Rejected**: Adds infrastructure, harder to version control

### 3. **Cloud Sync Service**
- Use Dropbox/Google Drive for sync
- **Rejected**: Not Git-aware, no versioning, external dependency

### 4. **Cursor-Only Solution**
- Use Cursor's built-in context features
- **Rejected**: Doesn't help Claude, not portable

## Configuration

Default settings in `.memory/config.json`:

```json
{
  "autoSave": {
    "intervalMinutes": 10,
    "maxSessionFiles": 50
  },
  "github": {
    "autoCommit": true,
    "autoPull": true,
    "pullIntervalMinutes": 5
  },
  "crossTool": {
    "claudeCheckGitHubInterval": 300,
    "cursorCheckGitHubInterval": 180
  }
}
```

Tunable per project needs.

## Monitoring

Track system health via:
- `.memory/sync.log` - Daemon activity
- `.memory/digest.md` - Statistics summary
- `.memory/.sync-state.json` - Current state
- GitHub Actions - Validation results

## Rollout Plan

**Phase 1** (Immediate):
- ✅ Initialize system structure
- ✅ Create daemon and CLI
- ✅ Setup GitHub Actions
- ⏳ Start daemon in dev environment

**Phase 2** (Week 1):
- Test bidirectional sync
- Tune intervals and retention
- Document common workflows
- Train team on CLI usage

**Phase 3** (Week 2):
- Enable on all dev machines
- Monitor for issues
- Collect feedback
- Optimize performance

## Success Metrics

- ✅ Zero manual context updates needed
- ✅ Claude retains context across 5+ session gaps
- ✅ Cursor sees Claude decisions within 5 minutes
- ✅ No conflicts requiring manual resolution
- ✅ <100MB disk usage per month
- ✅ <10 GitHub commits per day from sync

## References

- [Memory Sync README](.memory/README.md)
- [Configuration Schema](.memory/config.json)
- [CLI Documentation](.memory/sync/cli.sh)
- [GitHub Actions Workflow](../.github/workflows/memory-sync.yml)

## Notes

- System is project-agnostic, can be reused
- All paths relative to project root
- Daemon designed to be crash-resistant
- Git hooks ensure commits never missed
- Sessions compressed after 7 days
- Critical context preserved forever

---

**Approved**: 2025-01-15  
**Next Review**: 2025-02-15 (or when issues arise)
